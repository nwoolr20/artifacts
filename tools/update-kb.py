#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Tool to update the Digital Forensics Artifact Knowledge Base."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import glob
import io
import logging
import os
import sys

from artifacts import errors
from artifacts import reader


class ArtifactKnowledgeBaseUpdater(object):
  """Artifact Knowledge Base updater."""

  LEGACY_PATH = os.path.join('data', 'legacy.yaml')

  _ARTIFACTS_KB_URL_PREFIX = (
      'https://github.com/ForensicArtifacts/artifacts-kb/')

  def __init__(self, kb_path=None):
    """Creates an Artifact Knowledge Base updater.

    Args:
      kb_path (Optional[str]): path of the directory that contains the
          artifacts-kb articles.
    """
    super(ArtifactKnowledgeBaseUpdater, self).__init__()
    self._kb_path = kb_path

  def _CreateKBArticle(self, artifact_definition):
    """Creates a knowledge base article.

    Args:
      artifact_definition (ArtifactDefinition): artifact definition.

    Returns:
      bool: True if the knowledge base article was created successfully.
    """
    if not self._kb_path:
      logging.info('Missing knowledge base article for: {0:s}'.format(
          artifact_definition.name))
      return False

    if artifact_definition.name.startswith('Windows'):
      kb_article_path = '{0:s}.md'.format(artifact_definition.name[7:])
      kb_article_path = os.path.join('windows', kb_article_path)

    else:
      logging.info((
          'Unable to create knowledge base article for artifact definition: '
          '{0:s}').format(artifact_definition.name))
      return False

    kb_article_path = os.path.join(self._kb_path, kb_article_path)

    if os.path.exists(kb_article_path):
      logging.info((
          'artifact definition: {0:s} has knowledge base article but is not '
          'specified as URL').format(artifact_definition.name))
      return False

    template_mappings = {
        'title': artifact_definition.name[7:]}

    article_template = [
        '## {title:s}',
        '']

    if artifact_definition.description:
      description = artifact_definition.description
      description = description.replace('{', '{{')
      description = description.replace('}', '}}')

      article_template.append(description)
    else:
      article_template.append('TODO: add short summary')

    article_template.extend([
        '',
        '### References',
        ''])

    for url in artifact_definition.urls:
      url = url.replace('{', '{{')
      url = url.replace('}', '}}')

      article_template.append('* [TODO: add description]({0:s})'.format(url))

    article_template.append('')

    article_content = '\n'.join(article_template)
    article_content = article_content.format(**template_mappings)

    with io.open(kb_article_path, 'w', encoding='utf-8') as file_object:
      file_object.write(article_content)

    return True

  def ProcessFile(self, filename):
    """Processes the artifacts definition in a specific file.

    Args:
      filename (str): name of the artifacts definition file.

    Returns:
      bool: True if the artifacts definitions in the file were processed
          successfully.
    """
    result = True
    artifact_reader = reader.YamlArtifactsReader()

    try:
      for artifact_definition in artifact_reader.ReadFile(filename):
        if not artifact_definition.urls:
          logging.info('artifact definition: {0:s} is missing URLs'.format(
              artifact_definition.name))

        has_kb_page = False
        for url in artifact_definition.urls:
          if url.startswith(self._ARTIFACTS_KB_URL_PREFIX):
            has_kb_page = True
          else:
            logging.info((
                'artifact definition: {0:s} URL outside knowledge base: '
                '{1:s}').format(artifact_definition.name, url))

        if not has_kb_page:
          if not self._CreateKBArticle(artifact_definition):
            result = False

        # TODO: if has_kb_page check if reference URLs still are valid

    except errors.FormatError as exception:
      logging.warning(
          'Unable to process file: {0:s} with error: {1!s}'.format(
              filename, exception))
      result = False

    return result


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(
      description='Updates the Digital Forensics Artifact Knowledge Base.')

  argument_parser.add_argument(
      '--kb', dest='kb_path', type=str, metavar='PATH', action='store',
      help='path of the directory that contains the artifacts-kb articles.')

  argument_parser.add_argument(
      'definitions', nargs='?', action='store', metavar='PATH', default=None,
      help=('path of the file or directory that contains the artifact '
            'definitions.'))

  options = argument_parser.parse_args()

  if not options.definitions:
    print('Source value is missing.')
    print('')
    argument_parser.print_help()
    print('')
    return False

  if not os.path.exists(options.definitions):
    print('No such file or directory: {0:s}'.format(options.definitions))
    print('')
    return False

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  updater = ArtifactKnowledgeBaseUpdater(kb_path=options.kb_path)

  if os.path.isdir(options.definitions):
    result = True
    for filename in glob.glob(os.path.join(options.definitions, '*.yaml')):
      print('Processing definitions in: {0:s}'.format(filename))
      if not updater.ProcessFile(filename):
        result = False

  else:
    print('Processing definitions in: {0:s}'.format(options.definitions))
    result = updater.ProcessFile(options.definitions)

  if not result:
    print('FAILURE')
    return False

  print('SUCCESS')
  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
