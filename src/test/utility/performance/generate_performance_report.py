"""
Comprehensive Performance Report Generator
============================================
Reads  : All_Responses/Performance/performance_log.csv
Writes : All_Responses/Performance/Performance_Report.xlsx

Sheets:
  0. Dashboard Summary
  1. Response Time Analysis
  2. Throughput Analysis
  3. Error Rate Analysis
  4. Resource Utilization (template)
  5. Scalability Analysis
  6. Stability (Soak) Analysis
  7. Correctness Under Load
  8. Concurrency Handling
  9. SLA-SLO Compliance
 10. Security Performance

Usage:
  python src/test/utility/performance/generate_performance_report.py
  python src/test/utility/performance/generate_performance_report.py --csv path/to/csv --output path/to/xlsx
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# ═══════════════════════════════════════════════════════════════════════════
# Configuration / Thresholds
# ═══════════════════════════════════════════════════════════════════════════
SLA_THRESHOLDS = {
    "response_time_p95_ms": 500,
    "response_time_p99_ms": 1000,
    "response_time_max_ms": 3000,
    "error_rate_pct": 1.0,
    "min_throughput_rps": 5,
}

RESPONSE_TIME_BANDS = {
    "fast": 200,      # ms - green
    "normal": 500,    # ms - yellow
    "slow": 2000,     # ms - orange  (>= slow is red)
}

AUTH_ENDPOINT_PATTERNS = ["token", "auth", "login", "oauth", "AccessToken"]

# ═══════════════════════════════════════════════════════════════════════════
# Styles
# ═══════════════════════════════════════════════════════════════════════════
HDR_FONT   = Font(bold=True, color="FFFFFF", size=11)
HDR_FILL   = PatternFill("solid", fgColor="2F5496")
TITLE_FONT = Font(bold=True, size=14, color="1F3864")
SUB_FONT   = Font(bold=True, size=11, color="2F5496")
GREEN      = PatternFill("solid", fgColor="C6EFCE")
YELLOW     = PatternFill("solid", fgColor="FFEB9C")
ORANGE     = PatternFill("solid", fgColor="F4B084")
RED        = PatternFill("solid", fgColor="FFC7CE")
LIGHT_BLUE = PatternFill("solid", fgColor="D6E4F0")
THIN       = Border(*(Side("thin"),) * 4)


def _style_header(ws, row=1):
    for cell in ws[row]:
        cell.font, cell.fill, cell.alignment, cell.border = (
            HDR_FONT, HDR_FILL, Alignment(horizontal="center", wrap_text=True), THIN,
        )


def _auto_width(ws):
    for col in ws.columns:
        mx = max((len(str(c.value or "")) for c in col), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(mx + 3, 55)


def _color_rt(cell, val):
    try:
        v = float(val)
    except (TypeError, ValueError):
        return
    if v < RESPONSE_TIME_BANDS["fast"]:
        cell.fill = GREEN
    elif v < RESPONSE_TIME_BANDS["normal"]:
        cell.fill = YELLOW
    elif v < RESPONSE_TIME_BANDS["slow"]:
        cell.fill = ORANGE
    else:
        cell.fill = RED


def _color_pct(cell, val, good_below=1.0):
    try:
        v = float(val)
    except (TypeError, ValueError):
        return
    cell.fill = GREEN if v < good_below else (YELLOW if v < good_below * 5 else RED)


def _write_df(ws, df, start_row=1):
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    _style_header(ws, start_row)
    _auto_width(ws)


def _add_title(ws, title, row=1, col=1):
    c = ws.cell(row=row, column=col, value=title)
    c.font = TITLE_FONT


# ═══════════════════════════════════════════════════════════════════════════
# Report Generator
# ═══════════════════════════════════════════════════════════════════════════
class PerfReport:
    def __init__(self, csv_path, output_path):
        self.csv_path = csv_path
        self.output_path = output_path
        self.df = pd.read_csv(csv_path)
        self._clean()
        self.wb = Workbook()
        self.wb.remove(self.wb.active)

    def _clean(self):
        df = self.df
        df.columns = [c.strip() for c in df.columns]
        if "consumer" not in df.columns:
            df["consumer"] = "unknown"
        df["consumer"] = df["consumer"].fillna("unknown").astype(str).str.strip()
        df["response_time_ms"] = pd.to_numeric(df["response_time_ms"], errors="coerce").fillna(0)
        df["status"] = pd.to_numeric(df["status"], errors="coerce").fillna(0).astype(int)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["status_class"] = df["status"].apply(
            lambda s: "2xx" if 200 <= s < 300 else ("4xx" if 400 <= s < 500 else ("5xx" if s >= 500 else "other"))
        )
        df["is_error"] = df["status_class"].isin(["4xx", "5xx"])
        self.df = df.sort_values("timestamp").reset_index(drop=True)

    # -- 0. Dashboard --
    def _sheet_dashboard(self):
        ws = self.wb.create_sheet("Dashboard", 0)
        df = self.df
        _add_title(ws, "Performance Test Dashboard", 1, 1)
        ws.cell(2, 1, value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").font = SUB_FONT

        metrics = [
            ("Total Requests", len(df)),
            ("Unique Consumers", df["consumer"].nunique()),
            ("Consumers Validated", ", ".join(sorted(df["consumer"].unique()))),
            ("Unique Features", df["feature"].nunique()),
            ("Unique Endpoints", df["endpoint"].nunique()),
            ("", ""),
            ("Avg Response Time (ms)", round(df["response_time_ms"].mean(), 1)),
            ("P90 Response Time (ms)", round(df["response_time_ms"].quantile(0.90), 1)),
            ("P95 Response Time (ms)", round(df["response_time_ms"].quantile(0.95), 1)),
            ("P99 Response Time (ms)", round(df["response_time_ms"].quantile(0.99), 1)),
            ("Max Response Time (ms)", round(df["response_time_ms"].max(), 1)),
            ("", ""),
            ("2xx Success Count", int((df["status_class"] == "2xx").sum())),
            ("4xx Client Errors", int((df["status_class"] == "4xx").sum())),
            ("5xx Server Errors", int((df["status_class"] == "5xx").sum())),
            ("Error Rate %", round(df["is_error"].mean() * 100, 2)),
            ("", ""),
            ("SLA P95 Threshold (ms)", SLA_THRESHOLDS["response_time_p95_ms"]),
            ("SLA P95 Compliant?", "YES" if df["response_time_ms"].quantile(0.95) <= SLA_THRESHOLDS["response_time_p95_ms"] else "NO"),
            ("SLA Error Rate Threshold %", SLA_THRESHOLDS["error_rate_pct"]),
            ("SLA Error Compliant?", "YES" if df["is_error"].mean() * 100 <= SLA_THRESHOLDS["error_rate_pct"] else "NO"),
        ]
        for i, (label, val) in enumerate(metrics, start=4):
            ws.cell(i, 1, value=label).font = SUB_FONT if label else Font()
            c = ws.cell(i, 2, value=val)
            if "Response Time" in label and isinstance(val, (int, float)):
                _color_rt(c, val)
            if label == "Error Rate %":
                _color_pct(c, val)
            if "Compliant?" in label:
                c.fill = GREEN if val == "YES" else RED
                c.font = Font(bold=True)

        row_start = len(metrics) + 6
        ws.cell(row_start, 1, value="Top 5 Slowest Features").font = SUB_FONT
        top5 = df.groupby("feature")["response_time_ms"].mean().nlargest(5).reset_index()
        top5.columns = ["Feature", "Avg Response Time (ms)"]
        top5["Avg Response Time (ms)"] = top5["Avg Response Time (ms)"].round(1)
        for j, r in enumerate(dataframe_to_rows(top5, index=False, header=True)):
            for k, val in enumerate(r, start=1):
                ws.cell(row_start + 1 + j, k, value=val)
        _style_header(ws, row_start + 1)
        ws.column_dimensions["A"].width = 35
        ws.column_dimensions["B"].width = 25

    # -- 1. Response Time --
    def _sheet_response_time(self):
        ws = self.wb.create_sheet("1. Response Time")
        df = self.df
        grp = df.groupby(["consumer", "feature"])["response_time_ms"]
        summary = grp.agg(Count="count", Avg="mean", Min="min", Max="max", Median="median").reset_index()
        summary["P90"] = grp.quantile(0.90).values
        summary["P95"] = grp.quantile(0.95).values
        summary["P99"] = grp.quantile(0.99).values
        for c in ["Avg", "Min", "Max", "Median", "P90", "P95", "P99"]:
            summary[c] = summary[c].round(1)
        summary.columns = ["Consumer", "Feature", "Count", "Avg (ms)", "Min (ms)", "Max (ms)", "Median (ms)", "P90 (ms)", "P95 (ms)", "P99 (ms)"]
        _write_df(ws, summary)
        for row in ws.iter_rows(min_row=2, max_row=len(summary) + 1):
            for ci in [2, 4, 5, 6, 7, 8]:
                _color_rt(row[ci], row[ci].value)
        if len(summary) > 0:
            chart = BarChart()
            chart.title = "Response Time by Feature"
            chart.y_axis.title = "Milliseconds"
            chart.style = 10
            chart.width, chart.height = 28, 14
            for col_idx in [3, 7, 8, 9]:
                data = Reference(ws, min_col=col_idx, min_row=1, max_row=len(summary) + 1)
                chart.add_data(data, titles_from_data=True)
            cats = Reference(ws, min_col=1, min_row=2, max_row=len(summary) + 1)
            chart.set_categories(cats)
            ws.add_chart(chart, "K2")

    # -- 2. Throughput --
    def _sheet_throughput(self):
        ws = self.wb.create_sheet("2. Throughput")
        df = self.df.copy()
        if df["timestamp"].isna().all():
            ws.append(["No valid timestamps - throughput cannot be calculated."])
            return
        df = df.dropna(subset=["timestamp"])
        df["second"] = df["timestamp"].dt.floor("s")
        rps = df.groupby("second").size().reset_index(name="RPS")
        stats = pd.DataFrame({
            "Metric": ["Avg RPS", "Max RPS", "Min RPS", "P95 RPS", "Total Duration (s)", "Total Requests"],
            "Value": [round(rps["RPS"].mean(), 2), int(rps["RPS"].max()), int(rps["RPS"].min()),
                      round(rps["RPS"].quantile(0.95), 2), len(rps), len(df)],
        })
        _write_df(ws, stats)
        ws2_start = len(stats) + 4
        ws.cell(ws2_start, 1, value="Requests Per Second Over Time").font = SUB_FONT
        rps_display = rps.copy()
        rps_display["second"] = rps_display["second"].dt.strftime("%H:%M:%S")
        for j, r in enumerate(dataframe_to_rows(rps_display, index=False, header=True)):
            for k, val in enumerate(r, start=1):
                ws.cell(ws2_start + 1 + j, k, value=val)
        _style_header(ws, ws2_start + 1)
        if len(rps) > 1:
            chart = LineChart()
            chart.title = "Throughput (RPS) Over Time"
            chart.y_axis.title = "Requests/sec"
            chart.style = 10
            chart.width, chart.height = 28, 14
            data = Reference(ws, min_col=2, min_row=ws2_start + 1, max_row=ws2_start + 1 + len(rps))
            cats = Reference(ws, min_col=1, min_row=ws2_start + 2, max_row=ws2_start + 1 + len(rps))
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            ws.add_chart(chart, "D2")
        _auto_width(ws)

    # -- 3. Error Rate --
    def _sheet_error_rate(self):
        ws = self.wb.create_sheet("3. Error Rate")
        df = self.df
        grp = df.groupby("feature")
        err = grp.agg(Total=("status", "count"), Errors=("is_error", "sum")).reset_index()
        err["Success"] = err["Total"] - err["Errors"]
        err["Error Rate %"] = (err["Errors"] / err["Total"] * 100).round(2)
        err["2xx"] = grp.apply(lambda x: (x["status_class"] == "2xx").sum(), include_groups=False).values
        err["4xx"] = grp.apply(lambda x: (x["status_class"] == "4xx").sum(), include_groups=False).values
        err["5xx"] = grp.apply(lambda x: (x["status_class"] == "5xx").sum(), include_groups=False).values
        err = err[["feature", "Total", "Success", "Errors", "Error Rate %", "2xx", "4xx", "5xx"]]
        err.columns = ["Feature", "Total", "Success", "Errors", "Error Rate %", "2xx", "4xx", "5xx"]
        _write_df(ws, err)
        for row in ws.iter_rows(min_row=2, max_row=len(err) + 1):
            _color_pct(row[4], row[4].value)
        status_counts = df["status_class"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        pie_start = len(err) + 4
        ws.cell(pie_start, 1, value="Overall Status Distribution").font = SUB_FONT
        for j, r in enumerate(dataframe_to_rows(status_counts, index=False, header=True)):
            for k, val in enumerate(r, start=1):
                ws.cell(pie_start + 1 + j, k, value=val)
        if len(status_counts) > 0:
            chart = PieChart()
            chart.title = "Status Code Distribution"
            chart.style = 10
            data = Reference(ws, min_col=2, min_row=pie_start + 1, max_row=pie_start + 1 + len(status_counts))
            cats = Reference(ws, min_col=1, min_row=pie_start + 2, max_row=pie_start + 1 + len(status_counts))
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            chart.dataLabels = DataLabelList()
            chart.dataLabels.showPercent = True
            chart.width, chart.height = 16, 12
            ws.add_chart(chart, "J2")
        _auto_width(ws)

    # -- 4. Resource Utilization (Template) --
    def _sheet_resource_util(self):
        ws = self.wb.create_sheet("4. Resource Utilization")
        _add_title(ws, "Resource Utilization", 1, 1)
        ws.cell(3, 1, value="Note: Karate captures API-level metrics only.").font = SUB_FONT
        ws.cell(4, 1, value="System metrics require external monitoring (Prometheus, Grafana, CloudWatch, etc.)")
        ws.cell(6, 1, value="Paste or import system metrics below:").font = SUB_FONT
        headers = ["Timestamp", "CPU %", "Memory %", "Disk I/O (MB/s)", "Network (MB/s)", "DB Connections", "Thread Pool Active", "Notes"]
        for i, h in enumerate(headers, start=1):
            c = ws.cell(8, i, value=h)
            c.font, c.fill, c.border = HDR_FONT, HDR_FILL, THIN
        ws.cell(10, 1, value="Recommended Thresholds:").font = SUB_FONT
        for i, (m, g) in enumerate([
            ("CPU %", "< 70% normal, 70-85% warning, > 85% critical"),
            ("Memory %", "< 75% normal, 75-90% warning, > 90% critical"),
            ("DB Connections", "< 80% pool capacity"),
        ], start=11):
            ws.cell(i, 1, value=m).font = Font(bold=True)
            ws.cell(i, 2, value=g)
        _auto_width(ws)

    # -- 5. Scalability --
    def _sheet_scalability(self):
        ws = self.wb.create_sheet("5. Scalability")
        df = self.df.copy()
        if df["timestamp"].isna().all():
            ws.append(["No valid timestamps - scalability analysis unavailable."])
            return
        df = df.dropna(subset=["timestamp"])
        df["second"] = df["timestamp"].dt.floor("s")
        concurrency = df.groupby("second").agg(
            concurrent_requests=("status", "count"), avg_response_time=("response_time_ms", "mean"),
        ).reset_index()
        concurrency["avg_response_time"] = concurrency["avg_response_time"].round(1)
        concurrency["concurrency_bucket"] = pd.cut(
            concurrency["concurrent_requests"], bins=[0, 1, 5, 10, 20, 50, 100, 1000],
            labels=["1", "2-5", "6-10", "11-20", "21-50", "51-100", "100+"],
        )
        scale = concurrency.groupby("concurrency_bucket", observed=True).agg(
            windows=("concurrent_requests", "count"), avg_rt=("avg_response_time", "mean"), max_rt=("avg_response_time", "max"),
        ).reset_index()
        scale.columns = ["Concurrency Level", "Time Windows", "Avg RT (ms)", "Max RT (ms)"]
        scale["Avg RT (ms)"] = scale["Avg RT (ms)"].round(1)
        scale["Max RT (ms)"] = scale["Max RT (ms)"].round(1)
        _write_df(ws, scale)
        if len(scale) > 1:
            chart = BarChart()
            chart.title = "Response Time vs Concurrency Level"
            chart.y_axis.title = "Avg Response Time (ms)"
            chart.style = 10
            chart.width, chart.height = 24, 14
            data = Reference(ws, min_col=3, min_row=1, max_row=len(scale) + 1)
            cats = Reference(ws, min_col=1, min_row=2, max_row=len(scale) + 1)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            ws.add_chart(chart, "F2")
        _auto_width(ws)

    # -- 6. Stability (Soak) --
    def _sheet_stability(self):
        ws = self.wb.create_sheet("6. Stability (Soak)")
        df = self.df.copy()
        if df["timestamp"].isna().all():
            ws.append(["No valid timestamps - stability analysis unavailable."])
            return
        df = df.dropna(subset=["timestamp"])
        duration = (df["timestamp"].max() - df["timestamp"].min()).total_seconds()
        n_windows = min(20, max(3, int(duration / 60)))
        df["window"] = pd.cut(df.index, bins=n_windows, labels=False)
        soak = df.groupby("window").agg(
            start_time=("timestamp", "min"), count=("status", "count"),
            avg_rt=("response_time_ms", "mean"),
            p95_rt=("response_time_ms", lambda x: x.quantile(0.95)),
            error_pct=("is_error", lambda x: round(x.mean() * 100, 2)),
        ).reset_index()
        soak["start_time"] = soak["start_time"].dt.strftime("%H:%M:%S")
        soak["avg_rt"] = soak["avg_rt"].round(1)
        soak["p95_rt"] = soak["p95_rt"].round(1)
        baseline_avg = soak["avg_rt"].iloc[0] if len(soak) > 0 else 0
        soak["degradation_%"] = ((soak["avg_rt"] - baseline_avg) / max(baseline_avg, 1) * 100).round(1)
        soak.columns = ["Window", "Start Time", "Requests", "Avg RT (ms)", "P95 RT (ms)", "Error %", "Degradation %"]
        _write_df(ws, soak)
        for row in ws.iter_rows(min_row=2, max_row=len(soak) + 1):
            try:
                v = float(row[6].value)
                row[6].fill = GREEN if v < 10 else (YELLOW if v < 20 else RED)
            except (TypeError, ValueError):
                pass
        if len(soak) > 2:
            chart = LineChart()
            chart.title = "Response Time Stability Over Test Duration"
            chart.y_axis.title = "ms"
            chart.style = 10
            chart.width, chart.height = 28, 14
            for ci in [4, 5]:
                data = Reference(ws, min_col=ci, min_row=1, max_row=len(soak) + 1)
                chart.add_data(data, titles_from_data=True)
            cats = Reference(ws, min_col=2, min_row=2, max_row=len(soak) + 1)
            chart.set_categories(cats)
            ws.add_chart(chart, "I2")
        _auto_width(ws)

    # -- 7. Correctness Under Load --
    def _sheet_correctness(self):
        ws = self.wb.create_sheet("7. Correctness Under Load")
        df = self.df
        pivot = df.pivot_table(index="feature", columns="status_class", values="status", aggfunc="count", fill_value=0).reset_index()
        pivot.columns.name = None
        _write_df(ws, pivot)
        flag_start = len(pivot) + 4
        ws.cell(flag_start, 1, value="Consistency Flags").font = SUB_FONT
        ws.cell(flag_start + 1, 1, value="Feature").font = HDR_FONT
        ws.cell(flag_start + 1, 1).fill = HDR_FILL
        ws.cell(flag_start + 1, 2, value="Issue").font = HDR_FONT
        ws.cell(flag_start + 1, 2).fill = HDR_FILL
        r = flag_start + 2
        for _, row_data in pivot.iterrows():
            has_2xx = row_data.get("2xx", 0) > 0
            has_err = row_data.get("4xx", 0) > 0 or row_data.get("5xx", 0) > 0
            if has_2xx and has_err:
                ws.cell(r, 1, value=row_data["feature"])
                ws.cell(r, 2, value="Mixed success + error responses under load").fill = YELLOW
                r += 1
        if r == flag_start + 2:
            ws.cell(r, 1, value="No inconsistencies detected").fill = GREEN
        _auto_width(ws)

    # -- 8. Concurrency Handling --
    def _sheet_concurrency(self):
        ws = self.wb.create_sheet("8. Concurrency Handling")
        df = self.df.copy()
        if df["timestamp"].isna().all():
            ws.append(["No valid timestamps - concurrency analysis unavailable."])
            return
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        overlap_counts = []
        ts_arr = df["timestamp"].values
        window = pd.Timedelta(milliseconds=100)
        for i in range(len(df)):
            nearby = ((ts_arr >= ts_arr[i] - window) & (ts_arr <= ts_arr[i] + window)).sum()
            overlap_counts.append(nearby)
        df["concurrent_overlap"] = overlap_counts
        summary = pd.DataFrame({
            "Metric": ["Max Concurrent Overlap (100ms window)", "Avg Concurrent Overlap",
                       "Requests with overlap > 1", "Avg RT when overlap > 5", "Avg RT when overlap = 1"],
            "Value": [
                int(df["concurrent_overlap"].max()), round(df["concurrent_overlap"].mean(), 1),
                int((df["concurrent_overlap"] > 1).sum()),
                round(df.loc[df["concurrent_overlap"] > 5, "response_time_ms"].mean(), 1) if (df["concurrent_overlap"] > 5).any() else "N/A",
                round(df.loc[df["concurrent_overlap"] == 1, "response_time_ms"].mean(), 1) if (df["concurrent_overlap"] == 1).any() else "N/A",
            ],
        })
        _write_df(ws, summary)
        dist_start = len(summary) + 4
        ws.cell(dist_start, 1, value="Overlap Distribution").font = SUB_FONT
        dist = df["concurrent_overlap"].value_counts().sort_index().reset_index()
        dist.columns = ["Concurrent Requests", "Occurrences"]
        for j, r in enumerate(dataframe_to_rows(dist, index=False, header=True)):
            for k, val in enumerate(r, start=1):
                ws.cell(dist_start + 1 + j, k, value=val)
        _style_header(ws, dist_start + 1)
        _auto_width(ws)

    # -- 9. SLA / SLO Compliance --
    def _sheet_sla(self):
        ws = self.wb.create_sheet("9. SLA-SLO Compliance")
        df = self.df
        grp = df.groupby("feature")
        sla = grp.agg(
            count=("status", "count"),
            p95=("response_time_ms", lambda x: x.quantile(0.95)),
            p99=("response_time_ms", lambda x: x.quantile(0.99)),
            max_rt=("response_time_ms", "max"),
            error_pct=("is_error", lambda x: round(x.mean() * 100, 2)),
        ).reset_index()
        sla["p95"] = sla["p95"].round(1)
        sla["p99"] = sla["p99"].round(1)
        sla["max_rt"] = sla["max_rt"].round(1)
        sla["P95 SLA"] = sla["p95"].apply(lambda v: "PASS" if v <= SLA_THRESHOLDS["response_time_p95_ms"] else "FAIL")
        sla["P99 SLA"] = sla["p99"].apply(lambda v: "PASS" if v <= SLA_THRESHOLDS["response_time_p99_ms"] else "FAIL")
        sla["Error SLA"] = sla["error_pct"].apply(lambda v: "PASS" if v <= SLA_THRESHOLDS["error_rate_pct"] else "FAIL")
        sla.columns = ["Feature", "Count", "P95 (ms)", "P99 (ms)", "Max (ms)", "Error %", "P95 SLA", "P99 SLA", "Error SLA"]
        _write_df(ws, sla)
        for row in ws.iter_rows(min_row=2, max_row=len(sla) + 1):
            for ci in [6, 7, 8]:
                row[ci].fill = GREEN if row[ci].value == "PASS" else RED
                row[ci].font = Font(bold=True)
        ref_start = len(sla) + 4
        ws.cell(ref_start, 1, value="SLA Thresholds Applied").font = SUB_FONT
        for i, (k, v) in enumerate(SLA_THRESHOLDS.items(), start=ref_start + 1):
            ws.cell(i, 1, value=k)
            ws.cell(i, 2, value=v)
        _auto_width(ws)

    # -- 10. Security Performance --
    def _sheet_security(self):
        ws = self.wb.create_sheet("10. Security Performance")
        df = self.df
        pattern = "|".join(AUTH_ENDPOINT_PATTERNS)
        auth_df = df[df["scenario"].str.contains(pattern, case=False, na=False) |
                      df["endpoint"].str.contains(pattern, case=False, na=False)]
        if auth_df.empty:
            ws.cell(1, 1, value="No auth/token endpoints detected in test data.").font = SUB_FONT
            ws.cell(3, 1, value="Patterns searched:").font = Font(italic=True)
            ws.cell(3, 2, value=pattern)
            _auto_width(ws)
            return
        stats = pd.DataFrame({
            "Metric": ["Auth Requests", "Avg Latency (ms)", "P95 Latency (ms)", "Max Latency (ms)", "Error Rate %"],
            "Value": [len(auth_df), round(auth_df["response_time_ms"].mean(), 1),
                      round(auth_df["response_time_ms"].quantile(0.95), 1),
                      round(auth_df["response_time_ms"].max(), 1),
                      round(auth_df["is_error"].mean() * 100, 2)],
        })
        _write_df(ws, stats)
        rate_limited = df[df["status"] == 429]
        rl_start = len(stats) + 4
        ws.cell(rl_start, 1, value="Rate Limiting (HTTP 429)").font = SUB_FONT
        ws.cell(rl_start + 1, 1, value="429 Responses Detected")
        ws.cell(rl_start + 1, 2, value=len(rate_limited))
        if len(rate_limited) > 0:
            ws.cell(rl_start + 2, 1, value="Endpoints Affected")
            ws.cell(rl_start + 2, 2, value=", ".join(rate_limited["endpoint"].unique()[:5]))
        _auto_width(ws)

    # -- Consumer Breakdown --
    def _sheet_consumer_breakdown(self):
        ws = self.wb.create_sheet("Consumer Breakdown")
        df = self.df
        _add_title(ws, "Performance by Consumer", 1, 1)

        grp = df.groupby("consumer")
        summary = grp.agg(
            Total_Requests=("response_time_ms", "count"),
            Avg_RT_ms=("response_time_ms", "mean"),
            P95_RT_ms=("response_time_ms", lambda x: x.quantile(0.95)),
            P99_RT_ms=("response_time_ms", lambda x: x.quantile(0.99)),
            Max_RT_ms=("response_time_ms", "max"),
            Min_RT_ms=("response_time_ms", "min"),
            Success_2xx=("status_class", lambda x: (x == "2xx").sum()),
            Client_Errors_4xx=("status_class", lambda x: (x == "4xx").sum()),
            Server_Errors_5xx=("status_class", lambda x: (x == "5xx").sum()),
            Error_Rate_Pct=("is_error", lambda x: round(x.mean() * 100, 2)),
        ).reset_index()
        summary.columns = [
            "Consumer", "Total Requests", "Avg RT (ms)", "P95 RT (ms)", "P99 RT (ms)",
            "Max RT (ms)", "Min RT (ms)", "2xx Success", "4xx Errors", "5xx Errors", "Error Rate %"
        ]
        for c in ["Avg RT (ms)", "P95 RT (ms)", "P99 RT (ms)", "Max RT (ms)", "Min RT (ms)"]:
            summary[c] = summary[c].round(1)

        for r_idx, r in enumerate(dataframe_to_rows(summary, index=False, header=True)):
            for c_idx, val in enumerate(r, start=1):
                ws.cell(3 + r_idx, c_idx, value=val)
        _style_header(ws, 3)
        _auto_width(ws)

        # Color code response times
        for row in ws.iter_rows(min_row=4, max_row=3 + len(summary)):
            for ci in [2, 3, 4, 5]:  # Avg, P95, P99, Max columns (0-indexed from col 1)
                _color_rt(row[ci], row[ci].value)
            _color_pct(row[10], row[10].value)  # Error Rate %

        # Per-consumer feature breakdown
        detail_start = 3 + len(summary) + 3
        ws.cell(detail_start, 1, value="Detailed: Consumer × Feature Breakdown").font = SUB_FONT
        detail = df.groupby(["consumer", "feature"]).agg(
            Count=("response_time_ms", "count"),
            Avg_RT=("response_time_ms", "mean"),
            P95_RT=("response_time_ms", lambda x: x.quantile(0.95)),
            Error_Rate=("is_error", lambda x: round(x.mean() * 100, 2)),
        ).reset_index()
        detail.columns = ["Consumer", "Feature", "Count", "Avg RT (ms)", "P95 RT (ms)", "Error Rate %"]
        detail["Avg RT (ms)"] = detail["Avg RT (ms)"].round(1)
        detail["P95 RT (ms)"] = detail["P95 RT (ms)"].round(1)
        for r_idx, r in enumerate(dataframe_to_rows(detail, index=False, header=True)):
            for c_idx, val in enumerate(r, start=1):
                ws.cell(detail_start + 1 + r_idx, c_idx, value=val)
        _style_header(ws, detail_start + 1)
        _auto_width(ws)

    # -- Generate --
    def generate(self):
        print(f"[PERF] Loading {len(self.df)} rows from {self.csv_path}")
        self._sheet_dashboard()
        self._sheet_consumer_breakdown()
        self._sheet_response_time()
        self._sheet_throughput()
        self._sheet_error_rate()
        self._sheet_resource_util()
        self._sheet_scalability()
        self._sheet_stability()
        self._sheet_correctness()
        self._sheet_concurrency()
        self._sheet_sla()
        self._sheet_security()
        os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)
        # Try saving; if file is locked (open in Excel), save with timestamp suffix
        try:
            self.wb.save(self.output_path)
        except PermissionError:
            base, ext = os.path.splitext(self.output_path)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = f"{base}_{ts}{ext}"
            self.wb.save(fallback)
            print(f"[PERF] Original file locked, saved to -> {fallback}")
            self.output_path = fallback
        print(f"[PERF] Report saved -> {self.output_path}")
        print(f"[PERF]   Sheets: {len(self.wb.sheetnames)}")
        print(f"[PERF]   Total requests: {len(self.df)}")
        print(f"[PERF]   Avg RT: {self.df['response_time_ms'].mean():.1f} ms")
        print(f"[PERF]   P95 RT: {self.df['response_time_ms'].quantile(0.95):.1f} ms")
        print(f"[PERF]   Error rate: {self.df['is_error'].mean() * 100:.2f}%")


def main():
    project_root = Path(__file__).resolve().parents[4]
    default_csv = str(project_root / "target" / "Performance" / "performance_log.csv")
    # Fallback to legacy path
    if not os.path.exists(default_csv):
        default_csv = str(project_root / "All_Responses" / "Performance" / "performance_log.csv")
    default_out = str(Path(default_csv).parent / "Performance_Report.xlsx")
    parser = argparse.ArgumentParser(description="Generate Performance Test Excel Report")
    parser.add_argument("--csv", default=default_csv, help="Path to performance_log.csv")
    parser.add_argument("--output", default=default_out, help="Output .xlsx path")
    parser.add_argument("--feature-filter", default=None, help="Comma-separated feature names to filter (e.g. upm_hospital,ppkg_hospital)")
    parser.add_argument("--consumer-filter", default=None, help="Comma-separated consumer names to filter (e.g. ACET,IIM)")
    args = parser.parse_args()
    if not os.path.exists(args.csv):
        print(f"[PERF] CSV not found: {args.csv}")
        print("[PERF] Run your Karate feature files first to generate performance data.")
        sys.exit(1)
    report = PerfReport(args.csv, args.output)
    if args.consumer_filter:
        consumers = [c.strip() for c in args.consumer_filter.split(",")]
        report.df = report.df[report.df["consumer"].isin(consumers)].reset_index(drop=True)
        if report.df.empty:
            print(f"[PERF] No data found for consumers: {consumers}")
            sys.exit(1)
        print(f"[PERF] Filtered to consumers: {consumers} ({len(report.df)} rows)")
    if args.feature_filter:
        features = [f.strip() for f in args.feature_filter.split(",")]
        report.df = report.df[report.df["feature"].isin(features)].reset_index(drop=True)
        if report.df.empty:
            print(f"[PERF] No data found for features: {features}")
            sys.exit(1)
        print(f"[PERF] Filtered to features: {features} ({len(report.df)} rows)")
    report.generate()


if __name__ == "__main__":
    main()

