# -*- coding: utf-8 -*-

#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from fuel_plugin_builder import builders
from fuel_plugin_builder import errors
from fuel_plugin_builder import loaders
from fuel_plugin_builder import validators

logger = logging.getLogger(__name__)

mapping = {
    '5.0.0': {
        'version': '5.0.0',
        'templates': [
            'templates/base',
            'templates/v5/plugin_data/'
        ],

        'loader': loaders.PluginLoaderV5,
        'validator': validators.ValidatorV5,
        'builder': builders.BuilderV3  # build process have not
        # changed
    },
    '4.0.0': {
        'version': '4.0.0',
        'templates': [
            'templates/base',
            'templates/v3/plugin_data/',
            'templates/v4/plugin_data/'
        ],
        'loader': loaders.PluginLoaderV4,
        'validator': validators.ValidatorV4,
        'builder': builders.BuilderV3  # build process have not
        # changed
    },
    '3.0.0': {
        'version': '3.0.0',
        'templates': [
            'templates/base',
            'templates/v3/plugin_data/'
        ],

        'loader': loaders.PluginLoaderV3,
        'validator': validators.ValidatorV3,
        'builder': builders.BuilderV3
    },
    '2.0.0': {
        'version': '2.0.0',
        'templates': [
            'templates/base',
            'templates/v2/plugin_data/'
        ],
        'loader': loaders.PluginLoaderV1,
        'validator': validators.ValidatorV2,
        'builder': builders.BuilderV2
    },
    '1.0.0': {
        'version': '1.0.0',
        'templates': [
            'templates/base',
            'templates/v1/'
        ],
        'loader': loaders.PluginLoaderV1,
        'validator': validators.validator_v1.ValidatorV1,
        'builder': builders.BuilderV1
    }
}


def get_plugin_for_version(version):
    """Retrieves data which are required for specific version of plugin

        :param str version: version of package
        :returns: dict which contains
                  'version' - package version
                  'templates' - array of paths to templates
                  'validator' - validator class
                  'builder' - builder class
        """

    data = mapping.get(version, None)

    if not data:
        raise errors.WrongPackageVersionError(
            'Wrong package version "{0}"'.format(version))
    return data


def get_version_mapping_from_plugin(plugin_metadata_path):
    """Returns mapping for specific version of the plugin.

    :param str plugin_metadata_path: path to the directory with metadata.yaml
    :returns: dict which contains
              'version' - package version
              'validator' - validator class
              'templates' - path to templates
              'builder' - builder class
    """
    from fuel_plugin_builder import loaders
    data = loaders.PluginLoaderV5().load(plugin_metadata_path)

    if data.report.is_failed():
        data.report.error('Wrong path to the plugin, '
                          'cannot find "metadata.yaml" file')

        logger.error(data.report.render())
        return
    package_version = data.get('package_version')
    return get_plugin_for_version(package_version)


def get_validator(plugin_path):
    validator = get_version_mapping_from_plugin(plugin_path)['validator']
    return validator(plugin_path)
