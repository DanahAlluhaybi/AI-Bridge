"""
seed_data.py

Loads example data into an empty database on startup so the app has
something realistic to show the first time it runs. Each seed function
checks whether its table already has rows and, if so, does nothing --
seeding only ever happens once per database file, and never overwrites
data that's already been added, edited, or deleted.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from . import models

# __file__ is backend/app/seed_data.py.
#   .parent               -> backend/app
#   .parent.parent        -> backend
#   .parent.parent.parent -> project root
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


# ---------------------------------------------------------------------------
# Legacy-to-AI Adapter sources
# ---------------------------------------------------------------------------
# One AdapterSource per EnterpriseSystem, matching that system's own
# integration_type. This stays in Python rather than its own JSON file
# because it's configuration (which mock file backs which system)
# rather than data someone would want to hand-edit.
ADAPTER_SOURCE_SEEDS = [
    {
        "system_name": "Corporate ERP",
        "source_type": "SQL Database",
        "sample_file": "erp_sql_source.json",
        "description": "Simulated SQL query results: vendor and procurement records.",
    },
    {
        "system_name": "HR Management System",
        "source_type": "REST API",
        "sample_file": "hr_rest_api_source.json",
        "description": "Simulated REST API response: employee records.",
    },
    {
        "system_name": "Finance Database",
        "source_type": "SQL Database",
        "sample_file": "finance_sql_source.json",
        "description": "Simulated SQL query results: invoice and ledger records.",
    },
    {
        "system_name": "Customer Support System",
        "source_type": "JSON",
        "sample_file": "support_json_source.json",
        "description": "Real JSON export: support ticket records.",
    },
    {
        "system_name": "Sales Database",
        "source_type": "CSV",
        "sample_file": "sales_csv_source.csv",
        "description": "Real CSV export: sales lead records.",
    },
]


def seed_adapter_sources(db: Session) -> None:
    already_seeded = db.query(models.AdapterSource).first() is not None
    if already_seeded:
        return

    for seed in ADAPTER_SOURCE_SEEDS:
        system = (
            db.query(models.EnterpriseSystem)
            .filter(models.EnterpriseSystem.name == seed["system_name"])
            .first()
        )
        if system is None:
            # If the matching system was renamed or deleted, skip it
            # rather than fail -- the adapter just won't offer that
            # source until a matching system exists again (see the
            # note on AdapterSource.system_id in models.py).
            continue
        db.add(models.AdapterSource(
            system_id=system.id,
            source_type=seed["source_type"],
            sample_file=seed["sample_file"],
            description=seed["description"],
        ))
    db.commit()


# ---------------------------------------------------------------------------
# AI Adoption -- recorded employee activities
# ---------------------------------------------------------------------------
# Real, demo-quality activities for each of the five seeded systems --
# what adoption/opportunities.py scores into Automation Opportunities.
# Deliberately specific to each system's own domain rather than a
# generic list repeated everywhere (see tests/automation/test_relevance.py
# for the automated check that guards against that). This is separate
# from tests/fixtures/activities.json, which is synthetic data used
# only by the evaluation suite -- never loaded into this database.
SYSTEM_ACTIVITY_SEEDS = [
    # Corporate ERP
    {
        "system_name": "Corporate ERP",
        "activity": "Enter purchase order details into the ERP",
        "description": "Staff retype supplier quote details into the ERP after receiving them by email or PDF.",
        "ai_opportunity": "Extract purchase order fields automatically from supplier quotes and populate the ERP, flagging anything that doesn't match a known supplier.",
        "frequency": "High", "volume": "High", "manual_effort": "High",
        "human_judgment": "Low", "data_sensitivity": "Medium", "process_standardization": "High",
    },
    {
        "system_name": "Corporate ERP",
        "activity": "Match incoming invoices to purchase orders",
        "description": "Staff compare invoice line items against the original purchase order before approving payment.",
        "ai_opportunity": "Automatically match invoice line items to purchase orders and flag mismatches for review instead of a full manual comparison.",
        "frequency": "High", "volume": "Medium", "manual_effort": "High",
        "human_judgment": "Medium", "data_sensitivity": "Medium", "process_standardization": "Medium",
    },
    {
        "system_name": "Corporate ERP",
        "activity": "Generate recurring procurement reports",
        "description": "Staff pull data from the ERP each month to compile a procurement summary for leadership.",
        "ai_opportunity": "Auto-generate the recurring procurement report directly from ERP data on a schedule instead of a manual monthly pull.",
        "frequency": "Medium", "volume": "Medium", "manual_effort": "Medium",
        "human_judgment": "Low", "data_sensitivity": "Low", "process_standardization": "High",
    },
    # HR Management System
    {
        "system_name": "HR Management System",
        "activity": "Enter new employee information into the HR system",
        "description": "HR staff transfer new-hire details from submitted documents into the HR system by hand.",
        "ai_opportunity": "Extract and validate new-hire information from submitted documents before it's entered into the HR system.",
        "frequency": "High", "volume": "High", "manual_effort": "High",
        "human_judgment": "Low", "data_sensitivity": "High", "process_standardization": "High",
    },
    {
        "system_name": "HR Management System",
        "activity": "Classify incoming HR requests",
        "description": "Staff read each incoming request -- leave, benefits, payroll questions -- and route it to the right HR team.",
        "ai_opportunity": "Automatically classify incoming HR requests and route each one to the right team.",
        "frequency": "High", "volume": "High", "manual_effort": "Medium",
        "human_judgment": "Low", "data_sensitivity": "Medium", "process_standardization": "High",
    },
    {
        "system_name": "HR Management System",
        "activity": "Generate recurring HR headcount reports",
        "description": "Staff compile a headcount and turnover report from HR system data each reporting period.",
        "ai_opportunity": "Auto-generate the recurring headcount report directly from HR system data on a schedule.",
        "frequency": "Medium", "volume": "Medium", "manual_effort": "Medium",
        "human_judgment": "Low", "data_sensitivity": "Low", "process_standardization": "High",
    },
    {
        "system_name": "HR Management System",
        "activity": "Approve employee termination",
        "description": "An HR manager reviews the circumstances and makes the final call on an employee termination.",
        "ai_opportunity": "AI can summarize the case file for the reviewing manager, but the decision itself stays a human one.",
        "frequency": "Low", "volume": "Low", "manual_effort": "Low",
        "human_judgment": "High", "data_sensitivity": "High", "process_standardization": "Medium",
    },
    # Finance Database
    {
        "system_name": "Finance Database",
        "activity": "Reconcile ledger entries against bank transactions",
        "description": "Staff compare ledger entries to bank statement lines by hand to catch discrepancies.",
        "ai_opportunity": "Automatically match ledger entries against bank transactions and surface only the discrepancies for review.",
        "frequency": "High", "volume": "High", "manual_effort": "High",
        "human_judgment": "Medium", "data_sensitivity": "High", "process_standardization": "Medium",
    },
    {
        "system_name": "Finance Database",
        "activity": "Enter invoice line items into the ledger",
        "description": "Staff retype invoice line items into the ledger from vendor invoices.",
        "ai_opportunity": "Extract invoice line items directly from vendor invoices and populate the ledger automatically.",
        "frequency": "High", "volume": "High", "manual_effort": "High",
        "human_judgment": "Low", "data_sensitivity": "Medium", "process_standardization": "High",
    },
    {
        "system_name": "Finance Database",
        "activity": "Generate recurring financial reports",
        "description": "Staff compile a recurring financial summary from ledger data each reporting period.",
        "ai_opportunity": "Auto-generate the recurring financial report directly from ledger data on a schedule.",
        "frequency": "Medium", "volume": "Medium", "manual_effort": "Medium",
        "human_judgment": "Low", "data_sensitivity": "Low", "process_standardization": "High",
    },
    # Customer Support System
    {
        "system_name": "Customer Support System",
        "activity": "Classify incoming support tickets",
        "description": "Staff read each incoming ticket and assign it a category and a team.",
        "ai_opportunity": "Automatically classify incoming tickets and route each one to the right team.",
        "frequency": "High", "volume": "High", "manual_effort": "Low",
        "human_judgment": "Low", "data_sensitivity": "Low", "process_standardization": "High",
    },
    {
        "system_name": "Customer Support System",
        "activity": "Draft responses to repetitive customer questions",
        "description": "Staff write replies to common questions that come up in support tickets over and over.",
        "ai_opportunity": "Draft a first-pass reply to common questions for an agent to review and send.",
        "frequency": "High", "volume": "Medium", "manual_effort": "Medium",
        "human_judgment": "Medium", "data_sensitivity": "Low", "process_standardization": "Medium",
    },
    {
        "system_name": "Customer Support System",
        "activity": "Summarize customer interactions for records",
        "description": "Staff write a short summary of each customer interaction for the record after it's resolved.",
        "ai_opportunity": "Auto-summarize the interaction transcript for the record, with staff reviewing before it's saved.",
        "frequency": "Medium", "volume": "Medium", "manual_effort": "Medium",
        "human_judgment": "Low", "data_sensitivity": "Medium", "process_standardization": "Medium",
    },
    # Sales Database
    {
        "system_name": "Sales Database",
        "activity": "Enter new sales leads into the pipeline",
        "description": "Staff retype lead details into the pipeline from inbound forms and event lists.",
        "ai_opportunity": "Extract lead details automatically from inbound forms and event lists and populate the pipeline.",
        "frequency": "High", "volume": "High", "manual_effort": "High",
        "human_judgment": "Low", "data_sensitivity": "Low", "process_standardization": "High",
    },
    {
        "system_name": "Sales Database",
        "activity": "Update sales opportunity status records",
        "description": "Staff update each opportunity's stage in the pipeline as deals progress.",
        "ai_opportunity": "Automatically update an opportunity's stage from linked activity (emails, calls, meetings logged) instead of a manual status change.",
        "frequency": "High", "volume": "High", "manual_effort": "Low",
        "human_judgment": "Low", "data_sensitivity": "Low", "process_standardization": "High",
    },
    {
        "system_name": "Sales Database",
        "activity": "Generate recurring sales pipeline reports",
        "description": "Staff compile a recurring pipeline summary from sales database data each reporting period.",
        "ai_opportunity": "Auto-generate the recurring pipeline report directly from sales database data on a schedule.",
        "frequency": "Medium", "volume": "Medium", "manual_effort": "Medium",
        "human_judgment": "Low", "data_sensitivity": "Low", "process_standardization": "High",
    },
]


def seed_system_activities(db: Session) -> None:
    already_seeded = db.query(models.SystemActivity).first() is not None
    if already_seeded:
        return

    for seed in SYSTEM_ACTIVITY_SEEDS:
        system = (
            db.query(models.EnterpriseSystem)
            .filter(models.EnterpriseSystem.name == seed["system_name"])
            .first()
        )
        if system is None:
            continue
        db.add(models.SystemActivity(
            system_id=system.id,
            activity=seed["activity"],
            description=seed["description"],
            ai_opportunity=seed["ai_opportunity"],
            frequency=seed["frequency"],
            volume=seed["volume"],
            manual_effort=seed["manual_effort"],
            human_judgment=seed["human_judgment"],
            data_sensitivity=seed["data_sensitivity"],
            process_standardization=seed["process_standardization"],
        ))
    db.commit()
