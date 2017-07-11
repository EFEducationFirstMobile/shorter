# Shorter

Shorter is a simple URL Shortener built with Flask and SQLAlchemy named after a famous jazz musician.

## Installation

Shorter has only been tested with python 3.5.2.

Install the requirements from the ``requirements.txt`` file:

```
$ pip install -r requirements.txt
```

Then install any python database library you might need for SQLAlchemy e.g. for postgresql:

```
$ pip install psycopg2
```

To initialize the database, first configure the database connection in ``shorter/config.py`` (you'll have to create the database and user yourself) and then run the ``init_db.py`` script in the project's root directory.

The ``sql_connection`` configuration value in ``config.py`` should be a valid SQLAlchemy database url: http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls

In order to start the server, just run the ``run_server.py`` script in the project's root directory:

```bash
$ ./run_server.py
 * Running on http://127.0.0.1:5000/
```

## Features

1. convert a URL to a short URL of up to 23 characters

a. given only the original URL, generate a random short URL
```bash
curl -H "Authorization: Basic amltbXk6c2VjcmV0" -H "Content-Type: application/json" \
     --data '{"url": "http://example.com"}' -X POST http://localhost:5000/
{
  "shorturl": "http://localhost:5000/1",
  "url": "http://example.com"
}
```
b. given both the original URL and the desired short URL, create the desired short URL or give the user an error if that is not possible (ie. it was already taken)
```
curl -H "Authorization: Basic amltbXk6c2VjcmV0" -H "Content-Type: application/json" \
     --data '{"url": "http://example.com", "shorturl": "foobar"}' \
     http://localhost:5000/
{
  "shorturl": "http://localhost:5000/foobar",
  "url": "http://example.com"
}

curl -H "Authorization: Basic amltbXk6c2VjcmV0" -H "Content-Type: application/json" \
     --data '{"url": "http://example.com", "shorturl": "foobar"}' \
     http://localhost:5000/
{
  "error": "Could not create new link. One with the given `shorturl` already exists"
}
```
2. retrieve the original URL, given a short URL
```bash
curl -v -H "Authorization: Basic amltbXk6c2VjcmV0" -H "Content-Type: application/json" \
     http://localhost:5000/foobar/redirect
...
< HTTP/1.0 302 FOUND
< Content-Type: text/html; charset=utf-8
< Content-Length: 243
< Location: http://example.com
< Server: Werkzeug/0.12.2 Python/3.5.2
< Date: Tue, 11 Jul 2017 20:41:18 GMT
<
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>Redirecting...</title>
<h1>Redirecting...</h1>
```

3. retrieve information about an existing short URL created by the user, including:

a. what is the original URL

b. when the shortening happened

c. how many times the short URL has been accessed
```bash
curl -H "Authorization: Basic amltbXk6c2VjcmV0" -H "Content-Type: application/json" \
     http://localhost:5000/foobar
{
  "accessed": 1,
  "created": "2017-07-11T21:38:46.595948",
  "shorturl": "http://localhost:5000/foobar",
  "url": "http://example.com"
}
```

4. see a list of the URLs he/she created and the information detailed in item 3
```bash
curl -H "Authorization: Basic amltbXk6c2VjcmV0" -H "Content-Type: application/json" \
     http://localhost:5000/
[
  {
    "accessed": 0,
    "created": "2017-07-11T21:38:05.784988",
    "shorturl": "http://localhost:5000/1",
    "url": "http://example.com"
  },
  {
    "accessed": 2,
    "created": "2017-07-11T21:38:46.595948",
    "shorturl": "http://localhost:5000/foobar",
    "url": "http://example.com"
  }
]
```

## Testing

You can run the tests from the project's base directory using your favourite python test runner e.g.

```bash
$ python -m unittest discover
```
