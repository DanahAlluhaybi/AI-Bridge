"""
adapter/extract.py

Step 1 of the pipeline: pull the raw records out of a source, however
that source stores them, and return a plain list of dicts. Everything
after this point (validate, normalize, classify, detect) works on that
same plain shape regardless of source -- this is what lets one pipeline
handle CSV, JSON, REST API, and SQL Database sources without knowing
the difference past this point.

CSV and JSON do real parsing of real files via Python's standard
library. REST API and SQL Database are simulated: there are no live
systems to call, so those two read a local JSON file that stands in
for the response body / query rows a real call would return. Each
docstring says where a real integration would plug in.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

# backend/app/adapter/extract.py -> app -> backend -> project root
MOCK_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "mock-data" / "adapter_sources"


def extract_csv(filename: str) -> List[Dict[str, Any]]:
    """Real CSV parsing via the standard library csv module."""
    path = MOCK_DATA_DIR / filename
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def extract_json(filename: str) -> List[Dict[str, Any]]:
    """Real JSON parsing via the standard library json module."""
    path = MOCK_DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_rest_api(filename: str) -> List[Dict[str, Any]]:
    """
    Simulated. A real integration would call the system's API, e.g.:

        response = httpx.get(f"{system.base_url}/employees")
        return response.json()

    Here a local JSON file holds exactly the response body such a call
    would return, so the rest of the pipeline can't tell the difference.
    """
    return extract_json(filename)


def extract_sql(filename: str) -> List[Dict[str, Any]]:
    """
    Simulated. A real integration would query the system's database, e.g.:

        rows = connection.execute(text("SELECT * FROM employees")).mappings().all()
        return [dict(row) for row in rows]

    Here a local JSON file holds exactly the rows such a query would
    return.
    """
    return extract_json(filename)


EXTRACTORS = {
    "CSV": extract_csv,
    "JSON": extract_json,
    "REST API": extract_rest_api,
    "SQL Database": extract_sql,
}


def extract(source_type: str, filename: str) -> List[Dict[str, Any]]:
    """Dispatch to the extractor for the given source type."""
    return EXTRACTORS[source_type](filename)
