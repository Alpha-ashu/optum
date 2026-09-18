"""
Consolidate Consumer Validation Reports
========================================
Reads:  target/All_Responses/<CONSUMER>/ConsolidateReports/*_report.xlsx
Writes: target/All_Responses/ALL_COSMOS_CONSUMER_PROD_API_CONSOLIDATE_REPORT.xlsx
        target/All_Responses/ALL_COSMOS_CONSUMER_PROD_API_PERFORMANCE_REPORT.xlsx
"""

import os
import sys
import shutil
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# Resolve project root
project_root = Path(__file__).resolve().parents[4]
all_responses_dir = project_root / "target" / "All_Responses"

# Styling
HDR_FONT = Font(bold=True, color="FFFFFF", size=11)
HDR_FILL = PatternFill("solid", fgColor="2F5496")
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
SUB_FONT = Font(bold=True, size=11, color="2F5496")
GREEN = PatternFill("solid", fgColor="C6EFCE")
YELLOW = PatternFill("solid", fgColor="FFEB9C")
RED = PatternFill("solid", fgColor="FFC7CE")
THIN = Border(*(Side("thin"),) * 4)

CONSUMERS = ["ACET", "IIM", "ISET", "MEDICA", "MYUHC", "OHBSPE", "PTRCR", "VETSS"]
VAR_TYPES = ["Summary", "Hospital", "Physician"]


def style_header(ws, row=1):
    for cell in ws[row]:
        cell.font = HDR_FONT
        cell.fill = HDR_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = THIN


def auto_width(ws):
    for col in ws.columns:
        mx = max((len(str(c.value or "")) for c in col), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(mx + 3, 55)


def write_df(ws, df, start_row=1):
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    style_header(ws, start_row)
    auto_width(ws)


# Collect all existing report files from consumer-specific folders
master_data = []

for consumer in CONSUMERS:
    consumer_reports_dir = all_responses_dir / consumer / "ConsolidateReports"
    
    if not consumer_reports_dir.exists():
        print(f"[CONSOLIDATE] Skipping {consumer} - ConsolidateReports directory not found")
        continue

    all_reports = list(consumer_reports_dir.glob("*_report.xlsx"))
    print(f"[CONSOLIDATE] Found {len(all_reports)} report files for {consumer}")

    for var_type in VAR_TYPES:
        var_name = f"{consumer}_{var_type}"
        report_file = consumer_reports_dir / f"{var_name}_report.xlsx"

        if not report_file.exists():
            print(f"[CONSOLIDATE] Skipping {var_name} - report not found")
            continue

        # Read data for master summary
        try:
            xls = pd.ExcelFile(str(report_file), engine="openpyxl")
            if "Final Consolidated Data" in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name="Final Consolidated Data")
                df["Consumer"] = consumer
                df["Type"] = var_type
                master_data.append(df)
        except Exception as e:
            print(f"[CONSOLIDATE] Error reading {report_file.name}: {e}")

# Create master consolidated report across all consumers
if master_data:
    try:
        all_df = pd.concat(master_data, ignore_index=True)
        wb = Workbook()
        wb.remove(wb.active)

        # Summary sheet
        ws = wb.create_sheet("All Consumers Summary")
        ws.cell(1, 1, value="All Consumers Validation Summary").font = TITLE_FONT

        summary_rows = []
        for consumer in CONSUMERS:
            for var_type in VAR_TYPES:
                subset = all_df[(all_df["Consumer"] == consumer) & (all_df["Type"] == var_type)]
                if subset.empty:
                    continue
                total = len(subset)
                matched = (subset.get("Match Status", pd.Series()) == "Matched").sum() if "Match Status" in subset.columns else 0
                partial = (subset.get("Match Status", pd.Series()) == "Partially Matched").sum() if "Match Status" in subset.columns else 0
                not_matched = (subset.get("Match Status", pd.Series()) == "Not Matched").sum() if "Match Status" in subset.columns else 0
                pct = round((matched + partial) / total * 100, 2) if total > 0 else 0
                summary_rows.append({
                    "Consumer": consumer,
                    "Type": var_type,
                    "Total Fields": total,
                    "Matched": int(matched),
                    "Partially Matched": int(partial),
                    "Not Matched": int(not_matched),
                    "Match Rate %": pct,
                })

        if summary_rows:
            summary_df = pd.DataFrame(summary_rows)
            for r_idx, r in enumerate(dataframe_to_rows(summary_df, index=False, header=True)):
                for c_idx, val in enumerate(r, start=1):
                    ws.cell(3 + r_idx, c_idx, value=val)
            style_header(ws, 3)

            # Color match rate
            for row in ws.iter_rows(min_row=4, max_row=3 + len(summary_rows)):
                c = row[6]  # Match Rate % column (0-indexed)
                try:
                    v = float(c.value)
                    c.fill = GREEN if v >= 90 else (YELLOW if v >= 70 else RED)
                except (TypeError, ValueError):
                    pass

        auto_width(ws)

        # Raw data sheet
        ws_raw = wb.create_sheet("All Data")
        write_df(ws_raw, all_df)

        # Per-consumer detail sheets
        for consumer in CONSUMERS:
            consumer_subset = all_df[all_df["Consumer"] == consumer]
            if not consumer_subset.empty:
                ws_consumer = wb.create_sheet(f"{consumer}")
                write_df(ws_consumer, consumer_subset)

        master_path = all_responses_dir / "ALL_COSMOS_CONSUMER_PROD_API_CONSOLIDATE_REPORT.xlsx"
        os.makedirs(str(all_responses_dir), exist_ok=True)
        wb.save(str(master_path))
        print(f"[CONSOLIDATE] Master consolidated report -> {master_path}")
    except Exception as e:
        print(f"[CONSOLIDATE] Error creating master summary: {e}")
else:
    print("[CONSOLIDATE] No validation data found to consolidate")

print("[CONSOLIDATE] Done!")
