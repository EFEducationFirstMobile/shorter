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

from urllib.parse import urljoin, urlparse

from flask import Flask
from flask import abort, render_template, request

from shorter import config
from shorter import database
from shorter.database import db_session
from shorter import exception

app = Flask(__name__)

OUR_HOSTNAME = urlparse(config.base_url).hostname


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/", methods=['POST'])
def shorten():
    """Shortens a URL, returning another URL which will redirect to :url:

    :url: a valid URL which will be shortened

    """
    try:
        url = request.form['url']
    except KeyError:
        abort(400, "The required form value argument 'url' was not provided.")

    try:
        db_url = database.Url(url)
    except exception.InvalidURL as e:
        abort(400, e)

    if urlparse(url).hostname == OUR_HOSTNAME:
        abort(400, "That is already a Shorter link.")

    db_session.add(db_url)
    db_session.commit()

    shorter = urljoin(config.base_url, db_url.short)

    return shorter


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
