# -*- coding: utf-8 -*-
# Copyright (c) 2014-2017 Ionuț Arțăriși <ionut@artarisi.eu>
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

import base64
from urllib.parse import urljoin
import unittest

from sqlalchemy import create_engine

from shorter import (
    config,
    database,
)
from shorter.database import Base, db_session
from shorter.utils import get_response_json
from shorter.web import app

TEST_URL = 'http://example.com'


class WebTest(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite://')
        db_session.configure(bind=engine)
        Base.metadata.create_all(bind=engine)

        app.testing = True
        # TODO test with csrf enabled
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        username = 'foo'
        password = 'bar'
        db_session.add(
            database.User(
                username=username, password=password))
        db_session.commit()

        base64_creds = base64.standard_b64encode(
            '{}:{}'.format(username, password).encode('utf-8')
        ).decode('utf-8')
        self._auth_headers = {
            'Authorization': 'Basic {}'.format(base64_creds)}

    def tearDown(self):
        db_session.remove()

    def test_empty_post(self):
        resp = self.json_post('/', data=dict())
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'url': ['This field is required.']})

    def test_invalid_url(self):
        resp = self.json_post('/', data=dict(url='not-a-url'))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json['error'], "This URL is malformed: not-a-url")

    def test_our_url(self):
        resp = self.json_post('/', data=dict(url=config.base_url + '/foo'))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("That is already a Shorter link.",
                      resp.data.decode('utf-8'))

    def test_custom_url(self):
        shorturl = "myshorturl"
        resp = self.json_post(
            '/', data=dict(
                url=TEST_URL,
                shorturl=shorturl))
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn(
            urljoin(config.base_url, shorturl), resp.data.decode('utf-8'))

    def test_custom_url_json(self):
        shorturl = "myshorturl"
        resp = self.json_post(
            '/', data=dict(
                url=TEST_URL,
                shorturl=shorturl))
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(
            resp.json,
            {'shorturl': urljoin(config.base_url, shorturl),
             'url': TEST_URL})

    def test_custom_url_already_taken(self):
        # given a shorturl was already used
        shorturl = "myshorturl"
        self.json_post(
            '/', data=dict(
                url=TEST_URL,
                shorturl=shorturl))

        # when trying to shorten (a different) url to the same shorturl
        resp = self.json_post(
            '/', data=dict(
                url=urljoin(TEST_URL, '1'),
                shorturl=shorturl))
        self.assertEqual(
            resp.json,
            {
                'error': (
                    'Could not create new link. '
                    'One with the given `shorturl` already exists')})

    def test_custom_url_too_long(self):
        shorturl = "o" * 24
        resp = self.json_post(
            '/', data=dict(
                url=TEST_URL,
                shorturl=shorturl))
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(
            resp.json,
            {'shorturl': ['Make sure the `shorturl` field is no more than 23 '
                          'alphanumeric chars.']})

    def test_custom_url_disallowed_characters(self):
        shorturl = "ș"
        resp = self.json_post(
            '/', data=dict(
                url=TEST_URL,
                shorturl=shorturl))
        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertEqual(
            resp.json,
            {'shorturl': ['Make sure the `shorturl` field is no more than 23 '
                          'alphanumeric chars.']})

    def test_shortened_url(self):
        resp = self.json_post('/', data=dict(url=TEST_URL))

        self.assertEqual(resp.status_code, 200)
        self.assertIn(urljoin(config.base_url, "1"), resp.data.decode('utf-8'))

    def test_expand_not_found(self):
        resp = self.client.get('/not-found')

        self.assertEqual(resp.status_code, 404)

    def test_redirect(self):
        self.json_post('/', data=dict(url=TEST_URL))
        resp = self.client.get('/1/redirect')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers['location'], TEST_URL)

        url = db_session.query(database.Url).one()
        self.assertEqual(url.accessed, 1)

    def test_expand_json(self):
        self.json_post('/', data=dict(url=TEST_URL))
        default_shorturl = '/1'
        resp = self.json_get(default_shorturl)

        db_url = db_session.query(database.Url).one()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json,
            {'shorturl': urljoin(config.base_url, default_shorturl),
             'url': TEST_URL,
             'created': db_url.created.isoformat(),
             'accessed': 0})

    def test_list_urls(self):
        expected_urls = [
            {
                'shorturl': urljoin(config.base_url, str(i + 1)),
                'url': urljoin(TEST_URL, str(i)),
                'accessed': 0
            } for i in range(3)]

        for url in expected_urls:
            self.json_post('/', data=dict(url=url['url']))

        resp = self.json_get('/')
        self.assertEqual(resp.status_code, 200, resp.data)
        for url, expected_url in zip(resp.json, expected_urls):
            self.assertEqual(url['shorturl'], expected_url['shorturl'])
            self.assertEqual(url['url'], expected_url['url'])
            self.assertEqual(url['accessed'], expected_url['accessed'])
            self.assertIsNotNone(url['created'])

    def json_get(self, *args, **kwargs):
        response = self._json_req(*args, method='get', **kwargs)
        return response

    def json_post(self, *args, **kwargs):
        response = self._json_req(*args, method='post', **kwargs)
        return response

    def _json_req(self, *args, method='get', **kwargs):
        headers = dict(
            Accept='application/json',
            **self._auth_headers
        )

        try:
            kwargs['headers'].extend(headers)
        except KeyError:
            kwargs['headers'] = headers

        method = getattr(self.client, method)
        response = method(*args, **kwargs)
        response.json = get_response_json(response)
        return response
