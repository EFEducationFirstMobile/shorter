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
from sqlalchemy.orm import sessionmaker

from shorter import database


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite://')
        database.Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def test_create_one(self):
        example_url = 'http://example.com'
        url = database.Url(example_url)
        self.session.add(url)
        self.session.commit()
        self.assertEqual(url.id, 1)
        self.assertEqual(url.url, example_url)
