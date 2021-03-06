# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Julien Danjou <julien@danjou.info>
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

import mock

from ceilometer.central import manager
from ceilometer.image import glance
from ceilometer.openstack.common import context
from ceilometer.openstack.common.fixture import moxstubout
from ceilometer.openstack.common import test

IMAGE_LIST = [
    type('Image', (object,),
         {u'status': u'queued',
          u'name': "some name",
          u'deleted': False,
          u'container_format': None,
          u'created_at': u'2012-09-18T16:29:46',
          u'disk_format': None,
          u'updated_at': u'2012-09-18T16:29:46',
          u'properties': {},
          u'min_disk': 0,
          u'protected': False,
          u'id': u'1d21a8d0-25f4-4e0a-b4ec-85f40237676b',
          u'location': None,
          u'checksum': None,
          u'owner': u'4c8364fc20184ed7971b76602aa96184',
          u'is_public': True,
          u'deleted_at': None,
          u'min_ram': 0,
          u'size': 2048}),
    type('Image', (object,),
         {u'status': u'active',
          u'name': "hello world",
          u'deleted': False,
          u'container_format': None,
          u'created_at': u'2012-09-18T16:27:41',
          u'disk_format': None,
          u'updated_at': u'2012-09-18T16:27:41',
          u'properties': {},
          u'min_disk': 0,
          u'protected': False,
          u'id': u'22be9f90-864d-494c-aa74-8035fd535989',
          u'location': None,
          u'checksum': None,
          u'owner': u'9e4f98287a0246daa42eaf4025db99d4',
          u'is_public': True,
          u'deleted_at': None,
          u'min_ram': 0,
          u'size': 0}),
    type('Image', (object,),
         {u'status': u'queued',
          u'name': None,
          u'deleted': False,
          u'container_format': None,
          u'created_at': u'2012-09-18T16:23:27',
          u'disk_format': "raw",
          u'updated_at': u'2012-09-18T16:23:27',
          u'properties': {},
          u'min_disk': 0,
          u'protected': False,
          u'id': u'8d133f6c-38a8-403c-b02c-7071b69b432d',
          u'location': None,
          u'checksum': None,
          u'owner': u'5f8806a76aa34ee8b8fc8397bd154319',
          u'is_public': True,
          u'deleted_at': None,
          u'min_ram': 0,
          u'size': 1024}),
    # Make one duplicate private image to test the iter_images method.
    type('Image', (object,),
         {u'status': u'queued',
          u'name': "some name",
          u'deleted': False,
          u'container_format': None,
          u'created_at': u'2012-09-18T16:29:46',
          u'disk_format': None,
          u'updated_at': u'2012-09-18T16:29:46',
          u'properties': {},
          u'min_disk': 0,
          u'protected': False,
          u'id': u'1d21a8d0-25f4-4e0a-b4ec-85f40237676b',
          u'location': None,
          u'checksum': None,
          u'owner': u'4c8364fc20184ed7971b76602aa96184',
          u'is_public': True,
          u'deleted_at': None,
          u'min_ram': 0,
          u'size': 2048}),
]


class _BaseObject(object):
    pass


class TestManager(manager.AgentManager):

    def __init__(self):
        super(TestManager, self).__init__()
        self.keystone = None


class TestImagePollster(test.BaseTestCase):

    def fake_get_glance_client(self, ksclient):
        glanceclient = _BaseObject()
        setattr(glanceclient, "images", _BaseObject())
        setattr(glanceclient.images,
                "list", lambda *args, **kwargs: iter(IMAGE_LIST))
        return glanceclient

    @mock.patch('ceilometer.pipeline.setup_pipeline', mock.MagicMock())
    def setUp(self):
        super(TestImagePollster, self).setUp()
        self.stubs = self.useFixture(moxstubout.MoxStubout()).stubs
        self.context = context.get_admin_context()
        self.manager = TestManager()
        self.stubs.Set(glance._Base, 'get_glance_client',
                       self.fake_get_glance_client)

    def test_iter_images(self):
        # Tests whether the iter_images method returns an unique image
        # list when there is nothing in the cache
        images = list(glance.ImagePollster().
                      _iter_images(self.manager.keystone, {}))
        self.assertEqual(len(images), len(set(image.id for image in images)))

    def test_iter_images_cached(self):
        # Tests whether the iter_images method returns the values from
        # the cache
        cache = {'images': []}
        images = list(glance.ImagePollster().
                      _iter_images(self.manager.keystone, cache))
        self.assertEqual(images, [])

    def test_image(self):
        samples = list(glance.ImagePollster().get_samples(self.manager, {}))
        self.assertEqual(len(samples), 3)
        for sample in samples:
            self.assertEqual(sample.volume, 1)

    def test_image_size(self):
        samples = list(glance.ImageSizePollster().get_samples(self.manager,
                                                              {}))
        self.assertEqual(len(samples), 3)
        for image in IMAGE_LIST:
            self.assertTrue(
                any(map(lambda sample: sample.volume == image.size,
                        samples)))

    def test_image_get_sample_names(self):
        samples = list(glance.ImagePollster().get_samples(self.manager, {}))
        self.assertEqual(set([s.name for s in samples]),
                         set(['image']))

    def test_image_size_get_sample_names(self):
        samples = list(glance.ImageSizePollster().get_samples(self.manager,
                                                              {}))
        self.assertEqual(set([s.name for s in samples]),
                         set(['image.size']))
