#!/usr/bin/env python3

from database import Base, ENGINE


Base.metadata.create_all(ENGINE)
