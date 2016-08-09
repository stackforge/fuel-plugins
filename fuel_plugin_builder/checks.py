# -*- coding: utf-8 -*-
#
#    Copyright 2016 Mirantis, Inc.
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

import jsonschema
import six
from yaml import YAMLError

from fuel_plugin_builder import utils
from fuel_plugin_builder.files_manager import files_manager
from fuel_plugin_builder.reports import ReportNode

# This file provides number of functions which making some plugin-specific data
# requirements/integrity and file system checks and returning report.
#
# Three basic rules of using and adding new checks:
# 1. Check could call another check and use it's report.
# 2. Check always returning a Report node.
# 3. Check should be named with check_* prefix to be easy to find.


def check_yaml_loadable(path):
    """Load YAML file and try to parse it.

    :param path: path of YAML file
    :type path: str

    :return: data or nothing
    :rtype: list|dict|None
    """
    report = ReportNode()
    try:
        return files_manager.load(path)
    except IOError as (errno, strerror):
        report.error(u"I/O error({0}): {1}".format(errno, strerror))
    except YAMLError as exc:
        error_message = u"Can't parse YAML file"
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            error_message += u", error position: (%s:%s)" % (
                mark.line + 1, mark.column + 1)
            report.error(error_message)
    return report


def check_with_json_schema(schema, data):
    """Check data with JSON Schema.

    :param schema: JSON Schema
    :type schema: list|dict
    :param data: data to check
    :type data: list|dict

    :return: report node
    :rtype: reports.ReportNode
    """
    root_report_node = ReportNode()
    validator = jsonschema.Draft4Validator(schema)

    def _convert_errors_tree_report_tree(json_schema_errors, report_node):
        """Make detailed report tree of JSON errors.

        :param json_schema_errors: validation errors
        :type json_schema_errors: iterable[ValidationError]
        :param report_node: report node
        :type report_node: ReportNode

        :return: report node
        :rtype: reports.ReportNode
        """
        for exc in sorted(json_schema_errors, key=lambda e: e.path):
            path = u' -> '.join(
                map(six.text_type, exc.path)) or None
            sub_report_node = ReportNode(path)
            if exc.message:
                sub_report_node.error(exc.message)
            report_node.add_nodes(sub_report_node)
            if exc.context:  # make nested report nodes
                _convert_errors_tree_report_tree(exc.context, sub_report_node)
        return report_node

    return _convert_errors_tree_report_tree(
        validator.iter_errors(data),
        root_report_node
    )


def check_multi_json_schema_is_valid(schemas, data):
    """Checks multiple JSON Schema using record ``type`` field to choose
    appropriate schema.

    :param schemas: dict of schemas in format
                        {
                            'type1': schema1,
                            'type2': schema2
                        }
    :type schemas: dict
    :param data: data tree
    :type data: list[list|dict]

    :return: report
    :rtype: reports.ReportNode
    """
    report = ReportNode()
    if not isinstance(data, list):
        report.error(u'Data should be a list of entities')
        return report
    for record_id, record in enumerate(data):
        record_type = record.get('type', '')
        schema = schemas.get(record_type)
        if schema is not None:
            report.add_nodes(
                check_with_json_schema(schema, record)
            )
        else:
            report.error(u'Invalid type: {0} for record: {1}'.format(
                record_type, record_id
            ))
    return report


def check_path_exists(path):
    """Check if path is exists or path mask has been resolved to at least
    one path.

    :param path: path
    :type path: basestring|str

    :return: report
    :rtype: reports.ReportNode
    """
    report = ReportNode(u'Checking path existence: {}'.format(path))

    if not utils.fs.get_paths(path):
        report.error(u'Path not exists')

    return report


def check_dir_exists(path):
    """Check if dir is exists.

    :param path: path
    :type path: str

    :return: report
    :rtype: reports.ReportNode
    """
    report = ReportNode(text=path)

    if not utils.fs.is_dir(path):
        report.error(u'Directory not exists')
    return report


