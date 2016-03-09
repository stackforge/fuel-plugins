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

from fuel_plugin_builder.validators import schemas

from fuel_plugin_builder.validators.base import BaseValidator
from fuel_plugin_builder.validators.base import Inspection

from fuel_plugin_builder.validators.checks import EnvConfigAttrsIsValidV1
from fuel_plugin_builder.validators.checks import IsFile
from fuel_plugin_builder.validators.checks import IsReleaseCompatible
from fuel_plugin_builder.validators.checks import JSONSchemaIsValid
from fuel_plugin_builder.validators.checks import MultiJSONSchemaIsValid
from fuel_plugin_builder.validators.checks import ScriptsAndRepoPathsIsValid


class ValidatorV4(BaseValidator):
    schema_v4 = schemas.SchemaV4()
    schema_v3 = schemas.SchemaV3()

    @property
    def inspections(self):
        return [
            Inspection(
                name='meta',
                path=self.get_absolute_path('metadata.yaml'),
                checks=[
                    IsFile(),
                    IsReleaseCompatible('8.0'),
                    JSONSchemaIsValid(self.schema_v4.metadata_schema),
                    ScriptsAndRepoPathsIsValid(
                        base_path=self.get_absolute_path())
                ]
            ),
            Inspection(
                name='env conf',
                path=self.get_absolute_path('environment_config.yaml'),
                checks=[
                    IsFile(),
                    JSONSchemaIsValid(self.schema_v4.attr_root_schema),
                    EnvConfigAttrsIsValidV1()
                ]
            ),
            Inspection(
                name='deployment tasks',
                path=self.get_absolute_path('deployment_tasks.yaml'),
                checks=[
                    IsFile(),
                    JSONSchemaIsValid(self.schema_v4.deployment_task_schema),
                    MultiJSONSchemaIsValid({
                        'puppet': self.schema_v4.puppet_task,
                        'shell': self.schema_v4.shell_task,
                        'group': self.schema_v4.group_task,
                        'skipped': self.schema_v4.skipped_task,
                        'copy_files': self.schema_v4.copy_files_task,
                        'sync': self.schema_v4.sync_task,
                        'upload_file': self.schema_v4.upload_file_task,
                        'stage': self.schema_v4.stage_task,
                        'reboot': self.schema_v4.reboot_task
                    })
                ]
            ),
            Inspection(
                name='network roles',
                path=self.get_absolute_path('network_roles.yaml'),
                checks=[
                    IsFile(required=False),
                    JSONSchemaIsValid(self.schema_v4.network_roles_schema)
                ]
            ),
            Inspection(
                name='volumes',
                path=self.get_absolute_path('volumes.yaml'),
                checks=[
                    IsFile(required=False),
                    JSONSchemaIsValid(self.schema_v4.volume_schema)
                ]
            ),
            Inspection(
                name='legacy tasks',
                path=self.get_absolute_path('tasks.yaml'),
                checks=[
                    IsFile(required=True),
                    JSONSchemaIsValid(self.schema_v3.tasks_schema)
                ]
            ),
            Inspection(
                name='components',
                path=self.get_absolute_path('components.yaml'),
                checks=[
                    IsFile(required=False),
                    JSONSchemaIsValid(self.schema_v4.components_schema)
                ]
            )
        ]
