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

from flask import (
    Flask,
    abort,
    g,
    jsonify,
    make_response,
    redirect,
)
from flask_httpauth import HTTPBasicAuth
from flask_wtf import FlaskForm
from sqlalchemy import orm
from sqlalchemy.exc import IntegrityError
from wtforms import StringField, validators

from shorter import config
from shorter import database
from shorter.database import db_session
from shorter import exception
from shorter.shorten import BASE36_CHARS


auth = HTTPBasicAuth()
app = Flask(__name__)
# TODO move to envvar
app.secret_key = 'OGV1Ra6mUNiHyTeOxOa00QlZ09FeIxO'
# TODO enable CSRF
app.config['WTF_CSRF_ENABLED'] = False


OUR_HOSTNAME = urlparse(config.base_url).hostname
MAX_SHORTURL_LENGTH = 23


@auth.verify_password
def verify_password(username, password):
    try:
        user = db_session.query(database.User).filter_by(
            username=username).one()
    except orm.exc.NoResultFound:
        return False

    valid_password = user.check_password(password)
    if not valid_password:
        return False

    g.user = user
    return True


@app.after_request
def call_after_request_callbacks(response):
    for callback in getattr(g, 'after_request_callbacks', ()):
        callback(response)
    return response


@app.route("/")
@auth.login_required
def index():
    """Return the list of URLs that the logged in user has shortened"""
    return jsonify(
        [url.to_dict() for url in g.user.urls])


class ShortenForm(FlaskForm):
    url = StringField('url', validators=[validators.input_required()])
    shorturl = StringField(
        'shorturl',
        validators=[
            validators.optional(),
            validators.Regexp(
                r'^[{chars}]{{,23}}$'.format(chars=BASE36_CHARS),
                message=('Make sure the `shorturl` field is no more than 23 '
                         'alphanumeric chars.')
            )
        ])


@app.route("/", methods=['POST'])
@auth.login_required
def shorten():
    """Create a shortened url and return its representation

    :url: a valid URL which will be shortened

    """
    form = ShortenForm()
    if not form.validate():
        return jsonify(form.errors), 400

    url = form.url.data

    if urlparse(url).hostname == OUR_HOSTNAME:
        return jsonify({'error': "That is already a Shorter link."}), 400

    db_url = _save_url(url, form.shorturl.data, g.user)

    full_shorturl = urljoin(config.base_url, db_url.short)

    return jsonify(
        url=url,
        shorturl=full_shorturl)


def _save_url(url, shorturl, user):
    """Save URL to the database"""
    error_resp = make_response(
            jsonify(
                {
                    'error': (
                        "Could not create new link. "
                        "One with the given `shorturl` already exists")}),
            400)

    # first make sure it's not already in the database
    already_exists = db_session.query(database.Url).filter_by(
        short=shorturl).one_or_none()

    if already_exists:
        raise abort(error_resp)

    try:
        db_url = database.Url(
            url, short=shorturl, user=user)
    except exception.InvalidURL as e:
        abort(
            make_response(
                jsonify({'error': str(e)}),
                400))

    # between the time we checked for it, a different process might have
    # created it, so we could still get an IntegrityError because
    # `short` is not unique when saving it to the database
    db_session.add(db_url)
    try:
        db_session.commit()
    except IntegrityError as e:
        db_session.rollback()
        raise abort(error_resp)

    return db_url


@app.route("/<short>")
def expand(short):
    """Return information about a shortened URL

    :short: a string which identifies an already shortened URL

    """
    try:
        url = db_session.query(database.Url).filter_by(short=short).one()
    except orm.exc.NoResultFound:
        abort(404)

    return jsonify(url.to_dict())


@app.route("/<short>/redirect")
def redir(short):
    try:
        url = db_session.query(database.Url).filter_by(short=short).one()
    except orm.exc.NoResultFound:
        abort(404)

    @after_this_request
    def increment_accessed(response):
        # avoid concurrency issues by letting the database increment the
        # column
        url.accessed = database.Url.accessed + 1
        db_session.add(url)
        db_session.commit()

    return redirect(url.url)


def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
