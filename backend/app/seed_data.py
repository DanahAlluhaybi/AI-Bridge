"""
seed_data.py
------------
Phase 2 needs *something* to show in the Enterprise Systems page the
very first time you run the app -- an empty table would make it
impossible to tell "the feature works" from "the feature is broken and
shows nothing either way". So on every backend startup we check: if the
enterprise_systems table is empty, load five realistic (but 100%
fictional) example systems from mock-data/enterprise_systems.json and
insert them.

This only ever fires once per database file. If you've already added,
edited, or deleted systems yourself, `already_seeded` is True and this
function does nothing -- it never overwrites your changes.

The mock data lives in its own JSON file (not hardcoded as a Python
dict here) so that "the data" and "the code that loads the data" are
separate -- you can open mock-data/enterprise_systems.json and edit the
example systems without touching any Python.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from . import models

# __file__ is backend/app/seed_data.py.
#   .parent           -> backend/app
#   .parent.parent     -> backend
#   .parent.parent.parent -> ai-bridge (the project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MOCK_DATA_FILE = PROJECT_ROOT / "mock-data" / "enterprise_systems.json"


def _load_mock_systems() -> list[dict]:
    with open(MOCK_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_enterprise_systems(db: Session) -> None:
    already_seeded = db.query(models.EnterpriseSystem).first() is not None
    if already_seeded:
        return

    for record in _load_mock_systems():
        db.add(models.EnterpriseSystem(**record))
    db.commit()
