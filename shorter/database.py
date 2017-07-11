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

import hmac
import re
from urllib.parse import urljoin

import bcrypt
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
    event,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    backref,
    relationship,
    scoped_session,
    sessionmaker,
    validates)

from shorter import (
    config,
    exception,
)
from shorter.shorten import int_to_base36


ENGINE = create_engine(config.sql_connection)
# rounds for the bcrypt salt algo
SALT_ROUNDS = 8

Base = declarative_base()
db_session = scoped_session(sessionmaker(bind=ENGINE))


class Url(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    short = Column(String, index=True, unique=True)
    created = Column(DateTime(), nullable=False, default=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    accessed = Column(Integer, nullable=False, server_default='0')

    user = relationship(
        'User',
        backref=backref('urls'))

    def __init__(self, url, user, short=None):
        self.url = url.strip()
        self.user = user
        if not short:
            short = None
        self.short = short

    def __repr__(self):
        return "<Url(id={0} url={1})>".format(self.id, self.url)

    @validates('url')
    def validate_url(self, key, url):
        # thank you django.core.validators
        regex = re.compile(
            r'^((?:http|ftp)s?://)?'  # scheme
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

    def to_dict(self):
        full_shorturl = urljoin(config.base_url, self.short)
        return {
            'url': self.url,
            'shorturl': full_shorturl,
            'accessed': self.accessed,
            'created': self.created.isoformat(),
        }


urls = Table('urls', Base.metadata, autoload=True, autoload_with=ENGINE)


# rely on the database to give us a unique sequential id which we then
# use to store our own identifier for the urls
@event.listens_for(Url, 'after_insert')
def base36ify(mapper, connect, target, retval=True):
    # if `short` was already set, then we don't need to generate it
    if target.short is None:
        connect.execute(urls.update().where(urls.c.id == target.id),
                        {'short': int_to_base36(int(target.id))})
    return target


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    @validates('password')
    def validate_password(self, _, password):
        return _hash_password(password)

    def check_password(self, password):
        return hmac.compare_digest(
            self.password.encode('utf-8'),
            bcrypt.hashpw(
                password.encode('utf-8'),
                self.password.encode('utf-8')))


def _hash_password(password):
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(SALT_ROUNDS)).decode('utf-8')
