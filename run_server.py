#!/usr/bin/env python3

from shorter.database import (
    User,
    db_session,
)
from shorter.web import app

if __name__ == "__main__":
    # makes testing easier
    test_user_created = db_session.query(User).filter_by(
        username='jimmy').one_or_none()
    if not test_user_created:
        db_session.add(
            User(username='jimmy', password='secret'))
        db_session.commit()

    app.run()
