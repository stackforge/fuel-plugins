# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
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

from fuel_plugin_builder import consts
from fuel_plugin_builder.validators.schemas import SchemaV3


class SchemaV4(SchemaV3):

    @property
    def package_version(self):
        return {'enum': ['4.0.0']}

    @property
    def metadata_schema(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'title': 'plugin',
            'type': 'object',
            'required': [
                'name',
                'title',
                'version',
                'package_version',
                'description',
                'fuel_version',
                'licenses',
                'authors',
                'homepage',
                'releases',
                'groups'],
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': consts.PLUGIN_NAME_PATTERN},
                'title': {'type': 'string'},
                'version': {'type': 'string'},
                'package_version': self.package_version,
                'description': {'type': 'string'},
                'fuel_version': self.list_of_strings,
                'licenses': self.list_of_strings,
                'authors': self.list_of_strings,
                'groups': {'type': 'array', 'uniqueItems': True, 'items':
                           {'enum':
                            ['network',
                             'storage',
                             'storage::cinder',
                             'storage::glance',
                             'hypervisor',
                             'monitoring']}},
                'homepage': {'type': 'string'},
                'releases': {
                    'type': 'array',
                    'items': self.plugin_release_schema}},
                'hotplug': {'type': 'boolean'}
        }
