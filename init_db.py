#!/usr/bin/env python3

from shorter.database import Base, ENGINE


Base.metadata.create_all(ENGINE)
