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

import multiprocessing
from urllib.parse import urljoin
import unittest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sqlalchemy import create_engine

from shorter import config
from shorter.database import Base, db_session
from shorter.web import app

TEST_URL = 'http://example.com'
config.base_url = 'http://localhost:5001'


class UITests(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()

        engine = create_engine('sqlite://')
        db_session.configure(bind=engine)
        Base.metadata.create_all(bind=engine)

        self.flask_process = multiprocessing.Process(
            target=app.run, args=('localhost', 5001))
        self.flask_process.start()

    def tearDown(self):
        self.driver.close()
        self.flask_process.terminate()

        db_session.remove()

    def test_shorter_says_hello(self):
        self.driver.get(config.base_url)

        banner = self.driver.find_element_by_id('banner')
        self.assertIn('Hi', banner.text)

    def test_index_has_form(self):
        self.driver.get(config.base_url)

        form = self.driver.find_element_by_id('shorten')
        self.assertEqual(form.tag_name, 'form')

    def test_shortens_url(self):
        self.driver.get(config.base_url)
        url_field = self.driver.find_element_by_name('url')
        url_field.send_keys(TEST_URL)
        url_field.send_keys(Keys.RETURN)

        shortened = self.driver.find_element_by_id('shorter')
        self.assertEqual(shortened.tag_name, 'a')
        self.assertEqual(urljoin(config.base_url, '1'), shortened.text)

        original = self.driver.find_element_by_id('original')
        self.assertEqual(original.tag_name, 'a')
        self.assertEqual(TEST_URL, original.text)

    def test_expand(self):
        self.driver.get(config.base_url)
        url_field = self.driver.find_element_by_name('url')
        url_field.send_keys(TEST_URL)
        url_field.send_keys(Keys.RETURN)

        self.driver.get(urljoin(config.base_url, '1'))
        self.assertIn('Example Domain', self.driver.title)

    def test_expand_not_found(self):
        self.driver.get(urljoin(config.base_url, 'not-found'))

        self.assertIn('404', self.driver.title)
