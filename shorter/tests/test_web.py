# -*- coding: utf-8 -*-
# Copyright (c) 2014 Ionuț Arțăriși <ionut@artarisi.eu>
# This file is part of shorter.

# shorter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# shorter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with shorter. If not, see <http://www.gnu.org/licenses/>.

import unittest

from shorter import config
from shorter.web import app


class WebTest(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_empty_post(self):
        resp = self.client.post('/', data=dict())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("The required form value argument 'url' "
                      "was not provided.", resp.data.decode('utf-8'))

    def test_invalid_url(self):
        resp = self.client.post('/', data=dict(url='not-a-url'))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("This URL is malformed: not-a-url",
                      resp.data.decode('utf-8'))

    def test_our_url(self):
        resp = self.client.post('/', data=dict(url=config.base_url + '/foo'))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("That is already a Shorter link.",
                      resp.data.decode('utf-8'))
