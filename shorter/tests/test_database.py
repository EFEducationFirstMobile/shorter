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

from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy import orm

from shorter import database
from shorter import exception

EXAMPLE_URL = 'http://example.com'


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite://')
        database.Base.metadata.create_all(bind=engine)
        Session = orm.sessionmaker(bind=engine)
        self.session = Session()

    def _create_url(self):
        url = database.Url(EXAMPLE_URL)
        self.session.add(url)
        self.session.commit()
        return url

    def test_create_one(self):
        url = self._create_url()
        self.assertEqual(url.id, 1)
        self.assertEqual(url.url, EXAMPLE_URL)

    def test_short_url_attribute_one(self):
        url = self._create_url()
        self.assertEqual(url.short, '1')

    def test_short_url_attribute_base36(self):
        url = database.Url(EXAMPLE_URL)
        url.id = '47'
        self.session.add(url)
        self.session.commit()
        self.assertEqual(url.short, '1b')

    def test_invalid_url_raises(self):
        self.assertRaises(exception.InvalidURL, database.Url, '')
        self.assertRaises(exception.InvalidURL, database.Url, 'not-a-url')
        self.assertRaises(exception.InvalidURL, database.Url,
                          'http://almost-a.url/but/?it=has& spa ces')

    def test_url_spaces_are_stripped(self):
        url = database.Url('  {0}   '.format(EXAMPLE_URL))
        self.assertEqual(url.url, EXAMPLE_URL)

    def test_query_by_short(self):
        self._create_url()
        try:
            self.session.query(database.Url).filter_by(short='1').one()
        except orm.exc.NoResultFound:
            self.fail("Could not find test URL when querying by the "
                      "'short' attribute.")

    def test_short_attr_is_unique(self):
        url = self._create_url()
        url2 = database.Url(EXAMPLE_URL)
        url2.short = url.short
        self.session.add(url2)
        self.assertRaises(exc.IntegrityError, self.session.commit)

    def test_short_attr_only_updates_one_row(self):
        url1 = self._create_url()
        url2 = self._create_url()
        self.session.add(url1)
        self.session.add(url2)
        self.assertNotEqual(url1.short, url2.short)
