"""
adapter/pipeline.py

Runs the full flow for one AdapterSource:

    Source Data -> Extraction -> Validation -> Normalization
                -> Classification -> Sensitive Data Detection
                -> AI-Ready Data

and saves the result: one ProcessingJob (the summary), one
ProcessingResult per record, and one DetectedIssue per problem found.
Each step above lives in its own module; this file only decides when
to call them and what to do with what comes back.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from .. import models
from . import classify, extract, normalize, validate

# Fields compared (raw vs. normalized) to decide whether a record
# counts as "cleaned". Excludes `amount`: a CSV amount like "45000.00"
# always arrives as a string and normalizes to the float 45000.0 --
# that's a type change, not a real cleanup, and counting it would mark
# almost every record "cleaned" even when nothing about it was messy.
FIELDS_TO_COMPARE_FOR_CLEANING = ["full_name", "city", "country", "phone", "date_field", "notes"]


def _was_meaningfully_cleaned(raw: Dict[str, Any], normalized: Dict[str, Any]) -> bool:
    for field in FIELDS_TO_COMPARE_FOR_CLEANING:
        if str(raw.get(field, "")).strip() != str(normalized.get(field, "")).strip():
            return True
    return False


def run_adapter(source: models.AdapterSource, db: Session) -> models.ProcessingJob:
    started_at = datetime.now(timezone.utc)
    raw_records = extract.extract(source.source_type, source.sample_file)

    # Validation runs on the raw data, before anything is fixed.
    all_issues: List[Dict[str, Any]] = list(validate.validate_records(raw_records))
    duplicate_indexes = validate.find_duplicate_keys(raw_records)

    job = models.ProcessingJob(
        source_id=source.id,
        status="Completed",
        started_at=started_at,
        records_processed=len(raw_records),
    )
    db.add(job)
    db.flush()  # assigns job.id without committing, so results/issues can reference it

    classification_summary = {"Public": 0, "Internal": 0, "Sensitive": 0}
    records_cleaned = 0

    for i, raw in enumerate(raw_records):
        normalized, normalize_issues = normalize.normalize_record(raw)
        for issue in normalize_issues:
            all_issues.append({**issue, "record_index": i})

        classification, sensitive_fields = classify.classify_record(normalized)
        classification_summary[classification] += 1

        is_duplicate = i in duplicate_indexes
        if _was_meaningfully_cleaned(raw, normalized) or normalize_issues:
            records_cleaned += 1

        db.add(models.ProcessingResult(
            job_id=job.id,
            record_index=i,
            raw_data=raw,
            normalized_data=normalized,
            classification=classification,
            is_duplicate=is_duplicate,
            sensitive_fields=sensitive_fields,
        ))

        for field in sensitive_fields:
            all_issues.append({
                "record_index": i,
                "issue_type": "Sensitive Field",
                "field_name": field,
                "description": f"'{field}' contains data classified as sensitive.",
                "severity": "Info",
            })

    for issue in all_issues:
        db.add(models.DetectedIssue(job_id=job.id, **issue))

    sensitive_field_issue_count = sum(
        1 for issue in all_issues if issue["issue_type"] == "Sensitive Field"
    )
    quality_issue_count = len(all_issues) - sensitive_field_issue_count

    job.records_cleaned = records_cleaned
    job.duplicate_records = len(duplicate_indexes)
    job.issues_detected = quality_issue_count
    job.sensitive_fields_detected = sensitive_field_issue_count
    job.classification_summary = classification_summary
    # A simple pass/fail read on unresolved quality issues -- not the AI
    # Readiness Score, which is a separately calculated value (see
    # readiness/engine.py).
    job.ai_readiness_status = (
        "Passed Basic Checks" if quality_issue_count == 0 else "Needs Attention"
    )
    job.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    return job
