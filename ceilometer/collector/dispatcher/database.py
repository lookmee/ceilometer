# -*- encoding: utf-8 -*-
#
# Copyright 2013 IBM Corp
#
# Author: Tong Li <litong01@us.ibm.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from ceilometer.collector import dispatcher
from ceilometer.openstack.common import log
from ceilometer.openstack.common import timeutils
from ceilometer.publisher import rpc as publisher_rpc
from ceilometer import storage

LOG = log.getLogger(__name__)


class DatabaseDispatcher(dispatcher.Base):
    '''Dispatcher class for recording metering data into database.

    The dispatcher class which records each meter into a database configured
    in ceilometer configuration file.

    To enable this dispatcher, the following section needs to be present in
    ceilometer.conf file

    dispatchers = database
    '''
    def __init__(self, conf):
        super(DatabaseDispatcher, self).__init__(conf)
        self.storage_conn = storage.get_connection(conf)

    def record_metering_data(self, context, data):
        # We may have receive only one counter on the wire
        if not isinstance(data, list):
            data = [data]

        for meter in data:
            LOG.debug('metering data %s for %s @ %s: %s',
                      meter['counter_name'],
                      meter['resource_id'],
                      meter.get('timestamp', 'NO TIMESTAMP'),
                      meter['counter_volume'])
            if publisher_rpc.verify_signature(
                    meter,
                    self.conf.publisher_rpc.metering_secret):
                try:
                    # Convert the timestamp to a datetime instance.
                    # Storage engines are responsible for converting
                    # that value to something they can store.
                    if meter.get('timestamp'):
                        ts = timeutils.parse_isotime(meter['timestamp'])
                        meter['timestamp'] = timeutils.normalize_time(ts)
                    self.storage_conn.record_metering_data(meter)
                except Exception as err:
                    LOG.exception('Failed to record metering data: %s', err)
            else:
                LOG.warning(
                    'message signature invalid, discarding message: %r',
                    meter)

    def record_events(self, events):
        if not isinstance(events, list):
            events = [events]

        return self.storage_conn.record_events(events)
