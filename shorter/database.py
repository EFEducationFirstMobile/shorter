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

import re

from sqlalchemy import Column, Integer, String, Table
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates

from shorter.config import sql_connection
from shorter import exception
from shorter.shorten import int_to_base36

Base = declarative_base()
ENGINE = create_engine(sql_connection)


class Url(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    short = Column(String)

    def __init__(self, url):
        self.url = url.strip()

    def __repr__(self):
        return "<Url(id={0} url={1})>".format(self.id, self.url)

    @validates('url')
    def validate_url(self, key, url):
        # thank you django.core.validators
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # scheme
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not regex.match(url):
            raise exception.InvalidURL("This URL is malformed: " + url)
        return url

urls = Table('urls', Base.metadata, autoload=True, autoload_with=ENGINE)


@event.listens_for(Url, 'after_insert')
def base36ify(mapper, connect, target, retval=True):
    connect.execute(urls.update(), {'short': int_to_base36(int(target.id))})
    return target
