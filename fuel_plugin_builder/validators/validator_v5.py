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

from fuel_plugin_builder import utils

from fuel_plugin_builder.validators.schemas import SchemaV5
from fuel_plugin_builder.validators import ValidatorV4

logger = logging.getLogger(__name__)


class ValidatorV5(ValidatorV4):

    schema = SchemaV5()

    def __init__(self, *args, **kwargs):
        super(ValidatorV5, self).__init__(*args, **kwargs)

    @property
    def basic_version(self):
        return '8.0'

    def check_tasks_schema(self):
        pass

    def check_tasks(self):
        if utils.exists(self.tasks_path):
            # logger.warn('tasks.yaml file is deprecated')
            # TODO(ikutukov): warn when warning mechanism will be available
            pass
