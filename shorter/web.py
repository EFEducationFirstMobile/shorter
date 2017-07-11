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

from urllib.parse import urljoin, urlparse

from flask import Flask, abort, jsonify, redirect, render_template
from flask_wtf import FlaskForm
from sqlalchemy import orm
from wtforms import StringField, validators

from shorter import config
from shorter import database
from shorter.database import db_session
from shorter import exception
from shorter.utils import request_wants_json


app = Flask(__name__)
# TODO move to envvar
app.secret_key = 'OGV1Ra6mUNiHyTeOxOa00QlZ09FeIxO'

OUR_HOSTNAME = urlparse(config.base_url).hostname
MAX_SHORTURL_LENGTH = 23

@app.route("/")
def index():
    return render_template("index.html")


class ShortenForm(FlaskForm):
    url = StringField('url', validators=[validators.input_required()])
    shorturl = StringField(
        'shorturl',
        validators=[
            validators.optional(),
            validators.Length(max=MAX_SHORTURL_LENGTH)
        ])


@app.route("/", methods=['POST'])
def shorten():
    """Shortens a URL, returning another URL which will redirect to :url:

    :url: a valid URL which will be shortened

    """
    form = ShortenForm()
    if not form.validate():
        return jsonify(form.errors), 400

    url = form.url.data
    try:
        db_url = database.Url(url, short=form.shorturl.data)
    except exception.InvalidURL as e:
        abort(400, e)

    if urlparse(url).hostname == OUR_HOSTNAME:
        abort(400, "That is already a Shorter link.")

    db_session.add(db_url)
    db_session.commit()

    full_shorturl = urljoin(config.base_url, db_url.short)

    if request_wants_json():
        return jsonify(
            url=url,
            shorturl=full_shorturl)
    return render_template("shorter.html", original=url, shorter=full_shorturl)


@app.route("/<short>")
def expand(short):
    """Redirects the user to a URL which has already been shortened

    :short: a string which identifies an already shortened URL

    """
    try:
        url = db_session.query(database.Url).filter_by(short=short).one()
    except orm.exc.NoResultFound:
        abort(404)

    if request_wants_json():
        full_shorturl = urljoin(config.base_url, url.short)
        return jsonify(
            url=url.url,
            shorturl=full_shorturl
        )
    return redirect(url.url)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
