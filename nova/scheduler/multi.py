# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010 Openstack, LLC.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""
Scheduler that allows routing some calls to one driver and others to another.
"""

from nova import flags
from nova.openstack.common import cfg
from nova import utils
from nova.scheduler import driver


multi_scheduler_opts = [
    cfg.StrOpt('compute_scheduler_driver',
               default='nova.scheduler.chance.ChanceScheduler',
               help='Driver to use for scheduling compute calls'),
    cfg.StrOpt('volume_scheduler_driver',
               default='nova.scheduler.chance.ChanceScheduler',
               help='Driver to use for scheduling volume calls'),
    ]

FLAGS = flags.FLAGS
FLAGS.register_opts(multi_scheduler_opts)

# A mapping of methods to topics so we can figure out which driver to use.
_METHOD_MAP = {'run_instance': 'compute',
               'prep_resize': 'compute',
               'live_migration': 'compute',
               'create_volume': 'volume',
               'create_volumes': 'volume'}


class MultiScheduler(driver.Scheduler):
    """A scheduler that holds multiple sub-schedulers.

    This exists to allow flag-driven composibility of schedulers, allowing
    third parties to integrate custom schedulers more easily.

    """

    def __init__(self):
        super(MultiScheduler, self).__init__()
        compute_driver = utils.import_object(FLAGS.compute_scheduler_driver)
        volume_driver = utils.import_object(FLAGS.volume_scheduler_driver)

        self.drivers = {'compute': compute_driver,
                        'volume': volume_driver}

    def __getattr__(self, key):
        if not key.startswith('schedule_'):
            raise AttributeError(key)
        method = key[len('schedule_'):]
        if method not in _METHOD_MAP:
            raise AttributeError(key)
        return getattr(self.drivers[_METHOD_MAP[method]], key)

    def schedule(self, context, topic, method, *_args, **_kwargs):
        return self.drivers[topic].schedule(context, topic,
                method, *_args, **_kwargs)
