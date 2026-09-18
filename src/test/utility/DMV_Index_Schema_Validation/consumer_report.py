"""
DMV Index Schema Validation - Consumer-Based Report Sheets
============================================================
Purely additive reporting layer. It does NOT touch the comparison engine or
the existing 6-sheet report built by ``write_excel_report()`` in
``Schema_Validation.py``. It opens the ALREADY-WRITTEN workbook and inserts
two new sheets at the very front:

    Sheet 1 - "Run Information"     : who/what/where this run validated
    Sheet 2 - "Validation Summary"  : Total Records / Matched / Not Matched /
                                       Ignored / Execution Status

Every existing sheet (Summary, Validation Results, Claim Match Summary,
Missing Records, Schema Coverage Analysis, Stats By Element) shifts down by
two positions but is otherwise completely unchanged.

Integration point
------------------
``Schema_Validation.py`` calls :func:`inject_consumer_report_sheets` exactly
ONCE, at the very end of ``run()`` - the same place it previously called
``validation_framework.inject_report_info_sheet``.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Requirement 2: Request Type / Claim Type determination
# ─────────────────────────────────────────────────────────────────────────────

def determine_request_type(config: dict) -> str:
    """
    'Summary API' when the consumer validates the summary/list response
    (claim_filter is None); 'Detailed API' when a specific claim category
    (Hospital / Physician / Dental / Pharmacy / ...) is being validated.
    """
    claim_filter = config.get('claim_filter')
    return 'Summary API' if not claim_filter else 'Detailed API'


def determine_claim_type(config: dict) -> str:
    """
    Claim Type shown on the report header, e.g. Hospital / Physician /
    Dental / Pharmacy for detailed requests, or the configured label
    (typically 'Summary') for summary requests.
    """
    return str(config.get('claim_type') or config.get('claim_filter') or 'Summary').title()


# ─────────────────────────────────────────────────────────────────────────────
# Sheet 1: Run Information
# ─────────────────────────────────────────────────────────────────────────────

def build_run_information(consumer_name: str, config: dict, resolved_meta: Optional[dict] = None) -> List[Tuple[str, str]]:
    """Build the ordered (label, value) rows for the 'Run Information' block.

    Values are sourced from the metadata parsed off the SOURCE (PPKG) and
    TARGET (Alex) feature files and threaded through ``resolved_meta``.
    """
    resolved_meta = resolved_meta or {}
    metadata = dict(config.get('metadata') or {})
    now = datetime.now()

    consumer = (
        resolved_meta.get('consumer_label')
        or config.get('consumer_name')
        or consumer_name
    )
    request_type = resolved_meta.get('request_type') or determine_request_type(config)
    search_type = (
        resolved_meta.get('search_type')
        or config.get('search_type')
        or determine_claim_type(config)
    )

    rows = [
        ('Consumer Name',       consumer),
        ('Source URL',          resolved_meta.get('source_url') or metadata.get('source_url', '')),
        ('Target URL',          resolved_meta.get('target_url') or metadata.get('target_url', '')),
        ('Source Environment',  resolved_meta.get('source_env') or metadata.get('source_env', '')),
        ('Target Environment',  resolved_meta.get('target_env') or metadata.get('target_env', '')),
        ('Request Type',        request_type),
        ('Claim Search Type',   search_type),
        ('Execution Date',      now.strftime('%d-%b-%Y')),
        ('Execution Time',      now.strftime('%H:%M:%S')),
    ]
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Sheet 2: Validation Summary
# ─────────────────────────────────────────────────────────────────────────────

def build_validation_summary(consolidated_df: pd.DataFrame) -> List[Tuple[str, object]]:
    """Build the 'Validation Summary' metrics as ordered (label, value) rows.

    Categories (the ambiguous 'Ignored' bucket has been removed):
        Total Records      - every compared field row
        Matched            - values equal in both systems
        Mismatched         - present in BOTH systems but values differ
        Missing in Source  - present in Target (Alex) but absent in Source (PPKG)
        Missing in Target  - present in Source (PPKG) but absent in Target (Alex)

    'Mismatched' (value difference, both present) is deliberately kept separate
    from 'Missing' (record present in only one system).
    """
    if consolidated_df is None or consolidated_df.empty:
        return [
            ('Total Records',     0),
            ('Matched',           0),
            ('Mismatched',        0),
            ('Missing in Source', 0),
            ('Missing in Target', 0),
        ]

    df = consolidated_df
    status = df['Match Status'] if 'Match Status' in df.columns else pd.Series(dtype=str)

    total_records     = len(df)
    matched           = int((status == 'Match').sum())
    mismatched        = int((status == 'Mismatch').sum())
    # Source = PPKG (expected), Target = Alex (actual).
    missing_in_source = int((status == 'Value Missing in PPKG').sum())
    missing_in_target = int((status == 'Value Missing in Alex').sum())

    return [
        ('Total Records',     total_records),
        ('Matched',           matched),
        ('Mismatched',        mismatched),
        ('Missing in Source', missing_in_source),
        ('Missing in Target', missing_in_target),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Workbook injection (additive - never rewrites existing sheets)
# ─────────────────────────────────────────────────────────────────────────────

def inject_consumer_report_sheets(
    report_path: str,
    consumer_name: str,
    config: dict,
    resolved_meta: dict,
    consolidated_df: pd.DataFrame,
) -> None:
    """
    Insert ONE consolidated 'Run Information' sheet at the front of the
    already-written workbook. The sheet stacks two sections vertically:

        DMV Validation Run - Execution Information   (Run Information rows)
        Validation Summary                           (metric rows)

    Every other sheet keeps its content untouched and simply shifts one
    position to the right.
    """
    if not os.path.exists(report_path):
        return
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except Exception:
        return

    try:
        wb = load_workbook(report_path)
    except Exception:
        return

    # Remove any previously generated tabs (idempotent re-runs).
    for name in ('Run Information', 'Validation Summary'):
        if name in wb.sheetnames:
            del wb[name]

    ws = wb.create_sheet('Run Information', 0)

    title_fill   = PatternFill('solid', fgColor='1F4E79')
    section_fill = PatternFill('solid', fgColor='2E75B6')
    label_fill   = PatternFill('solid', fgColor='D9E2F3')
    thin = Side(style='thin')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def _section_title(row: int, text: str) -> None:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        cell = ws.cell(row=row, column=1, value=text)
        cell.font = Font(bold=True, size=13, color='FFFFFF')
        cell.fill = title_fill if row == 1 else section_fill
        cell.alignment = Alignment(horizontal='left', vertical='center')

    def _kv_rows(start_row: int, rows) -> int:
        r = start_row
        for label, value in rows:
            lcell = ws.cell(row=r, column=1, value=label)
            vcell = ws.cell(row=r, column=2, value=('' if value is None else str(value)))
            lcell.font = Font(bold=True)
            lcell.fill = label_fill
            lcell.border = border
            vcell.border = border
            vcell.alignment = Alignment(vertical='center', wrap_text=False)
            r += 1
        return r

    # ── Section 1: Run Information ──────────────────────────────────────────
    _section_title(1, 'DMV Validation Run - Execution Information')
    run_rows = build_run_information(consumer_name, config, resolved_meta)
    next_row = _kv_rows(3, run_rows)

    # ── Section 2: Validation Summary (directly below, same sheet) ──────────
    summary_title_row = next_row + 1
    _section_title(summary_title_row, 'Validation Summary')
    summary_rows = build_validation_summary(consolidated_df)
    _kv_rows(summary_title_row + 2, summary_rows)

    ws.column_dimensions['A'].width = 24
    ws.column_dimensions['B'].width = 90

    try:
        wb.save(report_path)
    except Exception:
        pass

