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

import logging

from fuel_plugin_builder import errors
from fuel_plugin_builder import utils
from fuel_plugin_builder.validators.schemas import SchemaV4
from fuel_plugin_builder.validators.schemas import TASK_ROLE_PATTERN
from fuel_plugin_builder.validators import ValidatorV3
import jsonschema
from os.path import join as join_path
import re
import six

logger = logging.getLogger(__name__)


class FormatCheckerV4(jsonschema.FormatChecker):

    def check(self, instance, format):
        """Check whether the instance conforms to the given format.

        :argument instance: the instance to check
        :type: any primitive type (str, number, bool)
        :argument str format: the format that instance should conform to
        :raises: :exc:`FormatError` if instance does not conform to format
        """

        if format not in self.checkers:
            return

        # For safety reasons custom checkers can be registered with
        # allowed exception types. Anything else will fall into the
        # default formatter.
        func, raises = self.checkers[format]
        result, cause = None, None

        try:
            result = func(instance)
        except raises as e:
            cause = e
        if not result:
            msg = "%r is not a %r" % (instance, format)
            raise jsonschema.exceptions.FormatError(msg, cause=cause)


class ValidatorV4(ValidatorV3):

    schema = SchemaV4()

    def __init__(self, *args, **kwargs):
        super(ValidatorV4, self).__init__(format_checker=FormatCheckerV4(),
                                          *args, **kwargs)
        self.components_path = join_path(self.plugin_path, 'components.yaml')

    @property
    def basic_version(self):
        return '8.0'

    def check_metadata_schema(self):
        self.validate_file_by_schema(
            self.schema.metadata_schema,
            self.meta_path,
            allow_not_exists=True)

    def check_tasks_schema(self):
        self.validate_file_by_schema(
            self.schema.tasks_schema,
            self.tasks_path,
            allow_empty=True
        )

    def check_schemas(self):
        logger.debug('Start schema checking "%s"', self.plugin_path)
        self.check_metadata_schema()
        self.check_tasks_schema()
        self.check_env_config_attrs()
        self.check_deployment_tasks_schema()
        self.check_network_roles_schema()
        self.check_node_roles_schema()
        self.check_volumes_schema()
        self.check_components_schema()

    def check_components_schema(self):
        self.validate_file_by_schema(self.schema.components_schema,
                                     self.components_path,
                                     allow_not_exists=True)

    def check_deployment_tasks(self):
        logger.debug(
            'Start deployment tasks checking "%s"',
            self.deployment_tasks_path)

        deployment_tasks = utils.parse_yaml(self.deployment_tasks_path)
        schemas = {
            'puppet': self.schema.puppet_task,
            'shell': self.schema.shell_task,
            'group': self.schema.group_task,
            'skipped': self.schema.skipped_task,
            'copy_files': self.schema.copy_files_task,
            'sync': self.schema.sync_task,
            'upload_file': self.schema.upload_file_task,
            'stage': self.schema.stage_task,
            'reboot': self.schema.reboot_task}

        for idx, deployment_task in enumerate(deployment_tasks):
            if deployment_task['type'] not in schemas:
                error_msg = 'There is no such task type:' \
                            '{0}'.format(deployment_task['type'])
                raise errors.ValidationError(error_msg)
            logger.debug("Checking task %s" % deployment_task.get('id'))
            self.validate_schema(
                deployment_task,
                schemas[deployment_task['type']],
                self.deployment_tasks_path,
                value_path=[idx])

    def check_tasks(self):
        """Check legacy tasks.yaml."""
        logger.debug('Start tasks checking "%s"', self.tasks_path)
        if utils.exists(self.tasks_path):
            # todo(ikutukov): remove self._check_tasks
            tasks = utils.parse_yaml(self.tasks_path)
            if tasks is None:
                return

            schemas = {
                'puppet': self.schema.puppet_parameters,
                'shell': self.schema.shell_parameters,
                'reboot': self.schema.reboot_parameters}

            for idx, task in enumerate(tasks):
                logger.debug("Checking task %s" % task.get('id'))
                self.validate_schema(
                    task.get('parameters'),
                    schemas[task['type']],
                    self.tasks_path,
                    value_path=[idx, 'parameters'])
        else:
            logger.debug('File "%s" doesn\'t exist', self.tasks_path)


@jsonschema.FormatChecker.cls_checks('fuel_task_role_format')
def _validate_role(instance):
    if isinstance(instance, six.string_types):
        if instance.startswith('/') and instance.endswith('/'):
            try:
                if re.compile(instance[1:-1]):
                    return True
            except Exception:
                pass
        else:
            try:
                if re.match(TASK_ROLE_PATTERN, instance):
                    return True
            except Exception:
                pass

        raise errors.TaskFieldError("Task role field should be either "
                                    "a valid regexp enclosed "
                                    "by slashes or a string "
                                    "of '{0}' or an array "
                                    "of those. Got '{1}' instead".
                                    format(TASK_ROLE_PATTERN, instance))