def check_file_exists(path):
    """Check if file is exists.

    :param path: path
    :type path: str

    :return: report
    :rtype: reports.ReportNode
    """
    result = ReportNode(text=path)

    if not utils.fs.is_exists(path):
        result.error(u'File not found')
    return result


def check_fuel_ver_compatible_with_package_ver(basic_version, plugin_metadata):
    """Checks Fuel version compatibility with plugin package version.

    :param basic_version: basic supported version
    :type basic_version: str
    :param plugin_metadata: plugin metadata root
    :type plugin_metadata: dict

    :return: report
    :rtype: reports.ReportNode
    """
    report = ReportNode(u'Checking version compatibility')
    report.info(u'Expected Fuel version >= {0}'.format(basic_version))
    incompatible_versions = list()
    compatible_versions = list()

    for fuel_version in plugin_metadata.get('fuel_version', []):
        if (
            utils.strict_version(fuel_version) <
            utils.strict_version(basic_version)
        ):
            incompatible_versions.append(fuel_version)
        else:
            compatible_versions.append(fuel_version)

    if not compatible_versions:
        report.error(
            u'Current plugin format {0} is not compatible with following Fuel '
            u'versions: {2}\n'
            u'Fuel version must be {1} or higher. '
            u'Please remove {2} version from metadata.yaml file or '
            u'downgrade package_version.'
            .format(
                plugin_metadata['package_version'],
                basic_version,
                ', '.join(incompatible_versions)
            )
        )

    if compatible_versions:
        if incompatible_versions:
            report.warning(
                u'Current plugin format {0} is not compatible with following '
                u'Fuel versions: {2}\n'
                u'Fuel version must be {1} or higher. '
                u'Please remove {2} version from metadata.yaml file or '
                u'downgrade package_version.'.format(
                    plugin_metadata['package_version'],
                    basic_version,
                    ', '.join(incompatible_versions)
                )
            )

        report.info(u'Plugin is compatible with target Fuel version.')

    return report



def check_env_attributes(self, data, attributes_schema):
    """Check attributes in environment config file.
    'attributes' is not required field, but if it's
    present it should contain UI elements OR metadata
    structure.
    """
    report = ReportNode()
    report.add_nodes(
        check_with_json_schema(data, self.schema.attr_root_schema)
    )

    attrs = data.get('attributes', {})
    for attr_id, attr in six.iteritems(attrs):
        # Metadata object is totally different
        # from the others, we have to set different
        # validator for it
        if attr_id == 'metadata':
            schema = attributes_schema.attr_meta_schema
        else:
            schema = attributes_schema.attr_element_schema
        report.add_nodes(
            check_with_json_schema(attr, schema)
        )

    return report

data = []

# CONFIGS_SCHEMAS = {
#     "volumes_path": check_json_schema_is_valid(schemas.volumes_v3_0_0, data),
#     "roles_path": check_json_schema_is_valid(schemas.roles_v3_0_0, data),
#     "network_roles_path": check_json_schema_is_valid(schemas.network_roles_v3_0_0, data),
#
#     "attributes_path": check_env_attributes(data),
#     "vmware_attributes_path": "", # no check
#     "node_attributes_path": "",
#     "nic_attributes_path": "",
#     "bond_attributes_path": "",
#     "components_path": schemas.components_v4_0_0,
#
#     "networks_path": "", # only for root release
#     "graphs": schemas.graphs_metadata_v5_0_0
# }
#
#
def check_release_record_v5_0_0(release_record):
    report = ReportNode()

    # for dir_key in CONFIGS_SCHEMAS:
    #     path = release_record.get(dir_key, None)
    #     if path:
    #         report.add_nodes(check_dir_exists(path))

    # deprecated mode
    mode = release_record.get('mode')
    if mode is not None:
        report.warning(u'"mode" directive going to be deprecated')


    # check_json_schema_is_valid(schemas.)
    return report