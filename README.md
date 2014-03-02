# Shorter

Shorter is a simple URL Shortener built with Flask and SQLAlchemy named after a famous jazz musician.

## Installation


To initialize the database, first configure the database connection in config.py (you'll have to create the database and user yourself) and then run the ``init_db.py`` script in the project's directory.

The ``sql_connection`` configuration value in ``config.py`` should be a valid SQLAlchemy database url: http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls
