"""Validation Report Generator"""

from __future__ import annotations

import os
import sys
import json
import logging
import pandas as pd
from collections import defaultdict, deque
from difflib import SequenceMatcher
from datetime import datetime
from typing import Optional, List, Tuple, Dict

import io
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

# Resolve project base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if not os.path.exists(os.path.join(BASE_DIR, 'pom.xml')):
    BASE_DIR = os.getcwd().split("src")[0] if "src" in os.getcwd() else os.getcwd()

# Consumer Configuration
try:
    import feature_config as _fc  # co-located configuration module
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'feature_config',
        os.path.join(os.path.dirname(__file__), 'feature_config.py'),
    )
    _fc = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_fc)

# Onboard a NEW validation by editing feature_config.CONSUMER_CONFIG (or drop a
CONSUMER_CONFIG = dict(_fc.CONSUMER_CONFIG)

# Generic, configuration-driven discovery
try:
    import validation_framework as _vf  # co-located helper module
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'validation_framework',
        os.path.join(os.path.dirname(__file__), 'validation_framework.py'),
    )
    _vf = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_vf)

try:
    _discovered = _vf.discover_validation_configs()
    if _discovered:
        CONSUMER_CONFIG.update(_discovered)
        print(f"[INFO] Loaded {len(_discovered)} validation config(s): {', '.join(_discovered.keys())}")
except Exception as _exc:  # discovery must never break the legacy consumers
    print(f"[WARN]  Config discovery skipped: {_exc}")

# Hardcoded override layer (Null vs Null Validation Override). Add new
# overrides ONLY to hardcoding.py - this engine file never changes for that.
try:
    import hardcoding as _hc  # co-located override configuration module
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'hardcoding',
        os.path.join(os.path.dirname(__file__), 'hardcoding.py'),
    )
    _hc = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_hc)

# Consumer-based reporting layer (Run Information / Validation Summary sheets).
# Purely additive - see consumer_report.py.
try:
    import consumer_report as _cr  # co-located reporting module
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'consumer_report',
        os.path.join(os.path.dirname(__file__), 'consumer_report.py'),
    )
    _cr = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_cr)

# CSV column aliases (canonical name -> list of possible column names in CSV)
CSV_COLUMN_ALIASES = _fc.CSV_COLUMN_ALIASES

# Columns that are always required
CSV_REQUIRED_COLUMNS = _fc.CSV_REQUIRED_COLUMNS


# Utility helpers

def resolve_column(df: pd.DataFrame, aliases: list) -> Optional[str]:
    for name in aliases:
        if name in df.columns:
            return name
    return None


def verify_csv_columns(df: pd.DataFrame, require_claimtype: bool = False) -> dict:
    """Resolve CSV column names using aliases."""
    col_map = {}
    missing = []
    for canonical, aliases in CSV_COLUMN_ALIASES.items():
        found = resolve_column(df, aliases)
        if found:
            col_map[canonical] = found
        elif canonical in CSV_REQUIRED_COLUMNS:
            missing.append(canonical)
        elif canonical == 'claimtype' and require_claimtype:
            missing.append(canonical)
    if missing:
        raise ValueError(
            f"Missing required CSV columns: {', '.join(missing)}\n"
            f"Available columns: {', '.join(df.columns)}"
        )
    return col_map


def normalize_path(path: str) -> str:
    path = path.strip()
    stripped = path.lstrip('/')
    # meta paths stay as-is - they live at the response root, not inside claim array
    if stripped.startswith('meta/'):
        return '/' + stripped
    # /data/*/ and /data/N/ -> /claim/*/ (wildcard the index)
    path = path.replace('/data/*/', '/claim/*/')
    # Replace hardcoded numeric indices: /data/0/ -> /claim/*/
    import re
    path = re.sub(r'/data/\d+/', '/claim/*/', path)
    stripped = path.lstrip('/')
    if not (stripped.startswith('claim/') or stripped.startswith('data/') or stripped.startswith('meta/')):
        path = '/claim/*/' + stripped
    return path


def wildcard_path(path: str) -> str:
    return '/'.join(['*' if p.isdigit() else p for p in path.strip('/').split('/')])


def extract_values(json_obj, pointer: str) -> list:
    """Extract all values matching a JSON pointer (supports * wildcards)."""
    def _extract(obj, parts, path_so_far):
        if not parts:
            return [(path_so_far.rstrip('/'), obj)]
        part, rest = parts[0], parts[1:]
        results = []
        if isinstance(obj, list):
            if part == '*':
                for i, item in enumerate(obj):
                    results.extend(_extract(item, rest, f"{path_so_far}/{i}"))
            elif part.isdigit():
                idx = int(part)
                if 0 <= idx < len(obj):
                    results.extend(_extract(obj[idx], rest, f"{path_so_far}/{idx}"))
        elif isinstance(obj, dict):
            if part in obj:
                results.extend(_extract(obj[part], rest, f"{path_so_far}/{part}"))
        return results

    return _extract(json_obj, pointer.strip('/').split('/'), '')


def safe_float(value) -> float:
    try:
        if isinstance(value, str):
            value = value.replace(',', '').replace('+', '').strip()
        return float(value) if value not in ('', None) else 0.0
    except (ValueError, TypeError):
        return 0.0


def normalize_value(value) -> str:
    if value is None:
        return ''
    s = str(value).strip()
    if s.lower() in ('null', 'none', 'nan'):
        return ''
    # Normalize purely-numeric strings so zero-padded / formatting-only
    if s.isdigit():
        return str(int(s))
    return s


# Fuzzy value comparison
_FUZZY_MATCH_THRESHOLD = _fc.FUZZY_MATCH_THRESHOLD


def values_match(a, b) -> bool:
    na = normalize_value(a)
    nb = normalize_value(b)
    if na == nb:
        return True
    # Only fuzzy-match non-empty strings; an empty vs non-empty value is a
    if not na or not nb:
        return False
    if SequenceMatcher(None, na, nb).ratio() >= _FUZZY_MATCH_THRESHOLD:
        return True
    return False


def _is_empty_record(val) -> bool:
    """True if `val` represents an empty placeholder object/array rather than"""
    if val is None:
        return True
    if isinstance(val, dict):
        if not val:
            return True
        return all(_is_empty_record(v) for v in val.values())
    if isinstance(val, list):
        if not val:
            return True
        return all(_is_empty_record(v) for v in val)
    return normalize_value(val) == ''


def _resolve_mapping_col(df: pd.DataFrame, aliases: list) -> Optional[str]:
    """Resolve a mapping-sheet column from a list of candidate header names."""
    cols = {str(c).strip().lower(): c for c in df.columns}
    for a in aliases:
        key = str(a).strip().lower()
        if key in cols:
            return cols[key]
    return None


def load_mapping(
    excel_path: str,
    source_aliases: Optional[list] = None,
    target_aliases: Optional[list] = None,
    normalize: bool = True,
) -> List[Tuple[str, str]]:
    """Load a two-column field-mapping workbook.

    The source/target path columns are resolved generically from ``*_aliases``
    (falling back to ``feature_config.MAPPING_COLUMN_ALIASES``) so ANY two-column
    mapping sheet works — the engine never hardcodes a single header name.

    ``normalize`` applies the claim-array path normalization used by the
    PPKG-vs-Alex engine. For same-shape "direct" comparisons pass
    ``normalize=False`` to keep the raw JSON pointers exactly as authored.
    """
    df = pd.read_excel(excel_path, engine='openpyxl')
    src_aliases = source_aliases or _fc.MAPPING_COLUMN_ALIASES['source']
    tgt_aliases = target_aliases or _fc.MAPPING_COLUMN_ALIASES['target']
    src_col = _resolve_mapping_col(df, src_aliases)
    tgt_col = _resolve_mapping_col(df, tgt_aliases)
    if src_col is None or tgt_col is None:
        raise ValueError(
            f"Could not resolve mapping columns in '{os.path.basename(excel_path)}'. "
            f"Tried source={src_aliases} / target={tgt_aliases}. "
            f"Available columns: {list(df.columns)}"
        )
    df.dropna(subset=[src_col, tgt_col], inplace=True)
    if normalize:
        prep = lambda p: normalize_path(str(p))
    else:
        prep = lambda p: '/' + str(p).strip().lstrip('/')
    return [(prep(row[src_col]), prep(row[tgt_col])) for _, row in df.iterrows()]


def wrap_response(data: dict) -> Tuple[dict, str]:
    """Return the FULL claim array with ALL transactions at their original indices."""
    root_key = 'claim'
    if isinstance(data, dict):
        if 'claim' in data:
            root_key = 'claim'
            claims = data['claim']
        elif 'data' in data:
            root_key = 'data'
            claims = data['data']
        else:
            claims = []
    else:
        claims = []

    if not isinstance(claims, list):
        claims = []

    return {"claim": claims}, root_key


def is_error_response(data) -> bool:
    if not isinstance(data, dict):
        return False
    # Explicit status error codes
    if data.get("status") in [404, "404", 400, "400"]:
        return True
    # Generic service-status envelope (e.g. {"svcRspSts": {"ResponseCode": "404"}})
    for env_key in ('svcRspSts', 'serviceResponseStatus', 'responseStatus'):
        env = data.get(env_key)
        if isinstance(env, dict):
            code = str(env.get('ResponseCode', env.get('responseCode', '')) or '').strip()
            if code[:1] in ('4', '5'):
                return True
    # Summary API returns warnings in meta with no data key when not found
    if 'meta' in data and 'data' not in data and 'claim' not in data:
        warnings = data.get('meta', {}).get('warnings', [])
        if warnings:
            return True
    return False


def describe_error_response(source: str, data) -> str:
    """Build a human-readable failure message for an error response.

    Surfaces the real diagnostic information for BOTH error shapes:
      1. top-level  {status, detail, title}
      2. gateway    {meta: {warnings: [{code, title, detail}, ...]}}
    So the report's 'Failure Reason' is meaningful (e.g. the 500 "Graph API
    Unavailable / Unable to retrieve data from HCP" warning) instead of an
    empty 'returned error:' string.
    """
    if not isinstance(data, dict):
        return f"{source} returned a non-JSON / unexpected response"

    # Shape 2: meta.warnings[] - collect code/title/detail from each warning.
    warnings = (data.get('meta') or {}).get('warnings') or []
    if warnings:
        parts = []
        for w in warnings:
            if not isinstance(w, dict):
                parts.append(str(w).strip())
                continue
            code   = str(w.get('code', '') or '').strip()
            title  = str(w.get('title', '') or '').strip().strip('"').strip()
            detail = str(w.get('detail', '') or '').strip()
            seg = ' - '.join(p for p in (code, title, detail) if p)
            if seg:
                parts.append(seg)
        if parts:
            return f"{source} returned error: " + ' | '.join(parts)

    # Shape 1: top-level status/title/detail.
    status = str(data.get('status', '') or '').strip()
    title  = str(data.get('title', '') or '').strip()
    detail = str(data.get('detail', '') or '').strip()
    seg = ' - '.join(p for p in (status, title, detail) if p)
    return f"{source} returned error: " + (seg or 'unspecified error')


def extract_status_code(data) -> str:
    """Best-effort HTTP / service status code from an error-response envelope.

    Looks at the same shapes is_error_response() understands:
      1. top-level  {"status": 404, ...}
      2. service    {"svcRspSts": {"ResponseCode": "404"}} (or responseStatus/…)
      3. gateway    {"meta": {"warnings": [{"code": "500", ...}]}}
    Returns '' when no code can be found.
    """
    if not isinstance(data, dict):
        return ''
    st = data.get('status')
    if st not in (None, ''):
        return str(st).strip()
    for env_key in ('svcRspSts', 'serviceResponseStatus', 'responseStatus'):
        env = data.get(env_key)
        if isinstance(env, dict):
            code = env.get('ResponseCode', env.get('responseCode', ''))
            if str(code).strip():
                return str(code).strip()
    warnings = (data.get('meta') or {}).get('warnings') or []
    for w in warnings:
        if isinstance(w, dict):
            code = str(w.get('code', '') or '').strip()
            if code:
                return code
    return ''


def _truncate_text(text, max_len: int = 30000) -> str:
    """Keep Excel cells under the 32,767-char limit."""
    if text is None:
        return ''
    text = str(text)
    return text if len(text) <= max_len else text[:max_len] + ' ...(truncated)'


def format_actual_response(source: str, data, max_len: int = 30000) -> str:
    """Serialize the ACTUAL response body for the 'Failure Reason' cell so the
    report shows exactly what came back from the service."""
    if data is None:
        return ''
    try:
        body = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except Exception:
        body = str(data)
    body = _truncate_text(body, max_len)
    return f"{source} response: {body}" if source else body


def has_claim_data(data) -> bool:
    if not isinstance(data, dict):
        return False
    for key in ('data', 'claim'):
        val = data.get(key)
        if isinstance(val, list) and len(val) > 0:
            return True
    return False


def get_claims_list(data: dict) -> list:
    """Return the raw claim array from a response dict."""
    if not isinstance(data, dict):
        return []
    return data.get('claim') or data.get('data') or []


def build_member_identifier(member_number_raw: str) -> str:
    """Build the member number part of the response filename."""
    try:
        # Strip any trailing .0 from CSV integer read as float
        s = str(member_number_raw).strip()
        if s.endswith('.0'):
            s = s[:-2]
        return s.zfill(9)
    except Exception:
        return str(member_number_raw).strip()


# Claim Match Summary helpers

def build_claim_match_and_missing(
    hcp_data: dict,
    alex_data: dict,
    claim_number: str,
    icn_number: str,
    member_number: str,
    claim_type: str,
    consumer: str,
    validation_type: str,
    test_case: str = '',
) -> Tuple[List[dict], List[dict]]:
    """Match PPKG (HCP) claim transactions to Alex claim transactions by ICN"""
    ppkg_claims = get_claims_list(hcp_data)
    alex_claims = get_claims_list(alex_data)

    # Build Alex ICN -> deque of indices (same ICN may appear multiple times)
    alex_icn_map: Dict[str, deque] = {}
    for i, c in enumerate(alex_claims):
        if isinstance(c, dict):
            icn = str(c.get('claimIdentifiers', {}).get('internalReferenceIdentifier', '') or '')
            if icn:
                alex_icn_map.setdefault(icn, deque()).append(i)

    claim_match_rows: List[dict] = []
    missing_records_rows: List[dict] = []
    matched_alex_indices: set = set()

    # Walk PPKG claims
    for ppkg_idx, ppkg_claim in enumerate(ppkg_claims):
        if not isinstance(ppkg_claim, dict):
            continue
        ppkg_icn      = str(ppkg_claim.get('claimIdentifiers', {}).get('internalReferenceIdentifier', '') or '')
        ppkg_txn      = str(ppkg_claim.get('claimIdentifiers', {}).get('claimTransactionIdentifier', '') or '')
        ppkg_txn_type = str(ppkg_claim.get('claimCategories', {}).get('claimTransactionType', '') or '')

        available = alex_icn_map.get(ppkg_icn, deque())
        alex_idx  = available.popleft() if available else None

        if alex_idx is None:
            claim_match_rows.append({
                'Test Case':        test_case,
                'Claim Number':     claim_number,
                'Member Number':    member_number,
                'Claim Type':       claim_type,
                'Consumer':         consumer,
                'PPKG Claim Index': ppkg_idx,
                'Alex Claim Index': '',
                'PPKG ICN':         ppkg_icn,
                'Alex ICN':         '',
                'PPKG TxnId':       ppkg_txn,
                'Alex TxnId':       '',
                'PPKG TxnType':     ppkg_txn_type,
                'Alex TxnType':     '',
                'Match Status':     'Missing in Alex',
            })
            missing_records_rows.append(_missing_row(
                test_case, claim_number, ppkg_icn or icn_number, claim_type, validation_type,
                True, True, 'MATCHING_RECORD_NOT_FOUND',
                f"PPKG claim transaction (ICN {ppkg_icn!r}, index {ppkg_idx}) has no matching Alex claim.",
            ))
        else:
            matched_alex_indices.add(alex_idx)
            alex_claim    = alex_claims[alex_idx]
            alex_icn      = str(alex_claim.get('claimIdentifiers', {}).get('internalReferenceIdentifier', '') or '')
            alex_txn      = str(alex_claim.get('claimIdentifiers', {}).get('claimTransactionIdentifier', '') or '')
            alex_txn_type = str(alex_claim.get('claimCategories', {}).get('claimTransactionType', '') or '')
            claim_match_rows.append({
                'Test Case':        test_case,
                'Claim Number':     claim_number,
                'Member Number':    member_number,
                'Claim Type':       claim_type,
                'Consumer':         consumer,
                'PPKG Claim Index': ppkg_idx,
                'Alex Claim Index': alex_idx,
                'PPKG ICN':         ppkg_icn,
                'Alex ICN':         alex_icn,
                'PPKG TxnId':       ppkg_txn,
                'Alex TxnId':       alex_txn,
                'PPKG TxnType':     ppkg_txn_type,
                'Alex TxnType':     alex_txn_type,
                'Match Status':     'Matched',
            })

    # Alex claims not matched to any PPKG claim
    for alex_idx, alex_claim in enumerate(alex_claims):
        if alex_idx in matched_alex_indices:
            continue
        if not isinstance(alex_claim, dict):
            continue
        alex_icn      = str(alex_claim.get('claimIdentifiers', {}).get('internalReferenceIdentifier', '') or '')
        alex_txn      = str(alex_claim.get('claimIdentifiers', {}).get('claimTransactionIdentifier', '') or '')
        alex_txn_type = str(alex_claim.get('claimCategories', {}).get('claimTransactionType', '') or '')
        claim_match_rows.append({
            'Test Case':        test_case,
            'Claim Number':     claim_number,
            'Member Number':    member_number,
            'Claim Type':       claim_type,
            'Consumer':         consumer,
            'PPKG Claim Index': '',
            'Alex Claim Index': alex_idx,
            'PPKG ICN':         '',
            'Alex ICN':         alex_icn,
            'PPKG TxnId':       '',
            'Alex TxnId':       alex_txn,
            'PPKG TxnType':     '',
            'Alex TxnType':     alex_txn_type,
            'Match Status':     'Missing in PPKG',
        })
        missing_records_rows.append(_missing_row(
            test_case, claim_number, alex_icn or icn_number, claim_type, validation_type,
            True, True, 'MATCHING_RECORD_NOT_FOUND',
            f"Alex claim transaction (ICN {alex_icn!r}, index {alex_idx}) has no matching PPKG claim.",
        ))

    return claim_match_rows, missing_records_rows


# Column definitions for all 5 sheets

CONSOLIDATED_COLUMNS = [
    'Test Case', 'Member Number', 'Claim Number', 'ICN Number',
    'Claim Type', 'ClaimTransaction',
    'PPKG Claim Index', 'Alex Claim Index',
    'PPKG ICN', 'Alex ICN',
    'Json Schema',
    'PPKGPath', 'AlexPath',
    'Normalized Pointer',
    'PPKGValue', 'AlexValue',
    'Match Status', 'Category', 'Severity', 'Conclusion',
    'Parent Alignment Issue', 'Root Cause Path',
]

# Exact, business-facing column set for the exported 'Validation Results'
VALIDATION_RESULTS_COLUMNS = [
    'Test Case', 'Member Number', 'Claim Number', 'ICN Number',
    'Claim Type', 'ClaimTransaction',
    'PPKG Claim Index', 'Alex Claim Index',
    'PPKG ICN', 'Alex ICN',
    'Json Schema',
    'PPKGPath', 'AlexPath',
    'PPKGValue', 'AlexValue',
    'Match Status', 'Category', 'Severity', 'Conclusion',
]

# Schema Validation sheet - one row per normalized pointer, cross-referencing
SCHEMA_VALIDATION_COLUMNS = [
    'Normalized Pointer',
    'Mapping Pointer', 'PPKG Schema Pointer', 'Alex Schema Pointer',
    'Present In Mapping', 'Present In PPKG Schema', 'Present In Alex Schema',
    'Response Status', 'Category', 'Severity', 'Conclusion',
    'Missing Only In Response', 'Missing Only In Schema',
    'Missing In Both Response And Schema', 'Mapped But Not Populated',
    'Occurrences',
]


# Severity classification & reconciliation helpers

def classify_severity(status: str, ppkg_val, alex_val) -> Tuple[str, str, str]:
    """Classify a comparison outcome into (Severity, Conclusion, Category)."""
    pv = normalize_value(ppkg_val)
    av = normalize_value(alex_val)
    pv_empty = _is_empty_record(ppkg_val)
    av_empty = _is_empty_record(alex_val)

    if status == 'Match':
        return 'Non-Blocker', 'Values Match', 'Match'
    if status == 'Mismatch':
        # Null on both sides is never a real mismatch.
        if pv == '' and av == '':
            return 'Non-Blocker', 'Null in Both (ignored)', 'Match'
        # One side is an empty placeholder object, the other holds real data
        if pv_empty and not av_empty:
            return (
                'Non-Blocker',
                'PPKG returned an empty placeholder object/array at this '
                'position; Alex has the populated record. Not a genuine '
                'value mismatch.',
                'Empty Record In PPKG',
            )
        if av_empty and not pv_empty:
            return (
                'Non-Blocker',
                'Alex returned an empty placeholder object/array at this '
                'position; PPKG has the populated record. Not a genuine '
                'value mismatch.',
                'Empty Record In Alex',
            )
        return 'Blocker', 'Data Mismatch between PPKG and Alex', 'Data Mismatch'
    if status == 'Value Missing in Target':
        # PPKG itself only holds an empty placeholder at this array position -
        if pv_empty:
            return (
                'Non-Blocker',
                'PPKG contains an empty placeholder object/array at this '
                'position; Alex may hold the populated record at a '
                'different array index. Not a genuine missing-field defect.',
                'Empty Record In PPKG',
            )
        # Provisional - refined post-run once the aggregate Alex schema is
        return 'Blocker', 'Field present in PPKG, missing in Alex', 'Missing In Alex (True Missing)'
    if status == 'Value Missing in Source':
        return 'Non-Blocker', 'New Field Added in Alex Response', 'Alex Only Field'
    if status == 'Value Missing in Both':
        return 'Non-Blocker', 'Field absent in both PPKG and Alex', 'Missing In Both'
    return 'Non-Blocker', '', ''


def status_category(status: str) -> str:
    """Reviewer-friendly category label for the straightforward statuses."""
    return {
        'Match':                  'Match',
        'Mismatch':                'Data Mismatch',
        'Value Missing in Target':  'Missing In Alex (True Missing)',
        'Value Missing in Both':  'Missing In Both',
    }.get(status, '')


def refine_value_missing_in_ppkg(in_ppkg_schema: bool) -> Tuple[str, str, str]:
    """Refine the generic 'Value Missing in Source' outcome into two distinct,"""
    if in_ppkg_schema:
        return (
            'Blocker',
            'Field expected in PPKG but not returned (PPKG has this field '
            'type elsewhere in the dataset, but not this specific occurrence)',
            'Missing In PPKG (True Missing)',
        )
    return (
        'Non-Blocker',
        'Field available in Alex. No corresponding field exists in PPKG. '
        'Validation not applicable.',
        'Alex Only Field',
    )


def refine_value_missing_in_alex(in_alex_schema: bool) -> Tuple[str, str, str]:
    """Refine the generic 'Value Missing in Target' outcome using the AGGREGATE"""
    if in_alex_schema:
        return (
            'Non-Blocker',
            'Field exists in both systems; Alex has this record at a '
            'different array index/position. Investigate record-matching / '
            'array alignment logic - do NOT treat this as a missing field.',
            'Record Alignment Difference',
        )
    return (
        'Blocker',
        'Field present in PPKG, missing in Alex',
        'Missing In Alex (True Missing)',
    )


def strip_path_suffix(path: str) -> str:
    """Remove the ' (field absent in ...)' annotation and any summation from a path."""
    if not path:
        return ''
    p = str(path).split(' (field absent')[0].strip()
    # For summation comparisons keep only the first component for normalization
    if '+' in p:
        p = p.split('+')[0].strip()
    return p


def normalized_pointer_for_row(row: dict) -> str:
    """Derive the normalized (index-stripped, wildcarded) JSON pointer for a"""
    status = row.get('Match Status', '')
    if status == 'Value Missing in Source':
        raw = strip_path_suffix(row.get('AlexPath', ''))
    else:
        raw = strip_path_suffix(row.get('PPKGPath', ''))
    if not raw:
        raw = strip_path_suffix(row.get('AlexPath', ''))
    return '/' + wildcard_path(raw) if raw else ''


def build_conclusion(status: str, in_alex_schema: bool) -> str:
    """Human-readable reconciliation conclusion combining response status + schema presence."""
    if status == 'Match':
        return 'Field matches in PPKG and Alex'
    if status == 'Mismatch':
        return 'Data Mismatch between PPKG and Alex'
    if status == 'Value Missing in Target':
        return 'Missing in Alex Schema and Response' if not in_alex_schema else 'Missing in Alex Response'
    if status == 'Value Missing in Source':
        return 'New Field Added in Alex Response'
    if status == 'Value Missing in Both':
        return 'Field absent in both PPKG and Alex'
    return ''


# Ranking so the "worst" status wins when a pointer appears with several statuses
_STATUS_RANK = {
    'Mismatch':               5,
    'Value Missing in Target':  4,
    'Value Missing in Source':  3,
    'Value Missing in Both':  2,
    'Match':                  1,
}


# Generic, dynamic Summary-metric helpers

def _count_rows(df: pd.DataFrame, **filters) -> int:
    """Count rows in `df` matching ALL given column=value filters."""
    if df is None or df.empty:
        return 0
    mask = pd.Series(True, index=df.index)
    for col, val in filters.items():
        if col not in df.columns:
            return 0
        mask &= (df[col] == val)
    return int(mask.sum())


def _reference(**filters) -> str:
    """Build a human-readable "how to reproduce this count" reference string,"""
    parts = ['Validation Results Sheet'] + [f"{col} = '{val}'" for col, val in filters.items()]
    return ' | '.join(parts)


def _unique_issue_count(df: pd.DataFrame, match_status: str, category: str) -> int:
    """Count UNIQUE underlying issues for a suppressible category (Record"""
    if df is None or df.empty:
        return 0
    sub = df[(df['Match Status'] == match_status) & (df['Category'] == category)]
    if sub.empty:
        return 0
    is_suppressed = sub['Parent Alignment Issue'] == 'Y'
    suppressed_unique = (
        sub.loc[is_suppressed, ['Test Case', 'Claim Number', 'Root Cause Path']]
        .drop_duplicates()
        .shape[0]
    )
    non_suppressed = int((~is_suppressed).sum())
    return suppressed_unique + non_suppressed


def build_schema_validation(
    consolidated_rows: List[dict],
    mapping_all_wc: set,
    ppkg_paths_all: Dict[str, object],
    alex_paths_all: Dict[str, object],
) -> List[dict]:
    """Build the Schema Validation worksheet - one row per normalized JSON"""
    agg: Dict[str, dict] = {}
    for r in consolidated_rows:
        ptr = normalized_pointer_for_row(r)
        if not ptr:
            continue
        status = r.get('Match Status', '')
        entry  = agg.get(ptr)
        if entry is None:
            agg[ptr] = {'status': status, 'count': 1}
        else:
            entry['count'] += 1
            if _STATUS_RANK.get(status, 0) > _STATUS_RANK.get(entry['status'], 0):
                entry['status'] = status

    # Build the canonical schema-order index (shared with every other sheet)
    schema_order = build_schema_order_index(ppkg_paths_all, alex_paths_all)
    ordered_ptrs = ordered_by_schema(
        [p.lstrip('/') for p in agg.keys()], schema_order,
    )
    # Map back from wildcard (no leading slash) to the original pointer key.
    wc_to_ptr = {p.lstrip('/'): p for p in agg.keys()}
    ordered_ptrs = [wc_to_ptr[wc] for wc in ordered_ptrs]

    rows: List[dict] = []
    for ptr in ordered_ptrs:
        info    = agg[ptr]
        status  = info['status']
        wc      = ptr.lstrip('/')
        in_map  = wc in mapping_all_wc
        # schema_has_path() recognizes object/array-level pointers as
        in_ppkg = schema_has_path(wc, ppkg_paths_all)
        in_alex = schema_has_path(wc, alex_paths_all)

        # Use the SAME refinement as Validation Results / Summary for the
        if status == 'Value Missing in Source':
            severity, conclusion, category = refine_value_missing_in_ppkg(in_ppkg)
        elif status == 'Value Missing in Target':
            severity, conclusion, category = refine_value_missing_in_alex(in_alex)
        else:
            severity, conclusion, category = classify_severity(
                status,
                'x' if status == 'Mismatch' else '',   # ensure Mismatch treated as blocker
                'y' if status == 'Mismatch' else '',
            )

        # Reconciliation-question flags (mutually clarifying categories)
        missing_only_in_response = bool(
            (status == 'Value Missing in Target' and category == 'Record Alignment Difference') or
            (status == 'Value Missing in Source' and category == 'Missing In Source (True Missing)')
        )
        missing_only_in_schema = bool(in_map and (in_ppkg != in_alex))
        missing_in_both = bool(in_map and not in_ppkg and not in_alex)
        mapped_but_not_populated = bool(
            in_map and in_ppkg and in_alex and
            (status == 'Value Missing in Both' or 'Null' in conclusion)
        )

        rows.append({
            'Normalized Pointer':      ptr,
            'Mapping Pointer':         ptr if in_map  else '',
            'PPKG Schema Pointer':     ptr if in_ppkg else '',
            'Alex Schema Pointer':     ptr if in_alex else '',
            'Present In Mapping':          _yn(in_map),
            'Present In PPKG Schema':      _yn(in_ppkg),
            'Present In Alex Schema':      _yn(in_alex),
            'Response Status':         status,
            'Category':                category,
            'Severity':                severity,
            'Conclusion':              conclusion,
            'Missing Only In Response':             _yn(missing_only_in_response),
            'Missing Only In Schema':                _yn(missing_only_in_schema),
            'Missing In Both Response And Schema':   _yn(missing_in_both),
            'Mapped But Not Populated':              _yn(mapped_but_not_populated),
            'Occurrences':             info['count'],
        })
    return rows

SUMMARY_COLUMNS = [
    'Test Case', 'Claim Number', 'ICN Number', 'ClaimTransaction',
    'Coverage Percentage', 'Matched Values',
]

CLAIM_MATCH_COLUMNS = [
    'Test Case', 'Claim Number', 'Member Number', 'Claim Type', 'Consumer',
    'PPKG Claim Index', 'Alex Claim Index',
    'PPKG ICN', 'Alex ICN',
    'PPKG TxnId', 'Alex TxnId',
    'PPKG TxnType', 'Alex TxnType',
    'Match Status',
]

MISSING_RECORDS_COLUMNS = [
    'Test Case', 'Claim Number', 'ICN', 'Claim Type', 'Validation Type',
    'PPKG Response Available', 'Alex Response Available',
    'Failure Category', 'Failure Reason',
]

# Schema Coverage Analysis sheet (schema-drift detection)
SCHEMA_COVERAGE_COLUMNS = [
    'Path', 'Source',
    'Present In Mapping', 'Present In PPKG Response', 'Present In Alex Response',
    'Coverage Status', 'Sample Value',
]

# Recognised Missing-Records failure categories
FAILURE_CATEGORIES = (
    'RESPONSE_MISSING_PPKG',
    'RESPONSE_MISSING_ALEX',
    'RESPONSE_MISSING_BOTH',
    'INVALID_CLAIM_TYPE',
    'CLAIM_NOT_FOUND',
    'MATCHING_RECORD_NOT_FOUND',
    # The SAME claim/member appears on more than one test-data row. The row is
    # still validated in full (nothing is dropped) - this category exists so the
    # repetition is visible on the Missing Records + Summary sheets.
    'DUPLICATE_RECORD',
    # Generic ("direct") mode: one side returned an error/failure envelope
    # (e.g. 404/500) while the other returned a normal response.
    'RESPONSE_FAILED_PPKG',
    'RESPONSE_FAILED_ALEX',
)


def _yn(flag) -> str:
    """Boolean -> 'Y' / 'N'."""
    return 'Y' if flag else 'N'


def _missing_row(test_case, claim_number, icn, claim_type, validation_type,
                 ppkg_avail, alex_avail, category, reason) -> dict:
    """Build a single Missing Records row using the enhanced schema."""
    return {
        'Test Case':               test_case,
        'Claim Number':            claim_number,
        'ICN':                     icn,
        'Claim Type':              claim_type,
        'Validation Type':         validation_type,
        'PPKG Response Available': _yn(ppkg_avail),
        'Alex Response Available': _yn(alex_avail),
        'Failure Category':        category,
        'Failure Reason':          reason,
    }


# Core comparison engine helpers

def resolved_path_str(raw_ptr: str, root_key: str) -> str:
    ptr = raw_ptr.lstrip('/')
    if ptr.startswith('claim/'):
        ptr = root_key + ptr[len('claim'):]
    return '/' + ptr


def path_claim_index(resolved_ptr: str) -> str:
    parts = resolved_ptr.strip('/').split('/')
    if len(parts) >= 2 and parts[1].isdigit():
        return parts[1]
    return ''


def with_claim_index(path: str, idx) -> str:
    """Return a copy of a mapping path with its top-level claim index replaced by `idx`."""
    parts = path.strip('/').split('/')
    if len(parts) >= 2 and (parts[1].isdigit() or parts[1] == '*'):
        parts[1] = str(idx)
    return '/' + '/'.join(parts)


def get_claim_icn(data: dict, claim_index: int) -> str:
    if not isinstance(data, dict) or claim_index < 0:
        return ''
    claims = data.get('claim') or data.get('data') or []
    if not isinstance(claims, list) or claim_index >= len(claims):
        return ''
    claim_obj = claims[claim_index]
    if not isinstance(claim_obj, dict):
        return ''
    return str(claim_obj.get('claimIdentifiers', {}).get('internalReferenceIdentifier', '') or '')


def _desentinel_pointer(path: str, sibling: str) -> str:
    """Guarantee the internal out-of-range sentinel index (_NO_MATCH_INDEX,"""
    if not path or str(_NO_MATCH_INDEX) not in path:
        return path
    core, sep, note = path.partition(' ')          # split off any " (field absent...)" note
    sib_core        = (sibling or '').partition(' ')[0]
    parts = core.split('/')
    sibs  = sib_core.split('/')
    for i, seg in enumerate(parts):
        if seg == str(_NO_MATCH_INDEX):
            parts[i] = sibs[i] if i < len(sibs) and sibs[i].isdigit() else ''
    fixed = '/'.join(p for p in parts if p != '')
    return fixed + sep + note


def _row(test_case, member_number, claim_number, icn_number,
         claim_type, claim_transaction,
         ppkg_idx, alex_idx, ppkg_icn, alex_icn,
         hcp_path, alex_path,
         hcp_val, alex_val, status,
         mapping_order=0) -> dict:
    """Build a single consolidated data row. Consumer and Type are intentionally excluded."""
    # Never let the internal out-of-range sentinel index leak into the report -
    hcp_path  = _desentinel_pointer(hcp_path,  alex_path)
    alex_path = _desentinel_pointer(alex_path, hcp_path)
    severity, conclusion, category = classify_severity(status, hcp_val, alex_val)
    # NOTE: for 'Value Missing in Source' (unless caught as an empty record) and
    src_path = alex_path if status == 'Value Missing in Source' else hcp_path
    src_path = strip_path_suffix(src_path) or strip_path_suffix(alex_path)
    normalized_ptr = '/' + wildcard_path(src_path) if src_path else ''
    return {
        'Test Case':          test_case,
        'Member Number':      member_number,
        'Claim Number':       claim_number,
        'ICN Number':         icn_number,
        'Claim Type':         claim_type,
        'ClaimTransaction':   claim_transaction,
        'PPKG Claim Index':   ppkg_idx,
        'Alex Claim Index':   alex_idx,
        'PPKG ICN':           ppkg_icn,
        'Alex ICN':           alex_icn,
        # Normalized (index-stripped, wildcarded) schema path - lets reviewers
        'Json Schema':        normalized_ptr,
        'PPKGPath':           hcp_path,
        'AlexPath':           alex_path,
        'Normalized Pointer': normalized_ptr,
        'PPKGValue':          normalize_value(hcp_val),
        'AlexValue':          normalize_value(alex_val),
        'Match Status':       status,
        'Category':           category,
        'Severity':           severity,
        'Conclusion':         conclusion,
        # Default: this row is NOT a suppressed child of some other parent
        'Parent Alignment Issue': 'N',
        'Root Cause Path':        '',
        '_mapping_order':     mapping_order,
    }


def _group_by_claim_index(vals: list) -> Dict[str, list]:
    """Group (resolved_ptr, value) tuples by their top-level claim index."""
    groups: Dict[str, list] = {}
    for ptr, val in vals:
        idx = path_claim_index(ptr)
        groups.setdefault(idx, []).append((ptr, val))
    return groups


def _build_resolved_alex_path(hcp_ptr: str, alex_path_schema: str, alex_root: str) -> str:
    """Build the expected Alex resolved path from the PPKG resolved ptr + Alex schema path."""
    hcp_parts  = hcp_ptr.strip('/').split('/')
    alex_parts = alex_path_schema.strip('/').split('/')
    resolved   = []
    hcp_cursor = 0
    for ap in alex_parts:
        if ap == '*':
            while hcp_cursor < len(hcp_parts) and not hcp_parts[hcp_cursor].isdigit():
                hcp_cursor += 1
            resolved.append(hcp_parts[hcp_cursor] if hcp_cursor < len(hcp_parts) else '0')
            hcp_cursor += 1
        else:
            resolved.append(ap)
            hcp_cursor += 1
    if resolved and resolved[0] == 'claim':
        resolved[0] = alex_root
    return '/' + '/'.join(resolved)


# Schema-drift helpers

def _wildcard_parts(parts: List[str]) -> str:
    """Join path segments, collapsing numeric array indices to '*'."""
    return '/'.join('*' if p.isdigit() else p for p in parts)


def extract_all_paths(data) -> Dict[str, object]:
    """Walk an entire response and return {wildcard_leaf_path: sample_value} for"""
    wrapped, _ = wrap_response(data)
    result: Dict[str, object] = {}

    def walk(obj, parts: List[str]):
        if isinstance(obj, dict):
            if not obj:
                result.setdefault(_wildcard_parts(parts), '')
            for k, v in obj.items():
                walk(v, parts + [str(k)])
        elif isinstance(obj, list):
            if not obj:
                result.setdefault(_wildcard_parts(parts), '')
            for i, item in enumerate(obj):
                walk(item, parts + [str(i)])
        else:
            result.setdefault(_wildcard_parts(parts), obj)

    walk(wrapped, [])
    if isinstance(data, dict) and isinstance(data.get('meta'), (dict, list)):
        walk(data['meta'], ['meta'])
    return result


def extract_all_paths_generic(data) -> Dict[str, object]:
    """Shape-agnostic variant of :func:`extract_all_paths`.

    Walks an ENTIRE response verbatim (no claim-array wrapping) and returns
    ``{wildcard_leaf_path: sample_value}``. Used by the generic "direct"
    comparison mode where responses do not follow the claim/data array schema.
    """
    result: Dict[str, object] = {}

    def walk(obj, parts: List[str]):
        if isinstance(obj, dict):
            if not obj:
                result.setdefault(_wildcard_parts(parts), '')
            for k, v in obj.items():
                walk(v, parts + [str(k)])
        elif isinstance(obj, list):
            if not obj:
                result.setdefault(_wildcard_parts(parts), '')
            for i, item in enumerate(obj):
                walk(item, parts + [str(i)])
        else:
            result.setdefault(_wildcard_parts(parts), obj)

    walk(data, [])
    return result


def build_schema_order_index(
    ppkg_paths: Dict[str, object],
    alex_paths: Dict[str, object],
) -> Dict[str, int]:
    """Build a single canonical ordering index (wildcard path -> position) that"""
    order: Dict[str, int] = {}
    for p in ppkg_paths:
        if p not in order:
            order[p] = len(order)
    for p in alex_paths:
        if p not in order:
            order[p] = len(order)
    return order


def ordered_by_schema(paths, schema_order: Dict[str, int]) -> List[str]:
    """Return `paths` ordered per `schema_order` (response schema walk order)."""
    _max = len(schema_order)
    return sorted(paths, key=lambda p: (schema_order.get(p, _max), p))


def schema_has_path(wc: str, paths_all: Dict[str, object]) -> bool:
    """True if the normalized wildcard pointer `wc` (no leading slash) is"""
    if wc in paths_all:
        return True
    prefix = wc + '/'
    return any(k.startswith(prefix) for k in paths_all)


def build_schema_coverage(
    mapping_all_wc: set,
    ppkg_paths: Dict[str, object],
    alex_paths: Dict[str, object],
    mapping_ppkg_wc: Optional[set] = None,
    mapping_alex_wc: Optional[set] = None,
) -> List[dict]:
    """Build the Schema Coverage Analysis rows by cross-referencing every path that"""
    mapping_ppkg_wc = mapping_ppkg_wc or set()
    mapping_alex_wc = mapping_alex_wc or set()

    schema_order  = build_schema_order_index(ppkg_paths, alex_paths)
    all_paths     = set(mapping_all_wc) | set(ppkg_paths) | set(alex_paths)
    ordered_paths = ordered_by_schema(all_paths, schema_order)

    rows: List[dict] = []

    for p in ordered_paths:
        in_map      = p in mapping_all_wc
        # schema_has_path() correctly recognizes object/array-level paths
        in_ppkg     = schema_has_path(p, ppkg_paths)
        in_alex     = schema_has_path(p, alex_paths)
        in_map_ppkg = p in mapping_ppkg_wc   # mapping sheet expects a PPKG counterpart
        in_map_alex = p in mapping_alex_wc   # mapping sheet expects an Alex counterpart

        if in_ppkg and in_alex:
            source = 'Both'
        elif in_ppkg:
            source = 'Source'
        elif in_alex:
            source = 'Target'
        else:
            source = 'Mapping'

        if in_ppkg and in_alex:
            # Field genuinely exists on both sides. If it's not yet in the
            status = 'Mapped And Present' if in_map else 'Missing Mapping Definition'
        elif in_ppkg and not in_alex:
            # Present in the source system only.
            status = 'Missing In Target' if in_map_alex else 'Field Available in Source Only (Not Available in Target)'
        elif in_alex and not in_ppkg:
            # Present in the target system only - the exact scenario reviewers found
            status = 'Missing In Source' if in_map_ppkg else 'Field Available in Target Only (Not Available in Source)'
        else:
            # Present in neither response (only reachable via a mapping entry).
            status = 'Missing In Both Responses' if in_map else 'Missing Mapping Definition'

        sample = ppkg_paths.get(p, alex_paths.get(p, ''))
        rows.append({
            'Path':                     '/' + p,
            'Source':                   source,
            'Present In Mapping':       _yn(in_map),
            'Present In PPKG Response': _yn(in_ppkg),
            'Present In Alex Response': _yn(in_alex),
            'Coverage Status':          status,
            'Sample Value':             normalize_value(sample),
        })
    return rows


# Parent-record inheritance helpers

_MISSING = object()  # sentinel: "path does not resolve to anything"


def _get_object_at_resolved_path(wrapped: dict, resolved_ptr: str):
    """Navigate `wrapped` (the {"claim": [...]} structure produced by"""
    if not resolved_ptr:
        return _MISSING
    obj = wrapped
    for part in resolved_ptr.strip('/').split('/'):
        if isinstance(obj, list):
            if not part.isdigit():
                return _MISSING
            idx = int(part)
            if idx < 0 or idx >= len(obj):
                return _MISSING
            obj = obj[idx]
        elif isinstance(obj, dict):
            if part not in obj:
                return _MISSING
            obj = obj[part]
        else:
            return _MISSING
    return obj


def _parent_pointer(ptr: str) -> str:
    """Return `ptr` with its final path segment removed (the containing object)."""
    parts = ptr.strip('/').split('/')
    return '/'.join(parts[:-1]) if len(parts) > 1 else ''


def _reroot_to_claim(path: str, root_key: str) -> str:
    """Rewrite a path's leading root segment to 'claim' (matching *_wrapped structures)."""
    parts = path.strip('/').split('/')
    if parts and parts[0] == root_key:
        parts[0] = 'claim'
    return '/'.join(parts)


def classify_missing_leaf_via_parent(parent_obj, missing_side: str) -> Optional[Tuple[str, str, str]]:
    """Given the raw parent container fetched from the "missing" side at the"""
    if parent_obj is _MISSING:
        return (
            'Non-Blocker',
            f'Parent record does not exist at this array position in {missing_side} '
            '(array cardinality differs between systems). This is a record/array '
            'alignment issue, not a genuine missing field.',
            'Record Alignment Difference',
        )
    if _is_empty_record(parent_obj):
        return (
            'Non-Blocker',
            f'Parent record in {missing_side} is an empty placeholder object at this '
            'array position; the other system holds the populated record. Not a '
            'genuine missing-field defect.',
            f'Empty Record In {missing_side}',
        )
    return None


# Index-based array record validation helpers

# Business/identifying keys used to look up a record that exists on both
BUSINESS_KEY_FIELDS = _fc.BUSINESS_KEY_FIELDS

# Key-Based Record Matching (PRIMARY alignment strategy)
ARRAY_MATCH_CONFIG: Dict[str, List] = _fc.ARRAY_MATCH_CONFIG

# Sentinel index used when key-based alignment searched the ENTIRE target
_NO_MATCH_INDEX = 999999


def _composite_key_lookup(flat: Dict[str, str], spec) -> Optional[object]:
    """Resolve a key spec (single field name, or tuple/list of field names for a"""
    fields = spec if isinstance(spec, (tuple, list)) else (spec,)
    values = []
    for field in fields:
        val = flat.get(field)
        if not val:
            fl = field.lower()
            val = next((v for k, v in flat.items() if fl in k.lower() and v != ''), None)
        if not val:
            return None
        values.append(val)
    return tuple(values) if len(values) > 1 else values[0]


# Leaf-key-name fragments that make a field a good business/identity key when
_GENERIC_KEY_FRAGMENTS = _fc._GENERIC_KEY_FRAGMENTS

# Explicit exception list: fields that should stay Non-Blocker even when
# genuinely missing (record-not-found) in the target/source system. Empty by
# default - see feature_config.IGNORABLE_MISSING_FIELDS for how to populate.
IGNORABLE_MISSING_FIELDS: List[str] = list(getattr(_fc, 'IGNORABLE_MISSING_FIELDS', []) or [])


def _is_ignorable_missing_field(*paths: str) -> bool:
    """True if ANY of `paths` (leaf field name or full pointer) matches an
    entry in IGNORABLE_MISSING_FIELDS (case-insensitive substring match)."""
    if not IGNORABLE_MISSING_FIELDS:
        return False
    haystacks = [str(p or '').lower() for p in paths]
    for needle in IGNORABLE_MISSING_FIELDS:
        n = str(needle).lower().strip()
        if n and any(n in h for h in haystacks):
            return True
    return False


def _derive_generic_key_specs(ppkg_flat: List[Dict[str, str]],
                              alex_flat: List[Dict[str, str]]) -> list:
    """Auto-derive an ordered list of single-field business keys for an array"""
    ppkg_keys: set = set()
    for f in ppkg_flat:
        ppkg_keys |= set(f.keys())
    alex_keys: set = set()
    for f in alex_flat:
        alex_keys |= set(f.keys())
    shared = ppkg_keys & alex_keys
    if not shared:
        return []

    specs: list = []
    # Highest-confidence: explicit BUSINESS_KEY_FIELDS present on both sides.
    for bk in BUSINESS_KEY_FIELDS:
        bl = bk.lower()
        for k in sorted(shared):
            if bl in k.lower() and k not in specs:
                specs.append(k)
    # Then any other identifier-like shared leaf key.
    for k in sorted(shared):
        kl = k.lower()
        if k not in specs and any(frag in kl for frag in _GENERIC_KEY_FRAGMENTS):
            specs.append(k)
    return specs


def _compute_array_alignment(
        ppkg_array: list,
        alex_array: list,
        key_specs: list
) -> Dict[int, int]:
    """PPKG is source of truth."""

    alignment: Dict[int, int] = {}

    if not isinstance(ppkg_array, list):
        return alignment

    if not isinstance(alex_array, list):
        return alignment

    ppkg_flat_records = [
        _flatten_leaf_values(x) if isinstance(x, dict) else {}
        for x in ppkg_array
    ]

    alex_flat_records = [
        _flatten_leaf_values(x) if isinstance(x, dict) else {}
        for x in alex_array
    ]

    # When the array container has NO explicit ARRAY_MATCH_CONFIG entry the
    if not key_specs:
        key_specs = _derive_generic_key_specs(ppkg_flat_records, alex_flat_records)

    used_alex_indexes: set = set()

    # Pass 1 - same-index fast path
    if key_specs:
        for i in range(min(len(ppkg_array), len(alex_array))):
            for spec in key_specs:
                p_key = _composite_key_lookup(ppkg_flat_records[i], spec)
                if p_key is None:
                    continue
                if _composite_key_lookup(alex_flat_records[i], spec) == p_key:
                    alignment[i] = i
                    used_alex_indexes.add(i)
                    break

    # Pass 2 - full-array business-key search (PPKG is source of truth)
    if key_specs:
        for ppkg_index, ppkg_flat in enumerate(ppkg_flat_records):
            if ppkg_index in alignment:
                continue
            matched_alex_index = None
            for spec in key_specs:
                source_key = _composite_key_lookup(ppkg_flat, spec)
                if source_key is None:
                    continue
                for alex_index, alex_flat in enumerate(alex_flat_records):
                    if alex_index in used_alex_indexes:
                        continue
                    if _composite_key_lookup(alex_flat, spec) == source_key:
                        matched_alex_index = alex_index
                        break
                if matched_alex_index is not None:
                    break
            if matched_alex_index is not None:
                alignment[ppkg_index] = matched_alex_index
                used_alex_indexes.add(matched_alex_index)

    # Pass 3 - positional fallback for records key-matching could NOT place
    for ppkg_index in range(len(ppkg_array)):
        if ppkg_index in alignment:
            continue
        if ppkg_index < len(alex_array) and ppkg_index not in used_alex_indexes:
            alignment[ppkg_index] = ppkg_index
            used_alex_indexes.add(ppkg_index)

    return alignment


def _get_alignment_map(
    ppkg_container_ptr: str,
    alex_container_ptr: str,
    config_wc: str,
    hcp_wrapped: dict,
    alex_wrapped: dict,
    alignment_cache: Dict[Tuple[str, str], Dict[int, int]],
    reverse: bool = False,
) -> Optional[Dict[int, int]]:
    """Return the {ppkg_index: alex_index} key-based alignment map for a specific,"""
    # Top-level claim array - index is resolved via ICN/claim matching
    if config_wc == 'claim' or '/' not in config_wc:
        return None
    key_specs = ARRAY_MATCH_CONFIG.get(config_wc)  # None -> generic auto-derived
    cache_key = (ppkg_container_ptr, alex_container_ptr)
    if cache_key not in alignment_cache:
        ppkg_array = _get_object_at_resolved_path(hcp_wrapped, ppkg_container_ptr)
        alex_array = _get_object_at_resolved_path(alex_wrapped, alex_container_ptr)
        alignment_cache[cache_key] = _compute_array_alignment(
            ppkg_array if isinstance(ppkg_array, list) else [],
            alex_array if isinstance(alex_array, list) else [],
            key_specs,
        )
    fmap = alignment_cache[cache_key]
    return {v: k for k, v in fmap.items()} if reverse else fmap


def _map_ptr_with_alignment(
    source_ptr: str,
    target_schema_parts: List[str],
    hcp_wrapped: dict,
    alex_wrapped: dict,
    alignment_cache: dict,
    use_reverse_map: bool,
) -> str:
    """Generic, key-based replacement for positional ("same index") pointer"""
    source_parts   = source_ptr.strip('/').split('/')
    source_indices = [p for p in source_parts if p.isdigit()]

    def _norm_root(parts: List[str]) -> str:
        # Both wrapped structures are rooted at "claim"; normalise a "data"
        if parts and parts[0] in ('claim', 'data'):
            return '/'.join(['claim'] + parts[1:])
        return '/'.join(parts)

    result: List[str] = []
    idx_cursor = 0
    for i, tp in enumerate(target_schema_parts):
        if tp == '*':
            if i < len(source_parts) and source_parts[i].isdigit():
                src_idx = int(source_parts[i])
            elif idx_cursor < len(source_indices):
                src_idx = int(source_indices[idx_cursor])
            else:
                src_idx = 0

            # Resolve BOTH sides' containers with their real parent indices.
            if use_reverse_map:
                alex_container_parts = source_parts[:i]
                ppkg_container_parts = result[:]
            else:
                ppkg_container_parts = source_parts[:i]
                alex_container_parts = result[:]

            ppkg_container_ptr = _norm_root(ppkg_container_parts)
            alex_container_ptr = _norm_root(alex_container_parts)
            # Config lookup is always keyed on the PPKG-side wildcard container.
            config_wc = '/'.join(
                '*' if p.isdigit() else p for p in ppkg_container_parts
            )
            if config_wc.split('/')[:1] == ['data']:
                config_wc = '/'.join(['claim'] + config_wc.split('/')[1:])

            fmap = _get_alignment_map(
                ppkg_container_ptr, alex_container_ptr, config_wc,
                hcp_wrapped, alex_wrapped, alignment_cache,
                reverse=use_reverse_map,
            )
            if fmap is None:
                use_idx = src_idx
            else:
                mapped = fmap.get(src_idx)
                if mapped is not None:
                    use_idx = mapped
                elif src_idx not in set(fmap.values()):
                    # No business-key counterpart was found, but this positional
                    use_idx = src_idx
                else:
                    use_idx = _NO_MATCH_INDEX
            result.append(str(use_idx))
            idx_cursor += 1
        else:
            result.append('claim' if (i == 0 and tp in ('claim', 'data')) else tp)
    if result and result[0] in ('claim', 'data'):
        result[0] = 'claim'
    return '/'.join(result)


def _last_array_element_pointer(resolved_ptr: str, min_pos: int = 2) -> Optional[Tuple[str, int, str]]:
    """Find the RIGHTMOST numeric path segment in `resolved_ptr` - i.e. the"""
    parts = resolved_ptr.strip('/').split('/')
    for i in range(len(parts) - 2, min_pos - 1, -1):
        if parts[i].isdigit():
            return '/'.join(parts[:i]), i, '/'.join(parts[i + 1:])
    return None


def _flatten_leaf_values(obj, prefix: str = '') -> Dict[str, str]:
    """Recursively flatten a dict/list into {leaf_key_name: normalized_value}."""
    out: Dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                out.update(_flatten_leaf_values(v, str(k)))
            else:
                nv = normalize_value(v)
                if nv != '':
                    out[str(k)] = nv
    elif isinstance(obj, list):
        for item in obj:
            out.update(_flatten_leaf_values(item, prefix))
    return out


def _find_matching_record_index(source_record, target_array: list, skip_idx=None) -> Optional[int]:
    """Given `source_record` (a dict with no counterpart at the SAME index in"""
    if not isinstance(source_record, dict) or not isinstance(target_array, list):
        return None
    src_flat = _flatten_leaf_values(source_record)
    for key in BUSINESS_KEY_FIELDS:
        key_l = key.lower()
        src_val = next(
            (v for k, v in src_flat.items() if key_l in k.lower() and v != ''), None
        )
        if not src_val:
            continue
        for idx, candidate in enumerate(target_array):
            if idx == skip_idx or not isinstance(candidate, dict):
                continue
            cand_flat = _flatten_leaf_values(candidate)
            for k, v in cand_flat.items():
                if key_l in k.lower() and v == src_val:
                    return idx
    return None


def _array_container_and_index(resolved_ptr: str) -> Optional[Tuple[str, int]]:
    """If `resolved_ptr` (e.g. 'claim/0/payments/1') ends in a numeric array"""
    if not resolved_ptr:
        return None
    parts = resolved_ptr.strip('/').split('/')
    if parts and parts[-1].isdigit():
        return '/'.join(parts[:-1]), int(parts[-1])
    return None


def _try_secondary_index_match(
    resolved_hcp_ptr: str,
    resolved_alex_ptr: str,
    hcp_wrapped: dict,
    alex_wrapped: dict,
    hcp_root: str,
    alex_root: str,
    hcp_val,
) -> Optional[Tuple[str, object, int, int]]:
    """Secondary Array Index Validation (cross-index search)."""
    hcp_info  = _last_array_element_pointer(resolved_hcp_ptr)
    alex_info = _last_array_element_pointer(resolved_alex_ptr)
    if hcp_info is None or alex_info is None:
        return None

    hcp_array_path, hcp_idx, _leaf_suffix_hcp = hcp_info
    alex_array_path, alex_idx, leaf_suffix    = alex_info

    hcp_record_ptr = f"{hcp_array_path}/{hcp_idx}"
    ppkg_record    = _get_object_at_resolved_path(hcp_wrapped, hcp_record_ptr)
    if not isinstance(ppkg_record, dict):
        return None

    alex_array = _get_object_at_resolved_path(alex_wrapped, alex_array_path)
    if not isinstance(alex_array, list) or len(alex_array) <= 1:
        return None

    found_idx = _find_matching_record_index(ppkg_record, alex_array, skip_idx=alex_idx)
    if found_idx is None or found_idx == alex_idx:
        return None

    new_leaf_ptr = f"{alex_array_path}/{found_idx}/{leaf_suffix}" if leaf_suffix else f"{alex_array_path}/{found_idx}"
    new_val = _get_object_at_resolved_path(alex_wrapped, new_leaf_ptr)
    if new_val is _MISSING:
        return None
    return new_leaf_ptr, new_val, found_idx, alex_idx


# Core comparison engine

def _index_tuple(ptr: str) -> Tuple[int, ...]:
    """Ordered tuple of the numeric array indices found in a resolved pointer."""
    return tuple(int(p) for p in ptr.strip('/').split('/') if p.isdigit())


def compare_direct(
    source_data: dict,
    target_data: dict,
    mapping: List[Tuple[str, str]],
    meta: dict,
    mapping_order_offset: int = 0,
) -> Tuple[List[dict], int, int]:
    """Generic, shape-agnostic comparison for two responses of the SAME schema.

    Unlike :func:`compare_claim_pair` (which is specialised for the PPKG-vs-Alex
    claim-array structure), this walks each mapped JSON pointer directly on the
    raw responses. Array elements are aligned by their index position (valid
    because both sides are the same API), so it works for any response shape
    (Claims360 B2B search, summary envelopes, ...). Rows use the same schema as
    :func:`_row`, so every downstream report sheet is produced unchanged.
    """
    rows: List[dict] = []
    total = 0
    matched = 0

    test_case         = meta.get('test_case', '')
    member_number     = meta.get('member_number', '')
    claim_number      = meta.get('claim_number', '')
    icn_number        = meta.get('icn_number', '')
    claim_transaction = meta.get('claim_transaction', '')
    claim_type        = meta.get('claim_type', '')

    def _emit(s_path, t_path, s_val, t_val, status, morder, s_idx='', t_idx=''):
        rows.append(_row(
            test_case, member_number, claim_number, icn_number,
            claim_type, claim_transaction,
            s_idx, t_idx, '', '',
            s_path, t_path,
            s_val, t_val, status,
            mapping_order=morder,
        ))

    for m_idx, (s_path, t_path) in enumerate(mapping):
        _morder  = mapping_order_offset + m_idx
        s_vals   = extract_values(source_data, wildcard_path(s_path))
        t_vals   = extract_values(target_data, wildcard_path(t_path))

        # Field absent on BOTH sides — log explicitly (single row).
        if not s_vals and not t_vals:
            _emit(
                '/' + s_path.lstrip('/') + ' (field absent in Source)',
                '/' + t_path.lstrip('/') + ' (field absent in Target)',
                '', '', 'Value Missing in Both', _morder,
            )
            total += 1
            continue

        t_by_idx: Dict[Tuple[int, ...], Tuple[str, object]] = {}
        for tp, tv in t_vals:
            t_by_idx.setdefault(_index_tuple(tp), (tp, tv))
        matched_targets: set = set()

        for sp, sv in s_vals:
            it       = _index_tuple(sp)
            s_idx    = str(it[0]) if it else ''
            r_s_path = '/' + sp.lstrip('/')
            match    = None
            if it in t_by_idx:
                match = t_by_idx[it]
                matched_targets.add(it)
            elif len(s_vals) == 1 and len(t_vals) == 1:
                # scalar (or single-element) field whose index differs
                match = t_vals[0]
                matched_targets.add(_index_tuple(t_vals[0][0]))

            if match is not None:
                tp, tv   = match
                t_idx    = str(_index_tuple(tp)[0]) if _index_tuple(tp) else ''
                is_match = values_match(sv, tv)
                status   = 'Match' if is_match else 'Mismatch'
                _emit(r_s_path, '/' + tp.lstrip('/'), sv, tv, status, _morder, s_idx, t_idx)
                matched += int(is_match)
            else:
                _emit(
                    r_s_path,
                    '/' + t_path.lstrip('/') + ' (field absent in Target)',
                    sv, '', 'Value Missing in Target', _morder, s_idx, s_idx,
                )
            total += 1

        # Target values with no source counterpart.
        for tp, tv in t_vals:
            it = _index_tuple(tp)
            if it in matched_targets:
                continue
            t_idx = str(it[0]) if it else ''
            _emit(
                '/' + s_path.lstrip('/') + ' (field absent in Source)',
                '/' + tp.lstrip('/'),
                '', tv, 'Value Missing in Source', _morder, t_idx, t_idx,
            )
            total += 1

    return rows, total, matched


def compare_claim_pair(
    hcp_data: dict,
    alex_data: dict,
    mapping: List[Tuple[str, str]],
    meta: dict,
    mapping_order_offset: int = 0,
) -> Tuple[List[dict], int, int]:
    """Compare one HCP vs Alex response per claim index."""
    hcp_wrapped, hcp_root   = wrap_response(hcp_data)
    alex_wrapped, alex_root = wrap_response(alex_data)

    rows:    List[dict] = []
    total   = 0
    matched = 0

    # Cache of the (expensive) found_idx lookup per (side, array_container_path,
    # missing_index, top_claim_idx). IMPORTANT: this is a lookup cache ONLY -
    # it does NOT suppress row emission. Every mapped field nested under a
    # missing array record still gets its own Validation Results row, so the
    # Validation Summary / Schema Coverage Analysis counts reconcile with the
    # actual number of affected fields instead of just the missing container.
    _missing_container_found_idx: Dict[tuple, Optional[int]] = {}

    # Key-based array-alignment cache - {(container_wc, claim_idx): {ppkg_idx:
    alignment_cache: Dict[Tuple[str, int], Dict[int, int]] = {}

    # PPKG is the source of truth. When a mapped field is absent in BOTH
    ppkg_claim_count = len(get_claims_list(hcp_data))
    alex_claim_count = len(get_claims_list(alex_data))

    claim_number      = meta.get('claim_number', '')
    icn_number        = meta.get('icn_number', '')
    claim_transaction = meta.get('claim_transaction', '')
    member_number     = meta.get('member_number', '')
    claim_type        = meta.get('claim_type', '')
    test_case         = meta.get('test_case', '')

    for mapping_idx, (hcp_path, alex_path) in enumerate(mapping):
        _morder   = mapping_order_offset + mapping_idx
        hcp_wild  = wildcard_path(hcp_path)
        alex_wild = wildcard_path(alex_path)

        # Meta path: compare directly against raw response root
        if hcp_wild.lstrip('/').startswith('meta/') or alex_wild.lstrip('/').startswith('meta/'):
            hcp_vals  = extract_values(hcp_data,  hcp_wild.lstrip('/'))
            alex_vals = extract_values(alex_data, alex_wild.lstrip('/'))
            if not hcp_vals and not alex_vals:
                continue
            for (h_ptr, h_val), (a_ptr, a_val) in zip(hcp_vals, alex_vals):
                is_match = values_match(h_val, a_val)
                status   = 'Match' if is_match else 'Mismatch'
                rows.append(_row(
                    test_case, member_number, claim_number, icn_number,
                    claim_type, claim_transaction,
                    '', '', '', '',
                    '/' + h_ptr.lstrip('/'), '/' + a_ptr.lstrip('/'),
                    h_val, a_val, status,
                    mapping_order=_morder,
                ))
                if is_match:
                    matched += 1
                total += 1
            continue

        hcp_vals  = extract_values(hcp_wrapped, hcp_wild)
        alex_vals = extract_values(alex_wrapped, alex_wild)

        if not hcp_vals and not alex_vals:
            # Field absent in BOTH PPKG and Alex - log explicitly (per claim)
            n = ppkg_claim_count or alex_claim_count
            idx_list = [str(i) for i in range(n)] if n > 0 else ['']
            for ci in idx_list:
                ci_int   = int(ci) if ci.isdigit() else -1
                ppkg_icn = get_claim_icn(hcp_data, ci_int)
                alex_icn = get_claim_icn(alex_data, ci_int)
                r_hcp    = with_claim_index(hcp_path, ci) if ci != '' else hcp_path
                r_alex   = with_claim_index(alex_path, ci) if ci != '' else alex_path
                rows.append(_row(
                    test_case, member_number, claim_number, icn_number,
                    claim_type, claim_transaction,
                    ci, ci, ppkg_icn, alex_icn,
                    r_hcp + ' (field absent in PPKG)',
                    r_alex + ' (field absent in Alex)',
                    '', '', 'Value Missing in Both',
                    mapping_order=_morder,
                ))
                total += 1
            continue

        # Summation support (per claim index)
        if '+' in alex_path and '+' not in hcp_path:
            alex_pointers = [p.strip() for p in alex_path.split('+')]

            alex_sum_by_idx:   Dict[str, float] = {}
            alex_parts_by_idx: Dict[str, list]  = {}
            alex_paths_by_idx: Dict[str, list]  = {}

            for ap in alex_pointers:
                for ptr, val in extract_values(alex_wrapped, wildcard_path(normalize_path(ap))):
                    idx = path_claim_index(ptr)
                    alex_sum_by_idx.setdefault(idx, 0.0)
                    alex_sum_by_idx[idx] += safe_float(val)
                    alex_parts_by_idx.setdefault(idx, []).append(safe_float(val))
                    alex_paths_by_idx.setdefault(idx, []).append(resolved_path_str(ptr, alex_root))

            for resolved_hcp_ptr, hcp_val in hcp_vals:
                ppkg_idx_str = path_claim_index(resolved_hcp_ptr)
                r_hcp_path   = resolved_path_str(resolved_hcp_ptr, hcp_root)
                ppkg_icn     = get_claim_icn(hcp_data, int(ppkg_idx_str) if ppkg_idx_str.isdigit() else -1)

                if ppkg_idx_str in alex_sum_by_idx:
                    alex_sum        = alex_sum_by_idx[ppkg_idx_str]
                    alex_parts_vals = alex_parts_by_idx[ppkg_idx_str]
                    alex_paths_list = alex_paths_by_idx[ppkg_idx_str]
                    alex_idx_str    = ppkg_idx_str
                    alex_icn        = get_claim_icn(alex_data, int(alex_idx_str) if alex_idx_str.isdigit() else -1)
                    hcp_float       = safe_float(hcp_val)
                    is_match        = abs(hcp_float - alex_sum) < 0.01
                    status          = 'Match' if is_match else 'Mismatch'
                    for alex_comp_path, alex_comp_val in zip(alex_paths_list, alex_parts_vals):
                        rows.append(_row(
                            test_case, member_number, claim_number, icn_number,
                            claim_type, claim_transaction,
                            ppkg_idx_str, alex_idx_str, ppkg_icn, alex_icn,
                            r_hcp_path, alex_comp_path,
                            f"{hcp_float:.2f}", f"{alex_comp_val:.2f}", status,
                            mapping_order=_morder,
                        ))
                    matched += int(is_match)
                else:
                    expected_alex_path = _build_resolved_alex_path(
                        resolved_hcp_ptr,
                        normalize_path(alex_path.split('+')[0].strip()),
                        alex_root,
                    )
                    rows.append(_row(
                        test_case, member_number, claim_number, icn_number,
                        claim_type, claim_transaction,
                        ppkg_idx_str, ppkg_idx_str,
                        ppkg_icn,
                        get_claim_icn(alex_data, int(ppkg_idx_str) if ppkg_idx_str.isdigit() else -1),
                        r_hcp_path, expected_alex_path + ' (field absent in Alex)',
                        f"{safe_float(hcp_val):.2f}", '', 'Value Missing in Target',
                        mapping_order=_morder,
                    ))
                total += 1

            # Alex has values for indices absent in PPKG
            hcp_group = _group_by_claim_index(hcp_vals)
            for alex_idx_str, alex_sum in alex_sum_by_idx.items():
                if alex_idx_str not in hcp_group:
                    alex_paths_list = alex_paths_by_idx[alex_idx_str]
                    alex_parts_list = alex_parts_by_idx[alex_idx_str]
                    alex_icn        = get_claim_icn(alex_data, int(alex_idx_str) if alex_idx_str.isdigit() else -1)
                    for alex_comp_path, alex_comp_val in zip(alex_paths_list, alex_parts_list):
                        rows.append(_row(
                            test_case, member_number, claim_number, icn_number,
                            claim_type, claim_transaction,
                            alex_idx_str, alex_idx_str, '', alex_icn,
                            hcp_path + ' (field absent in PPKG)', alex_comp_path,
                            '', f"{alex_comp_val:.2f}", 'Value Missing in Source',
                            mapping_order=_morder,
                        ))
                    total += 1
            continue

        # Direct comparison - matched by resolved path
        alex_schema_parts_direct = wildcard_path(alex_path).split('/')
        hcp_schema_parts_direct  = wildcard_path(hcp_path).split('/')

        def _alex_ptr_for_hcp_ptr(hcp_ptr: str) -> str:
            # KEY-BASED alignment first (requirements section 1-section 5): for any array
            return _map_ptr_with_alignment(
                hcp_ptr, alex_schema_parts_direct,
                hcp_wrapped, alex_wrapped, alignment_cache,
                use_reverse_map=False,
            )

        alex_by_ptr: Dict[str, Tuple] = {ptr.strip('/'): (ptr, val) for ptr, val in alex_vals}
        handled_alex_ptrs: set = set()

        for resolved_hcp_ptr, hcp_val in sorted(
            hcp_vals,
            key=lambda x: [int(p) if p.isdigit() else p for p in x[0].strip('/').split('/')],
        ):
            expected_alex_ptr = _alex_ptr_for_hcp_ptr(resolved_hcp_ptr)
            claim_idx  = path_claim_index(resolved_hcp_ptr)
            ppkg_icn   = get_claim_icn(hcp_data, int(claim_idx) if claim_idx.isdigit() else -1)
            alex_icn   = get_claim_icn(alex_data, int(claim_idx) if claim_idx.isdigit() else -1)
            r_hcp_path = resolved_path_str(resolved_hcp_ptr, hcp_root)

            if expected_alex_ptr in alex_by_ptr:
                resolved_alex_ptr, alex_val = alex_by_ptr[expected_alex_ptr]
                handled_alex_ptrs.add(expected_alex_ptr)
                r_alex_path = resolved_path_str(resolved_alex_ptr, alex_root)
                is_match    = values_match(hcp_val, alex_val)

                if not is_match:
                    # Secondary Array Index Validation
                    _remap = _try_secondary_index_match(
                        resolved_hcp_ptr, resolved_alex_ptr, hcp_wrapped, alex_wrapped,
                        hcp_root, alex_root, hcp_val,
                    )
                    if _remap is not None:
                        new_alex_ptr, new_alex_val, found_idx, expected_idx = _remap
                        handled_alex_ptrs.add(new_alex_ptr.strip('/'))
                        r_alex_path = resolved_path_str(new_alex_ptr, alex_root)
                        is_match2   = values_match(hcp_val, new_alex_val)
                        status2     = 'Match' if is_match2 else 'Mismatch'
                        remap_row   = _row(
                            test_case, member_number, claim_number, icn_number,
                            claim_type, claim_transaction,
                            claim_idx, claim_idx, ppkg_icn, alex_icn,
                            r_hcp_path, r_alex_path,
                            hcp_val, new_alex_val, status2,
                            mapping_order=_morder,
                        )
                        remap_row['Category']   = 'Index Difference'
                        remap_row['Severity']   = 'Non-Blocker'
                        remap_row['Conclusion'] = (
                            'Record exists in both systems. Array index differs. '
                            f'PPKG Index = {expected_idx}, Alex Index = {found_idx}.'
                            + ('' if is_match2 else ' Value also differs after remap - verify manually.')
                        )
                        rows.append(remap_row)
                        if is_match2:
                            matched += 1
                        total += 1
                        continue

                status = 'Match' if is_match else 'Mismatch'
                rows.append(_row(
                    test_case, member_number, claim_number, icn_number,
                    claim_type, claim_transaction,
                    claim_idx, claim_idx, ppkg_icn, alex_icn,
                    r_hcp_path, r_alex_path,
                    hcp_val, alex_val, status,
                    mapping_order=_morder,
                ))
                if is_match:
                    matched += 1
            else:
                # TRUE index-based array-record validation
                _parent_ptr    = _parent_pointer(expected_alex_ptr)
                _parent_obj    = _get_object_at_resolved_path(alex_wrapped, _parent_ptr)
                _array_info    = _array_container_and_index(_parent_ptr)

                if _parent_obj is _MISSING and _array_info is not None:
                    array_path, missing_idx = _array_info
                    root_cause_key = ('alex', array_path, missing_idx, claim_idx)

                    # Look up (and cache) whether the PPKG record exists
                    # elsewhere in the Alex array - the expensive full-array
                    # search only needs to run ONCE per missing container,
                    # even though every mapped field below re-uses the result.
                    if root_cause_key not in _missing_container_found_idx:
                        ppkg_record_ptr = _parent_pointer(resolved_hcp_ptr)
                        ppkg_record     = _get_object_at_resolved_path(hcp_wrapped, ppkg_record_ptr)
                        alex_array      = _get_object_at_resolved_path(alex_wrapped, array_path)
                        _missing_container_found_idx[root_cause_key] = (
                            _find_matching_record_index(ppkg_record, alex_array)
                            if isinstance(alex_array, list) else None
                        )
                    found_idx = _missing_container_found_idx[root_cause_key]

                    # Emit ONE row per affected mapped field (not one per
                    # missing container) so downstream counts (Validation
                    # Summary, Schema Coverage Analysis) reconcile with the
                    # actual number of missing fields.
                    field_row = _row(
                        test_case, member_number, claim_number, icn_number,
                        claim_type, claim_transaction,
                        claim_idx, claim_idx, ppkg_icn, alex_icn,
                        r_hcp_path,
                        resolved_path_str(_parent_ptr, alex_root) + ' (record absent in Alex)',
                        hcp_val, '', 'Value Missing in Target',
                        mapping_order=_morder,
                    )
                    if found_idx is not None:
                        field_row['Category']   = 'Record Found At Different Index'
                        field_row['Severity']   = 'Non-Blocker'
                        field_row['Conclusion'] = (
                            'Record exists in both systems but appears at different '
                            f'array positions. PPKG Index: {missing_idx}, Alex Index: '
                            f'{found_idx}. This is an index/record alignment issue, '
                            'not a missing field.'
                        )
                    elif _is_ignorable_missing_field(r_hcp_path, field_row.get('Normalized Pointer', '')):
                        field_row['Category']   = 'Missing Record At Index (Ignored)'
                        field_row['Severity']   = 'Non-Blocker'
                        field_row['Conclusion'] = (
                            f'Record not found in Alex at index {missing_idx}. Field is on '
                            'the explicit ignore list (IGNORABLE_MISSING_FIELDS) - treated '
                            'as Non-Blocker.'
                        )
                    else:
                        # Field present in PPKG (source of truth); the entire containing
                        # record is genuinely absent in Alex at every index - this is a
                        # real missing-field defect and must count as a Blocker.
                        field_row['Category']   = 'Missing In Alex (True Missing)'
                        field_row['Severity']   = 'Blocker'
                        field_row['Conclusion'] = (
                            f'Field present in PPKG, missing in Alex. Record not found in '
                            f'Alex at index {missing_idx} (array cardinality differs '
                            'between systems).'
                        )
                    field_row['Parent Alignment Issue'] = 'Y'
                    field_row['Root Cause Path'] = resolved_path_str(_parent_ptr, alex_root)
                    rows.append(field_row)
                    total += 1
                    continue

                expected_alex_path = _build_resolved_alex_path(resolved_hcp_ptr, alex_path, alex_root)
                new_row = _row(
                    test_case, member_number, claim_number, icn_number,
                    claim_type, claim_transaction,
                    claim_idx, claim_idx, ppkg_icn, alex_icn,
                    expected_alex_path + ' (field absent in Alex)',
                    r_hcp_path,
                    hcp_val, '', 'Value Missing in Target',
                    mapping_order=_morder,
                )
                # Inherit the PARENT record's classification (empty placeholder object, or a missing non-array object key)
                _override = classify_missing_leaf_via_parent(_parent_obj, 'Alex')
                if _override:
                    new_row['Severity'], new_row['Conclusion'], new_row['Category'] = _override
                    # Tag this leaf as a suppressed child of a single parent
                    new_row['Parent Alignment Issue'] = 'Y'
                    new_row['Root Cause Path'] = resolved_path_str(_parent_ptr, alex_root)
                rows.append(new_row)
            total += 1

        # Alex entries with no PPKG counterpart
        for ptr, val in sorted(
            alex_vals,
            key=lambda x: [int(p) if p.isdigit() else p for p in x[0].strip('/').split('/')],
        ):
            if ptr.strip('/') in handled_alex_ptrs:
                continue
            r_alex_path        = resolved_path_str(ptr, alex_root)
            claim_idx          = path_claim_index(ptr)
            ppkg_icn           = get_claim_icn(hcp_data, int(claim_idx) if claim_idx.isdigit() else -1)
            alex_icn           = get_claim_icn(alex_data, int(claim_idx) if claim_idx.isdigit() else -1)
            # KEY-BASED alignment first (requirements section 1-section 5): resolve the
            expected_ppkg_ptr  = _map_ptr_with_alignment(
                ptr, hcp_schema_parts_direct, hcp_wrapped, alex_wrapped,
                alignment_cache, use_reverse_map=True,
            )
            expected_ppkg_path = resolved_path_str(expected_ppkg_ptr, hcp_root)

            # TRUE index-based array-record validation (Alex->PPKG side)
            _parent_ptr_ppkg = _reroot_to_claim(_parent_pointer(expected_ppkg_path), hcp_root)
            _parent_obj      = _get_object_at_resolved_path(hcp_wrapped, _parent_ptr_ppkg)
            _array_info      = _array_container_and_index(_parent_ptr_ppkg)

            if _parent_obj is _MISSING and _array_info is not None:
                array_path, missing_idx = _array_info
                root_cause_key = ('ppkg', array_path, missing_idx, claim_idx)

                # Look up (and cache) whether the Alex record exists elsewhere
                # in the PPKG array - the expensive full-array search only
                # needs to run ONCE per missing container.
                if root_cause_key not in _missing_container_found_idx:
                    alex_record_ptr = _parent_pointer(ptr)
                    alex_record     = _get_object_at_resolved_path(alex_wrapped, alex_record_ptr)
                    ppkg_array      = _get_object_at_resolved_path(hcp_wrapped, array_path)
                    _missing_container_found_idx[root_cause_key] = (
                        _find_matching_record_index(alex_record, ppkg_array)
                        if isinstance(ppkg_array, list) else None
                    )
                found_idx = _missing_container_found_idx[root_cause_key]

                # Emit ONE row per affected mapped field (not one per missing
                # container) so downstream counts reconcile with the actual
                # number of missing fields.
                field_row = _row(
                    test_case, member_number, claim_number, icn_number,
                    claim_type, claim_transaction,
                    claim_idx, claim_idx, ppkg_icn, alex_icn,
                    expected_ppkg_path + ' (record absent in PPKG)',
                    r_alex_path,
                    '', val, 'Value Missing in Source',
                    mapping_order=_morder,
                )
                if found_idx is not None:
                    field_row['Category']   = 'Record Found At Different Index'
                    field_row['Severity']   = 'Non-Blocker'
                    field_row['Conclusion'] = (
                        'Record exists in both systems but appears at different '
                        f'array positions. PPKG Index: {found_idx}, Alex Index: '
                        f'{missing_idx}. This is an index/record alignment issue, '
                        'not a missing field.'
                    )
                elif _is_ignorable_missing_field(r_alex_path, field_row.get('Normalized Pointer', '')):
                    field_row['Category']   = 'Missing Record At Index (Ignored)'
                    field_row['Severity']   = 'Non-Blocker'
                    field_row['Conclusion'] = (
                        f'Record not found in PPKG at index {missing_idx}. Field is on '
                        'the explicit ignore list (IGNORABLE_MISSING_FIELDS) - treated '
                        'as Non-Blocker.'
                    )
                else:
                    # Field present in Alex; the entire containing record is genuinely
                    # absent in PPKG at every index - a real defect worth flagging,
                    # counted the same way "Missing In PPKG (True Missing)" rows are.
                    field_row['Category']   = 'Missing In PPKG (True Missing)'
                    field_row['Severity']   = 'Blocker'
                    field_row['Conclusion'] = (
                        f'Field present in Alex, missing in PPKG. Record not found in '
                        f'PPKG at index {missing_idx} (array cardinality differs '
                        'between systems).'
                    )
                field_row['Parent Alignment Issue'] = 'Y'
                field_row['Root Cause Path'] = resolved_path_str(_parent_ptr_ppkg, hcp_root)
                rows.append(field_row)
                total += 1
                continue

            new_row = _row(
                test_case, member_number, claim_number, icn_number,
                claim_type, claim_transaction,
                claim_idx, claim_idx, ppkg_icn, alex_icn,
                expected_ppkg_path + ' (field absent in PPKG)', r_alex_path,
                '', val, 'Value Missing in Source',
                mapping_order=_morder,
            )
            # Inherit the PARENT record's classification (empty placeholder /
            _override = classify_missing_leaf_via_parent(_parent_obj, 'PPKG')
            if _override:
                new_row['Severity'], new_row['Conclusion'], new_row['Category'] = _override
                # Tag this leaf as a suppressed child of a single parent
                new_row['Parent Alignment Issue'] = 'Y'
                new_row['Root Cause Path'] = resolved_path_str(_parent_ptr_ppkg, hcp_root)
            rows.append(new_row)
            total += 1

    # Final safety sweep - the internal out-of-range sentinel index
    _sentinel = str(_NO_MATCH_INDEX)
    for r in rows:
        rcp = r.get('Root Cause Path', '')
        if rcp and _sentinel in rcp:
            r['Root Cause Path'] = _desentinel_pointer(
                rcp, r.get('AlexPath', '') or r.get('PPKGPath', ''))
        concl = r.get('Conclusion', '')
        if concl and _sentinel in concl:
            real_idx = ''
            for p in (r.get('PPKGPath', ''), r.get('AlexPath', '')):
                for seg in str(p).partition(' ')[0].split('/'):
                    if seg.isdigit() and seg != _sentinel:
                        real_idx = seg
                if real_idx:
                    break
            r['Conclusion'] = concl.replace(
                'at index ' + _sentinel,
                ('at index ' + real_idx) if real_idx else 'beyond the array bounds')
            r['Conclusion'] = r['Conclusion'].replace(_sentinel, real_idx or '')

    return rows, total, matched


# Record Matching engine (PPKG record <-> Alex record, business-key based)

RECORD_MATCH_COLUMNS = [
    'Test Case', 'Member Number', 'Claim Number', 'ICN Number', 'Claim Type',
    'Array Container', 'PPKG Index', 'Alex Index', 'Match Status',
    'Business Key', 'Detail',
]

# Ordered record-level match statuses (also drives Excel cell colouring).
RECORD_MATCH_STATUSES = (
    'Exact Match',             # same business record, same array index
    'Index Difference Match',  # same business record, different array index
    'Missing In Alex',         # PPKG record with no counterpart anywhere in Alex
    'Missing In PPKG',         # Alex record with no counterpart anywhere in PPKG
)


def _collect_top_level_array_containers(wrapped: dict) -> set:
    """Return the set of RESOLVED container pointers (real indices, e.g."""
    out: set = set()

    def walk(obj, path: str):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{path}/{k}")
        elif isinstance(obj, list):
            p = path.strip('/')
            if p and p != 'claim' and any(isinstance(x, dict) for x in obj):
                if sum(1 for seg in p.split('/') if seg.isdigit()) == 1:
                    out.add(p)
            for i, x in enumerate(obj):
                walk(x, f"{path}/{i}")

    walk(wrapped, '')
    return out


def _spec_label(spec) -> str:
    """Human-readable label for a business-key spec (str or tuple of fields)."""
    if isinstance(spec, (tuple, list)):
        return ' + '.join(str(s) for s in spec)
    return str(spec)


def build_record_matching(hcp_data: dict, alex_data: dict, meta: dict) -> List[dict]:
    """Build the Record Matching rows for one claim pair."""
    hcp_wrapped, _hcp_root   = wrap_response(hcp_data)
    alex_wrapped, _alex_root = wrap_response(alex_data)

    test_case     = meta.get('test_case', '')
    member_number = meta.get('member_number', '')
    claim_number  = meta.get('claim_number', '')
    icn_number    = meta.get('icn_number', '')
    claim_type    = meta.get('claim_type', '')

    container_ptrs = (
        _collect_top_level_array_containers(hcp_wrapped)
        | _collect_top_level_array_containers(alex_wrapped)
    )

    rows: List[dict] = []

    def _sort_key(ptr: str):
        parts   = ptr.strip('/').split('/')
        claim_i = next((int(s) for s in parts if s.isdigit()), 0)
        return (claim_i, wildcard_path(ptr))

    for ptr in sorted(container_ptrs, key=_sort_key):
        container_wc = wildcard_path(ptr)

        ppkg_array = _get_object_at_resolved_path(hcp_wrapped,  ptr)
        alex_array = _get_object_at_resolved_path(alex_wrapped, ptr)
        ppkg_array = ppkg_array if isinstance(ppkg_array, list) else []
        alex_array = alex_array if isinstance(alex_array, list) else []
        if not ppkg_array and not alex_array:
            continue

        key_specs = ARRAY_MATCH_CONFIG.get(container_wc)
        if key_specs:
            key_label = ' | '.join(_spec_label(s) for s in key_specs)
        else:
            ppkg_flat = [_flatten_leaf_values(r) if isinstance(r, dict) else {} for r in ppkg_array]
            alex_flat = [_flatten_leaf_values(r) if isinstance(r, dict) else {} for r in alex_array]
            derived   = _derive_generic_key_specs(ppkg_flat, alex_flat)
            key_label = (' | '.join(_spec_label(s) for s in derived)
                         if derived else 'position (no business key available)')

        fmap         = _compute_array_alignment(ppkg_array, alex_array, key_specs)
        matched_alex = set(fmap.values())

        def _emit(ppkg_idx, alex_idx, status, detail):
            rows.append({
                'Test Case':       test_case,
                'Member Number':   member_number,
                'Claim Number':    claim_number,
                'ICN Number':      icn_number,
                'Claim Type':      claim_type,
                'Array Container': '/' + container_wc,
                'PPKG Index':      ppkg_idx,
                'Alex Index':      alex_idx,
                'Match Status':    status,
                'Business Key':    key_label,
                'Detail':          detail,
            })

        # PPKG is the source of truth - one row per PPKG record.
        for i in range(len(ppkg_array)):
            if i in fmap:
                j = fmap[i]
                if i == j:
                    _emit(i, j, 'Exact Match',
                          'Business record present at the same array index in both systems.')
                else:
                    _emit(i, j, 'Index Difference Match',
                          f'Same business record; PPKG index {i} maps to Alex index {j}.')
            else:
                _emit(i, '', 'Missing In Alex',
                      f'PPKG record at index {i} has no matching record anywhere in the Alex array.')

        # Alex records never matched to any PPKG record.
        for j in range(len(alex_array)):
            if j not in matched_alex:
                _emit('', j, 'Missing In PPKG',
                      f'Alex record at index {j} has no matching record anywhere in the PPKG array.')

    return rows


# Excel report writer - 5 sheets

def _blocker_category_label(category: str) -> str:
    """Reviewer-friendly label for a Blocker-severity Category, used in the"""
    return {
        'Missing In Alex (True Missing)': 'Missing In Target',
        'Missing In PPKG (True Missing)': 'Missing In Source',
    }.get(category, category or 'Other')


DUPLICATE_RECORDS_COLUMNS = [
    'Test Case', 'Claim Number', 'ICN', 'First Seen Test Case',
    'Occurrence', 'Validated',
]


def build_summary_blocks(
    consolidated_df: pd.DataFrame,
    duplicate_rows: Optional[List[dict]] = None,
) -> List[Tuple[str, pd.DataFrame]]:
    """Build the business-focused Summary sheet as an ordered list of"""
    blocks: List[Tuple[str, pd.DataFrame]] = []

    claim_cols   = ['Test Case', 'Claim Number', 'ICN Number']
    display_cols = ['Test Case', 'Claim Number', 'ICN']

    def _duplicate_blocks() -> List[Tuple[str, pd.DataFrame]]:
        """Duplicate-claim visibility: a count row + the full detail table."""
        dup_df = (
            pd.DataFrame(duplicate_rows, columns=DUPLICATE_RECORDS_COLUMNS)
            if duplicate_rows else pd.DataFrame(columns=DUPLICATE_RECORDS_COLUMNS)
        )
        validated   = int((dup_df['Validated'] == 'Yes').sum()) if not dup_df.empty else 0
        skipped     = int((dup_df['Validated'] == 'No').sum()) if not dup_df.empty else 0
        overview = pd.DataFrame([
            ('Duplicate Claims Detected',        len(dup_df)),
            ('Duplicates Still Validated',       validated),
            ('Duplicates Skipped (exact repeat)', skipped),
        ], columns=['Metric', 'Count'])
        return [
            ('Duplicate Records Overview', overview),
            ('Duplicate Records', dup_df),
        ]

    if consolidated_df is None or consolidated_df.empty:
        exec_df = pd.DataFrame([
            ('Total Claims Processed', 0), ('Total Fields Compared', 0),
            ('Total Matches', 0), ('Total Blockers', 0),
            ('Total Non-Blockers', 0), ('Coverage %', '0.00%'),
        ], columns=['Metric', 'Count'])
        blocks.append(('Executive Summary', exec_df))
        blocks.extend(_duplicate_blocks())
        return blocks

    df = consolidated_df
    total_rows = len(df)
    match_rows = int((df['Match Status'] == 'Match').sum())
    blocker_df = df[df['Severity'] == 'Blocker']
    blocker_total     = len(blocker_df)
    non_blocker_total = total_rows - blocker_total
    coverage_pct = (match_rows / total_rows * 100) if total_rows else 0.0

    # Claim Coverage Summary - per-claim Fields Compared / Matches /
    cov_group_cols = ['Test Case', 'Claim Number', 'ICN Number', 'ClaimTransaction']
    tmp = df[cov_group_cols + ['Match Status', 'Severity']].copy()
    tmp['_is_match']   = (tmp['Match Status'] == 'Match').astype(int)
    tmp['_is_blocker'] = (tmp['Severity'] == 'Blocker').astype(int)
    claim_coverage = (
        tmp.groupby(cov_group_cols, dropna=False)
        .agg(**{
            'Fields Compared': ('_is_match', 'size'),
            'Matches':         ('_is_match', 'sum'),
            'Blockers':        ('_is_blocker', 'sum'),
        })
        .reset_index()
        .rename(columns={'ICN Number': 'ICN', 'ClaimTransaction': 'Claim Transaction'})
    )
    claim_coverage['Coverage %'] = claim_coverage.apply(
        lambda r: f"{(r['Matches'] / r['Fields Compared'] * 100):.2f}%" if r['Fields Compared'] > 0 else 'N/A',
        axis=1,
    )
    claim_coverage = claim_coverage.sort_values(
        by=['Blockers', 'Test Case', 'Claim Number'], ascending=[False, True, True]
    ).reset_index(drop=True)
    claim_coverage = claim_coverage[
        ['Test Case', 'Claim Number', 'ICN', 'Claim Transaction',
         'Fields Compared', 'Matches', 'Blockers', 'Coverage %']
    ]

    # 1. Executive Summary
    exec_df = pd.DataFrame([
        ('Total Claims Processed', len(claim_coverage)),
        ('Total Fields Compared',  total_rows),
        ('Total Matches',          match_rows),
        ('Total Blockers',         blocker_total),
        ('Total Non-Blockers',     non_blocker_total),
        ('Duplicate Claims',       len(duplicate_rows or [])),
        ('Coverage %',             f"{coverage_pct:.2f}%"),
    ], columns=['Metric', 'Count'])
    blocks.append(('Executive Summary', exec_df))

    # 1b. Duplicate Records - overview + full detail table
    blocks.extend(_duplicate_blocks())

    # 2. Blocker Breakdown - sums EXACTLY to Total Blockers
    if not blocker_df.empty:
        bd = blocker_df['Category'].apply(_blocker_category_label).value_counts().reset_index()
        bd.columns = ['Category', 'Count']
        bd = bd.sort_values('Count', ascending=False).reset_index(drop=True)
    else:
        bd = pd.DataFrame(columns=['Category', 'Count'])
    bd = pd.concat(
        [bd, pd.DataFrame([{'Category': 'Total Blockers', 'Count': blocker_total}])],
        ignore_index=True,
    )
    blocks.append(('Blocker Breakdown', bd))

    # 3. Claim Coverage Summary
    blocks.append(('Claim Coverage Summary', claim_coverage))

    # 4. Top Failure Areas - Json Schema paths with the most Blocker rows,
    fail_key_cols = ['Json Schema'] + claim_cols
    if not blocker_df.empty:
        top_fail = (
            blocker_df.loc[blocker_df['Json Schema'] != '', fail_key_cols]
            .groupby(fail_key_cols, dropna=False)
            .size()
            .reset_index(name='Blockers')
            .rename(columns={'ICN Number': 'ICN'})
        )
        top_fail = top_fail.sort_values(
            by=['Blockers', 'Json Schema'], ascending=[False, True]
        ).head(20).reset_index(drop=True)
        top_fail = top_fail[['Json Schema'] + display_cols + ['Blockers']]
    else:
        top_fail = pd.DataFrame(columns=['Json Schema'] + display_cols + ['Blockers'])
    blocks.append(('Top Failure Areas', top_fail))

    # 5. Missing Field Summary - Json Schema AND the claim each occurrence
    def _missing_block(category: str) -> pd.DataFrame:
        sub = df[df['Category'] == category]
        out_cols = ['Json Schema'] + display_cols + ['Count']
        if sub.empty:
            out = pd.DataFrame(columns=out_cols)
        else:
            out = (
                sub.loc[:, fail_key_cols]
                .groupby(fail_key_cols, dropna=False)
                .size()
                .reset_index(name='Count')
                .rename(columns={'ICN Number': 'ICN'})
            )
            out = out.sort_values(
                by=['Count', 'Json Schema'], ascending=[False, True]
            ).reset_index(drop=True)
            out = out[out_cols]
        total = int(out['Count'].sum()) if not out.empty else 0
        total_row = pd.DataFrame([{
            'Json Schema': f'Total ({total} Blockers)',
            'Test Case': '', 'Claim Number': '', 'ICN': '', 'Count': total,
        }])
        return pd.concat([out, total_row], ignore_index=True)

    blocks.append(('Missing Field Summary - Missing In Target',
                   _missing_block('Missing In Alex (True Missing)')))
    blocks.append(('Missing Field Summary - Missing In Source',
                   _missing_block('Missing In PPKG (True Missing)')))

    # 6. Failure Distribution by Claim - WHY each claim has blockers
    failure_dist = claim_coverage[['Test Case', 'Claim Number', 'ICN']].copy()
    known_categories = ['Data Mismatch', 'Missing In Target', 'Missing In Source']
    if not blocker_df.empty:
        fd = blocker_df.copy()
        fd['_label'] = fd['Category'].apply(_blocker_category_label)
        fd_pivot = (
            fd.groupby(claim_cols + ['_label'], dropna=False)
            .size()
            .reset_index(name='Count')
            .rename(columns={'ICN Number': 'ICN'})
            .pivot_table(index=display_cols, columns='_label', values='Count', fill_value=0)
            .reset_index()
        )
    else:
        fd_pivot = pd.DataFrame(columns=display_cols)

    failure_dist = failure_dist.merge(fd_pivot, on=display_cols, how='left')
    # Ensure all 3 known category columns exist even when the current run has
    for col in known_categories:
        if col not in failure_dist.columns:
            failure_dist[col] = 0
    # Any Blocker category beyond the 3 known ones (e.g. future additions)
    extra_categories = [
        c for c in failure_dist.columns
        if c not in display_cols + known_categories
    ]
    for col in known_categories + extra_categories:
        failure_dist[col] = failure_dist[col].fillna(0).astype(int)
    count_cols = known_categories + extra_categories
    failure_dist['Total Blockers'] = failure_dist[count_cols].sum(axis=1)
    failure_dist = failure_dist[display_cols + count_cols + ['Total Blockers']]
    failure_dist = failure_dist.sort_values(
        by=['Total Blockers', 'Test Case', 'Claim Number'], ascending=[False, True, True]
    ).reset_index(drop=True)
    blocks.append(('Failure Distribution by Claim', failure_dist))

    return blocks


# Generic, system-agnostic report headers. The actual systems being compared
# (source vs target) are already stated in the report file name and on the
# "Run Information" sheet, so the data sheets themselves stay generic - no
# hardcoded 'PPKG' / 'Alex' names leak into any report column. This is a pure
# display-layer rename applied at write time; the in-memory frames keep their
# raw keys so all internal logic is untouched.
REPORT_COLUMN_RENAME = {
    'PPKG Claim Index':        'Source Claim Index',
    'Alex Claim Index':        'Target Claim Index',
    'PPKG ICN':                'Source ICN',
    'Alex ICN':                'Target ICN',
    'PPKG TxnId':              'Source TxnId',
    'Alex TxnId':              'Target TxnId',
    'PPKG TxnType':            'Source TxnType',
    'Alex TxnType':            'Target TxnType',
    'PPKGPath':                'Source Path',
    'AlexPath':                'Target Path',
    'PPKGValue':               'Source Value',
    'AlexValue':               'Target Value',
    'PPKG Schema Pointer':     'Source Schema Pointer',
    'Alex Schema Pointer':     'Target Schema Pointer',
    'Present In PPKG Schema':  'Present In Source Schema',
    'Present In Alex Schema':  'Present In Target Schema',
    'PPKG Response Available': 'Source Response Available',
    'Alex Response Available': 'Target Response Available',
    'Present In PPKG Response': 'Present In Source Response',
    'Present In Alex Response': 'Present In Target Response',
    'PPKG Index':              'Source Index',
    'Alex Index':              'Target Index',
    'PPKG Field Path':         'Source Field Path',
}


def _to_generic_report_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with report columns renamed to generic
    Source/Target headers (only columns present are affected)."""
    if df is None:
        return df
    return df.rename(columns=REPORT_COLUMN_RENAME)


def write_excel_report(
    output_path: str,
    summary_blocks: List[Tuple[str, pd.DataFrame]],
    consolidated_df: pd.DataFrame,
    claim_match_df: pd.DataFrame,
    missing_records_df: pd.DataFrame,
    schema_df: pd.DataFrame,
    stats_df: pd.DataFrame,
) -> None:
    """Write the formatted multi-sheet Excel report."""
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    HEADER_FILL   = PatternFill("solid", fgColor="1F4E79")
    HEADER_FONT   = Font(color="FFFFFF", bold=True)
    MATCH_FILL    = PatternFill("solid", fgColor="C6EFCE")   # green
    MISMATCH_FILL = PatternFill("solid", fgColor="FFC7CE")   # red
    MISSING_FILL  = PatternFill("solid", fgColor="FFEB9C")   # amber
    ALT_FILL      = PatternFill("solid", fgColor="EBF3FB")
    TITLE_FILL    = PatternFill("solid", fgColor="1F4E79")
    TOTAL_FILL    = PatternFill("solid", fgColor="D9E2F3")
    THIN_BORDER   = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'),  bottom=Side(style='thin'),
    )

    def _style_header(cell):
        cell.fill      = HEADER_FILL
        cell.font      = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border    = THIN_BORDER

    def _fill_for(status_val) -> Optional[object]:
        sv = str(status_val or '').strip().upper()
        if sv in ('MATCH', 'MATCHED', 'NON-BLOCKER') or sv == 'MAPPED AND PRESENT':
            return MATCH_FILL
        if sv == 'BLOCKER' or 'MISMATCH' in sv:
            return MISMATCH_FILL
        # Genuine, confirmed gaps - checked BEFORE the generic 'MISSING'
        if 'TRUE MISSING' in sv:
            return MISMATCH_FILL
        # Informational-only categories: the field genuinely exists on the
        if 'RECORD ALIGNMENT' in sv or sv.startswith('EMPTY RECORD') or sv == 'ALEX ONLY FIELD':
            return MISSING_FILL
        if 'AVAILABLE' in sv and 'ONLY' in sv:
            return MISSING_FILL
        if 'MISSING' in sv or 'NOT_FOUND' in sv or 'NOT FOUND' in sv or 'INVALID' in sv or 'FAILED' in sv:
            return MISSING_FILL
        return None

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Summary sheet: one titled, business-focused table per block
        cursor = 0
        block_meta: List[Tuple[str, int, int, int, int]] = []  # (title, title_row0, header_row0, n_rows, n_cols)
        for title, block_df in summary_blocks:
            block_df = _to_generic_report_columns(block_df)
            header_start = cursor + 1   # 0-indexed startrow for to_excel's own header
            block_df.to_excel(writer, sheet_name='Summary', index=False, startrow=header_start)
            block_meta.append((title, cursor, header_start, len(block_df), max(len(block_df.columns), 1)))
            cursor = header_start + len(block_df) + 2   # +1 blank spacer row before next title

        _to_generic_report_columns(consolidated_df).to_excel(writer,    sheet_name='Validation Results',      index=False)
        _to_generic_report_columns(claim_match_df).to_excel(writer,     sheet_name='Claim Match Summary',     index=False)
        _to_generic_report_columns(missing_records_df).to_excel(writer, sheet_name='Missing Records',         index=False)
        _to_generic_report_columns(schema_df).to_excel(writer,          sheet_name='Schema Coverage Analysis', index=False)
        _to_generic_report_columns(stats_df).to_excel(writer,           sheet_name='Stats By Element',        index=False)

        wb = writer.book

        def _format_sheet(ws, highlight_col: Optional[str] = None, header_row: int = 1):
            for cell in ws[header_row]:
                _style_header(cell)

            match_col_idx = None
            if highlight_col:
                for idx, cell in enumerate(ws[header_row], start=1):
                    if cell.value == highlight_col:
                        match_col_idx = idx
                        break

            for row_idx, row in enumerate(ws.iter_rows(min_row=header_row + 1), start=header_row + 1):
                is_alt = (row_idx % 2 == 0)
                for cell in row:
                    cell.alignment = Alignment(vertical='center', wrap_text=False)
                    cell.border    = THIN_BORDER
                    if (not cell.fill or cell.fill.patternType in (None, 'none')) and is_alt:
                        cell.fill = ALT_FILL

                if match_col_idx:
                    fill = _fill_for(ws.cell(row=row_idx, column=match_col_idx).value)
                    if fill:
                        for cell in row:
                            cell.fill = fill

            for col in ws.columns:
                max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col)
                ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 70)

            ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

        # Custom formatting for the multi-block, business-focused Summary
        ws_sum = wb['Summary']
        for title, title_row0, header_row0, n_rows, n_cols in block_meta:
            title_excel_row = title_row0 + 1
            title_cell = ws_sum.cell(row=title_excel_row, column=1, value=title)
            title_cell.font = Font(bold=True, size=12, color="FFFFFF")
            title_cell.fill = TITLE_FILL
            if n_cols > 1:
                ws_sum.merge_cells(start_row=title_excel_row, start_column=1,
                                    end_row=title_excel_row, end_column=n_cols)

            header_excel_row = header_row0 + 1
            for cell in ws_sum[header_excel_row]:
                if cell.value is not None:
                    _style_header(cell)

            for r in range(header_excel_row + 1, header_excel_row + 1 + n_rows):
                is_alt = ((r - header_excel_row) % 2 == 0)
                first_cell_val = str(ws_sum.cell(row=r, column=1).value or '')
                is_total_row = first_cell_val.strip().lower().startswith('total')
                for c in range(1, n_cols + 1):
                    cell = ws_sum.cell(row=r, column=c)
                    cell.border = THIN_BORDER
                    if is_total_row:
                        cell.font = Font(bold=True)
                        cell.fill = TOTAL_FILL
                    elif is_alt:
                        cell.fill = ALT_FILL

        for col in ws_sum.columns:
            max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col)
            ws_sum.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 70)

        _format_sheet(wb['Validation Results'],       'Category')
        _format_sheet(wb['Claim Match Summary'],      'Match Status')
        _format_sheet(wb['Missing Records'],          'Failure Category')
        _format_sheet(wb['Schema Coverage Analysis'], 'Coverage Status')
        _format_sheet(wb['Stats By Element'],         None)

    print(f"  [OK] Report saved: {output_path}")


# Summary row helper

def _summary_row(test_case, claim_number, icn_number, claim_transaction, coverage, matched_values) -> dict:
    return {
        'Test Case':           test_case,
        'Claim Number':        claim_number,
        'ICN Number':          icn_number,
        'ClaimTransaction':    claim_transaction,
        'Coverage Percentage': coverage,
        'Matched Values':      matched_values,
    }


# Main runner (fully generic - works for any consumer in CONSUMER_CONFIG)

def run(consumer_name: str) -> Optional[str]:
    if consumer_name not in CONSUMER_CONFIG:
        print(f"[ERROR] Unknown consumer: '{consumer_name}'")
        print(f"   Available: {', '.join(CONSUMER_CONFIG.keys())}")
        sys.exit(1)

    config     = CONSUMER_CONFIG[consumer_name]
    csv_path   = config['test_data']
    # Generic "direct pointer" comparison mode (same-shape source vs target).
    direct_mode  = str(config.get('comparison_mode', '')).strip().lower() == 'direct'
    # Severity policy: when enabled, EVERY outcome other than an exact 'Match'
    # is a Blocker (no nuanced Non-Blocker buckets). Defaults ON for direct mode
    # and is fully config-driven via "non_match_is_blocker" - nothing hardcoded.
    non_match_is_blocker = bool(config.get('non_match_is_blocker', direct_mode))
    # Optional: CSV column that forms the response-file key (defaults to the
    # claim-number column). Lets member-search style validations (files named by
    # reqSbmtProvId) reuse the same engine without any hardcoding.
    _id_col_override = config.get('identifier_column')
    # Optional: character replacements applied to that identifier value before
    # it's used to build/match the response filename (e.g. a GraphQL
    # claimTransactionIdentifier "KEN:73848570:0:1:..." is written to disk with
    # colons sanitized to underscores). A plain dict of {old: new}; applied in
    # order, generic across any validation with a similar sanitize rule.
    _id_replace = config.get('identifier_replace') or {}
    _map_cols    = config.get('mapping_columns') or {}
    _src_aliases = [_map_cols['source']] if _map_cols.get('source') else None
    _tgt_aliases = [_map_cols['target']] if _map_cols.get('target') else None
    clm_filter = config.get('claim_filter')         # e.g. "PHYSICIAN", "HOSPITAL", None
    claim_type = config['claim_type']               # e.g. "Physician", "Hospital", "Summary"
    mappings   = config['mapping_sheets']
    # Validation type: explicit config value wins, else legacy (filter/type).
    validation_type = config.get('validation_type') or clm_filter or claim_type

    # Generic source / response wiring (backward-compatible defaults)
    expected_source = config.get('expected_source', 'PPKG')
    actual_source   = config.get('actual_source', 'Alex')
    sources_cfg     = config.get('sources') or {}
    expected_folder = (sources_cfg.get(expected_source) or {}).get('folder', 'PPKG_Responses')
    expected_suffix = (sources_cfg.get(expected_source) or {}).get('suffix', '_ppkgResponse.json')
    actual_folder   = (sources_cfg.get(actual_source) or {}).get('folder', 'Alex_Responses')
    actual_suffix   = (sources_cfg.get(actual_source) or {}).get('suffix', '_alexResponse.json')

    # Response root: explicit override, else legacy target/All_Responses/<type>.
    resp_root = config.get('response_base') or os.path.join(BASE_DIR, 'target', 'All_Responses', claim_type)
    alex_dir      = os.path.join(resp_root, actual_folder)
    ppkg_dir      = os.path.join(resp_root, expected_folder)
    output_dir    = os.path.join(resp_root, 'Filtered_Reports')
    report_dir    = os.path.join(resp_root, 'ConsolidateReports')
    for d in (alex_dir, ppkg_dir, output_dir, report_dir):
        os.makedirs(d, exist_ok=True)

    print("=" * 65)
    print(f"  Consumer        : {consumer_name}")
    print(f"  Claim Type      : {claim_type}")
    print(f"  Validation Type : {validation_type}")
    print(f"  Expected Source : {expected_source}   Actual Source : {actual_source}")
    print(f"  Test Data       : {csv_path}")
    print(f"  Mappings        : {len(mappings)} sheet(s)")
    print(f"  Actual Dir      : {alex_dir}")
    print(f"  Expected Dir    : {ppkg_dir}")
    print("=" * 65)

    for path in [csv_path] + mappings:
        if not os.path.exists(path):
            print(f"[ERROR] File not found: {path}")
            return None

    df_claims = pd.read_csv(csv_path, dtype=str).fillna('')
    # Strip whitespace from all string columns
    df_claims = df_claims.apply(lambda col: col.str.strip() if col.dtype == object else col)
    print(f"  Loaded {len(df_claims)} rows from test data")

    # claimtype column only required if we need to filter by it
    col_map = verify_csv_columns(df_claims, require_claimtype=(clm_filter is not None))

    combined_mapping: List[Tuple[str, str]] = []
    for mp in mappings:
        m = load_mapping(mp, _src_aliases, _tgt_aliases, normalize=not direct_mode)
        combined_mapping.extend(m)
        print(f"  Loaded {len(m)} field mappings: {os.path.basename(mp)}")

    # Build wildcard mapping-path sets for Schema Coverage Analysis.
    # In direct mode the mapping pointers are authored EXACTLY as they appear in
    # the responses, so they must NOT be run through normalize_path() (which
    # prepends the PPKG-vs-Alex '/claim/*' array wrapper). Keeping them raw means
    # Schema Coverage searches only the pointers that actually exist in the
    # mapping sheet - never an invented '/claim/*/...' path.
    mapping_ppkg_wc: set = set()
    mapping_alex_wc: set = set()
    for hcp_path, alex_path in combined_mapping:
        mapping_ppkg_wc.add(wildcard_path(hcp_path))
        for ap in str(alex_path).split('+'):
            ap = ap.strip()
            if ap:
                _ap = ap if direct_mode else normalize_path(ap)
                mapping_alex_wc.add(wildcard_path(_ap))
    mapping_all_wc = mapping_ppkg_wc | mapping_alex_wc

    # NOTE: claims are NO LONGER filtered out. Every CSV row is processed and
    summary_rows:         List[dict] = []
    consolidated_rows:    List[dict] = []
    claim_match_rows:     List[dict] = []
    missing_records_rows: List[dict] = []
    field_stats = defaultdict(lambda: {'total': 0, 'matched': 0})
    seen_identifiers: set = set()
    # Duplicate-claim tracking: {member_claim_key: first test case that used it}.
    # Used to flag (never drop) repeated claims on the Missing Records + Summary
    # sheets.
    seen_claim_keys: Dict[str, str] = {}
    duplicate_rows: List[dict] = []

    # Schema-drift collectors (aggregated across all validated claim pairs)
    ppkg_paths_all: Dict[str, object] = {}
    alex_paths_all: Dict[str, object] = {}
    type_mismatch_count = 0

    for _, row in df_claims.iterrows():
        # Read CSV row values - all already strings due to dtype=str.
        # member number / ICN are optional (see CSV_REQUIRED_COLUMNS) so guard
        # the lookups - a test-data file carrying only a claim key still works.
        _member_col       = col_map.get('memberNumber')
        _claim_col        = col_map.get('payerClaimControlNumber')
        _icn_col          = col_map.get('icn')
        member_number     = build_member_identifier(str(row[_member_col])) if _member_col else ''
        claim_number      = str(row[_claim_col]).strip() if _claim_col else ''
        icn_number        = str(row[_icn_col]).strip() if _icn_col else ''
        # Response-file key: the karate feature writes '<testcase>_<key>_<suffix>'.
        # By default the key is the claim number, but a validation whose files are
        # named by a different column (e.g. the hospital search names its files by
        # the ICN 'reqInvnCtlNbr') sets "identifier_column" in its config.
        #
        # IMPORTANT: that knob must ONLY change the response-FILE lookup key — it
        # must NOT overwrite the Claim Number shown in the report. Previously the
        # override replaced claim_number directly, which is why the Missing Records
        # sheet showed the ICN in the Claim Number column. Keep them separate:
        #   • claim_number  → the real claim number from the CSV (reqClmNbr, …) for the report
        #   • file_key      → the value used to build/locate the response file name
        file_key = claim_number
        if _id_col_override and _id_col_override in row.index:
            file_key = str(row[_id_col_override]).strip()
            for _old, _new in _id_replace.items():
                file_key = file_key.replace(_old, _new)
        # If the CSV has no dedicated claim-number column, fall back to the file
        # key so the report still shows a meaningful identifier instead of blank.
        if not claim_number:
            claim_number = file_key
        claim_transaction = str(row.get('claimTransactionIdentifier', '') or '').strip()
        # testcase preserved as-is (e.g. "01", "02") - matches karate filename exactly
        test_case         = str(row.get('testcase', '') or '').strip()
        # claimtype from CSV row (e.g. PHYSICIAN, HOSPITAL) - used in Claim Match & Missing Records
        row_claim_type    = str(row[col_map['claimtype']] if 'claimtype' in col_map else claim_type).strip() or claim_type

        # File identifier matches karate naming: testcase + '_' + <file key>
        identifier = f"{test_case}_{file_key}"
        # Dedup key prevents validating the SAME response twice. It must be as
        # granular as the response FILE name - otherwise distinct test cases that
        # legitimately reuse a claim/member (e.g. the same ICN exercised under
        # several test cases, each written to its own
        # '<testcase>_<claim>_*.json') are silently dropped from the report.
        # Hence the test case is part of the key by default.
        #
        # Config knob (optional): "dedup_columns" - a list of CSV column names to
        # build the key from instead, e.g. ["memberNumber", "claimNumber"] to
        # restore the legacy member+claim behaviour, or [] to disable dedup
        # entirely. Keeps the engine generic - no consumer is hardcoded.
        _dedup_cols = config.get('dedup_columns')
        if _dedup_cols is None:
            dedup_key = f"{member_number}_{identifier}"
        elif not _dedup_cols:
            dedup_key = None                      # dedup explicitly disabled
        else:
            dedup_key = "_".join(
                str(row.get(_c, '') or '').strip() for _c in _dedup_cols
            )

        alex_file  = _vf.resolve_response_file(alex_dir, identifier, file_key, actual_suffix)
        ppkg_file  = _vf.resolve_response_file(ppkg_dir, identifier, file_key, expected_suffix)
        ppkg_avail = os.path.exists(ppkg_file)
        alex_avail = os.path.exists(alex_file)

        # 1. Claim-type validation
        if clm_filter and row_claim_type.upper() != clm_filter.upper():
            reason = (f"Claim returned but belongs to {row_claim_type.title()} category. "
                      f"Cannot be validated under {validation_type.title()} validation.")
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'INVALID_CLAIM_TYPE', reason))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A - Invalid claim type', '0/0'))
            type_mismatch_count += 1
            print(f"  [WARN]  {claim_number} | INVALID CLAIM TYPE ({row_claim_type} != {clm_filter})")
            continue

        # Duplicate guard (skipped entirely when dedup is disabled via config).
        # This only catches a TRUE repeat - the exact same response file key
        # (test case + claim). Such a row would validate the identical response
        # twice, so it is skipped.
        if dedup_key is not None:
            if dedup_key in seen_identifiers:
                print(f"  [WARN]  DUPLICATE - skipping {claim_number} | ICN: {icn_number}")
                missing_records_rows.append(_missing_row(
                    test_case, claim_number, icn_number, row_claim_type, validation_type,
                    ppkg_avail, alex_avail, 'DUPLICATE_RECORD',
                    'Duplicate row: the same test case + claim appears more than once in the '
                    'test data and resolves to the same response file. Skipped to avoid '
                    'validating the identical response twice.'))
                summary_rows.append(_summary_row(
                    test_case, claim_number, icn_number, claim_transaction,
                    'DUPLICATE', 'See earlier row',
                ))
                duplicate_rows.append({
                    'Test Case':            test_case,
                    'Claim Number':         claim_number,
                    'ICN':                  icn_number,
                    'First Seen Test Case': seen_claim_keys.get(f"{member_number}_{claim_number}", ''),
                    'Occurrence':           'Repeat (skipped)',
                    'Validated':            'No',
                })
                continue
            seen_identifiers.add(dedup_key)

        # Duplicate CLAIM detection (informational, never skips).
        # The same claim/member legitimately appears under several test cases -
        # each writes its OWN response file, so every row is still validated in
        # full. Reporting it here makes the repetition visible on the Missing
        # Records + Summary sheets instead of silently disappearing.
        _claim_dup_key = f"{member_number}_{claim_number}"
        if _claim_dup_key in seen_claim_keys:
            _first_tc = seen_claim_keys[_claim_dup_key]
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'DUPLICATE_RECORD',
                f'Duplicate claim: this claim/ICN was already exercised by Test Case '
                f'{_first_tc}. The row IS fully validated (it has its own response '
                f'file) - flagged so the repeated claim is visible.'))
            duplicate_rows.append({
                'Test Case':            test_case,
                'Claim Number':         claim_number,
                'ICN':                  icn_number,
                'First Seen Test Case': _first_tc,
                'Occurrence':           'Repeat',
                'Validated':            'Yes',
            })
            print(f"  [INFO]  DUPLICATE CLAIM - {claim_number} (first seen in Test Case {_first_tc}) - still validated")
        else:
            seen_claim_keys[_claim_dup_key] = test_case

        # 2. Response-availability validation
        if not ppkg_avail and not alex_avail:
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'RESPONSE_MISSING_BOTH',
                'Response Missing in Both Systems'))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A - Response missing (both)', '0/0'))
            print(f"  x  {claim_number} | Response missing in BOTH systems")
            continue
        if not alex_avail:
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'RESPONSE_MISSING_ALEX', 'Alex Response Missing'))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A - Alex response missing', '0/0'))
            print(f"  x  {claim_number} | Alex response missing")
            continue
        if not ppkg_avail:
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'RESPONSE_MISSING_PPKG', 'PPKG Response Missing'))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A - PPKG response missing', '0/0'))
            print(f"  x  {claim_number} | PPKG response missing")
            continue

        # Load JSON responses (robust to malformed / non-JSON error payloads).
        # Some upstream failures write a plain-text body (e.g. a gateway
        # timeout message) or an empty file instead of JSON. Those must be
        # reported as a failed record - never crash the whole run.
        load_error = None
        alex_raw = None
        hcp_raw  = None
        try:
            with open(alex_file, 'r', encoding='utf-8') as f:
                alex_raw = f.read()
            alex_data = json.loads(alex_raw)
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            load_error = f"Alex response is not valid JSON ({exc.__class__.__name__}): {exc}"
        if load_error is None:
            try:
                with open(ppkg_file, 'r', encoding='utf-8') as f:
                    hcp_raw = f.read()
                hcp_data = json.loads(hcp_raw)
            except (json.JSONDecodeError, ValueError, OSError) as exc:
                load_error = f"PPKG response is not valid JSON ({exc.__class__.__name__}): {exc}"

        if load_error is not None:
            # Record the ACTUAL (raw) response text in Failure Reason so the report
            # shows exactly what came back. No parseable status code here, so the
            # semantic category 'RESPONSE_NOT_JSON' stands in for Failure Category.
            _raw = alex_raw if 'Alex' in load_error else hcp_raw
            failure_reason = (f"{load_error} | Actual response: {_truncate_text(_raw)}"
                              if _raw else load_error)
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'RESPONSE_NOT_JSON', failure_reason))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                f'N/A - {load_error}', '0/0',
            ))
            print(f"  [WARN]  {claim_number} | SKIPPED - {load_error}")
            continue

        # Skip guard.
        # NOTE: is_error_response() (e.g. a 404 "no records found" envelope) only
        # short-circuits the CLASSIC PPKG-vs-Alex claim-array comparison, where an
        # error response genuinely means "no claim array to walk". In direct_mode
        # (same-shape source-vs-target, e.g. stage vs de-canary) the two systems'
        # error envelopes ARE the thing being validated - ResponseCode,
        # ResponseDesc, Errors[]... are ordinary mapped fields, so skipping them
        # would silently drop every test case where both sides legitimately
        # return the same 404/"record not found" response. Only a genuine JSON
        # load failure (handled above) skips a direct-mode row.
        skip_reason  = None
        skip_category = 'CLAIM_NOT_FOUND'
        err_source   = None   # 'Alex' / 'PPKG' — whose response failed
        err_data     = None   # the actual error-response dict (for status + body)
        if not direct_mode:
            if is_error_response(alex_data):
                err_source, err_data = 'Alex', alex_data
                skip_reason = describe_error_response('Alex', alex_data)
            elif is_error_response(hcp_data):
                err_source, err_data = 'PPKG', hcp_data
                skip_reason = describe_error_response('PPKG', hcp_data)
            elif not has_claim_data(alex_data):
                err_source, err_data = 'Alex', alex_data
                skip_reason = 'Alex response returned no claim data'
            elif not has_claim_data(hcp_data):
                err_source, err_data = 'PPKG', hcp_data
                skip_reason = 'PPKG response returned no claim data'
        else:
            # Generic ("direct") mode never checked either side for an
            # error/failure envelope, so an asymmetric failure (one side
            # errors out, e.g. a 404/500, while the other returns a normal
            # response) silently fell through into field-by-field comparison
            # instead of being flagged - it never landed on the Missing
            # Records sheet. Detect and report that here, same as classic mode.
            # If BOTH sides return the SAME error/"not found" envelope that is
            # a legitimate shared business scenario, not a defect - let it flow
            # through to compare_direct() so those fields still get validated.
            alex_is_err = is_error_response(alex_data)
            hcp_is_err  = is_error_response(hcp_data)
            if alex_is_err and not hcp_is_err:
                err_source, err_data = 'Alex', alex_data
                skip_reason   = describe_error_response('Alex', alex_data)
                skip_category = 'RESPONSE_FAILED_ALEX'
            elif hcp_is_err and not alex_is_err:
                err_source, err_data = 'PPKG', hcp_data
                skip_reason   = describe_error_response('PPKG', hcp_data)
                skip_category = 'RESPONSE_FAILED_PPKG'

        if skip_reason:
            # Failure Category = the HTTP / service status code (e.g. 404, 500)
            # read from the error envelope; falls back to the semantic category
            # when no code is present. Failure Reason = the ACTUAL response body
            # so the report records exactly what the service returned.
            status_code    = extract_status_code(err_data)
            failure_cat    = status_code or skip_category
            actual_body    = format_actual_response(err_source, err_data)
            failure_reason = (f"{skip_reason} | {actual_body}"
                              if actual_body else skip_reason)
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, failure_cat, failure_reason))
            print(f"  [WARN]  {claim_number} | SKIPPED - {skip_reason}")
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                f'N/A - {skip_reason}', '0/0',
            ))
            continue

        # Schema-path collection (drift analysis)
        _extract_paths = extract_all_paths_generic if direct_mode else extract_all_paths
        for p, v in _extract_paths(hcp_data).items():
            ppkg_paths_all.setdefault(p, v)
        for p, v in _extract_paths(alex_data).items():
            alex_paths_all.setdefault(p, v)

        # Claim-level match summary (claim-array specific; skipped for the
        # generic direct-pointer mode where responses have no claim array).
        if not direct_mode:
            cm_rows, mr_rows = build_claim_match_and_missing(
                hcp_data, alex_data,
                claim_number, icn_number, member_number, row_claim_type,
                consumer_name, validation_type, test_case=test_case,
            )
            claim_match_rows.extend(cm_rows)
            missing_records_rows.extend(mr_rows)

        # Field-level comparison
        meta = {
            'claim_number':      claim_number,
            'icn_number':        icn_number,
            'claim_transaction': claim_transaction,
            'member_number':     member_number,
            'claim_type':        row_claim_type,
            'test_case':         test_case,
        }

        comp_rows, total, matched_count = (
            compare_direct(hcp_data, alex_data, combined_mapping, meta)
            if direct_mode
            else compare_claim_pair(hcp_data, alex_data, combined_mapping, meta)
        )
        consolidated_rows.extend(comp_rows)


        for r in comp_rows:
            # Use the same Normalized Pointer as every other sheet so field
            schema_path = (r.get('Normalized Pointer') or '').lstrip('/') or wildcard_path(r['PPKGPath'])
            field_stats[schema_path]['total']   += 1
            field_stats[schema_path]['matched'] += int(r['Match Status'] == 'Match')

        coverage = (matched_count / total * 100) if total > 0 else 0.0
        summary_rows.append(_summary_row(
            test_case, claim_number, icn_number, claim_transaction,
            f"{coverage:.2f}%", f"{matched_count}/{total}",
        ))
        print(f"  [OK]  {claim_number} | ICN: {icn_number} | {matched_count}/{total} ({coverage:.1f}%)")

    # Final Consolidated Data (Validation Results)
    schema_order = build_schema_order_index(ppkg_paths_all, alex_paths_all)

    if consolidated_rows:
        consolidated_df = pd.DataFrame(consolidated_rows)

        def _claim_idx_int(val) -> int:
            try:
                return int(val)
            except (ValueError, TypeError):
                return 9999

        _max_order = len(schema_order)

        def _schema_order_for_row(ptr) -> int:
            return schema_order.get(str(ptr).lstrip('/'), _max_order)

        consolidated_df['_claim_idx_int']  = consolidated_df['PPKG Claim Index'].apply(_claim_idx_int)
        consolidated_df['_schema_order']   = consolidated_df['Normalized Pointer'].apply(_schema_order_for_row)
        consolidated_df = consolidated_df.sort_values(
            by=['Claim Number', '_claim_idx_int', '_schema_order'],
            kind='stable',
        ).drop(columns=['_claim_idx_int', '_schema_order', '_mapping_order'], errors='ignore').reset_index(drop=True)
    else:
        consolidated_df = pd.DataFrame(columns=CONSOLIDATED_COLUMNS)

    # Enforce exact column list (removes Consumer, Type, and any other extras)
    consolidated_df = consolidated_df.reindex(columns=CONSOLIDATED_COLUMNS)

    # Refine 'Value Missing in Source' rows using the now-complete AGGREGATE
    if not consolidated_df.empty:
        # Only refine rows STILL at their provisional 'Alex Only Field'
        _vmp_mask = (
            (consolidated_df['Match Status'] == 'Value Missing in Source') &
            (consolidated_df['Category'] == 'Alex Only Field')
        )
        if _vmp_mask.any():
            _wc_series = consolidated_df.loc[_vmp_mask, 'Normalized Pointer'].astype(str).str.lstrip('/')
            _refined = _wc_series.apply(lambda wc: refine_value_missing_in_ppkg(schema_has_path(wc, ppkg_paths_all)))
            consolidated_df.loc[_vmp_mask, 'Severity']   = _refined.apply(lambda t: t[0])
            consolidated_df.loc[_vmp_mask, 'Conclusion'] = _refined.apply(lambda t: t[1])
            consolidated_df.loc[_vmp_mask, 'Category']   = _refined.apply(lambda t: t[2])

        # Refine 'Value Missing in Target' rows using the now-complete
        _vma_mask = (
            (consolidated_df['Match Status'] == 'Value Missing in Target') &
            (consolidated_df['Category'] == 'Missing In Alex (True Missing)')
        )
        if _vma_mask.any():
            _wc_series2 = consolidated_df.loc[_vma_mask, 'Normalized Pointer'].astype(str).str.lstrip('/')
            _refined2 = _wc_series2.apply(lambda wc: refine_value_missing_in_alex(schema_has_path(wc, alex_paths_all)))
            consolidated_df.loc[_vma_mask, 'Severity']   = _refined2.apply(lambda t: t[0])
            consolidated_df.loc[_vma_mask, 'Conclusion'] = _refined2.apply(lambda t: t[1])
            consolidated_df.loc[_vma_mask, 'Category']   = _refined2.apply(lambda t: t[2])

    # Additive override layer (see hardcoding.py) - does NOT alter comparison
    # logic above; only rewrites the outcome for configured null-vs-null pairs.
    # Column names are resolved generically from THIS consumer's config
    # (feature_config.py 'report_columns', if any) - hardcoding.py never
    # hardcodes a literal column name for any single consumer.
    try:
        consolidated_df = _hc.validate_match(consolidated_df, var=consumer_name, config=config)
    except Exception as _exc:
        print(f"[WARN]  Hardcoded override skipped: {_exc}")

    # Severity policy enforcement (config-driven, see 'non_match_is_blocker').
    # Applied LAST so it wins over every refinement/override above: any row whose
    # Match Status is not an exact 'Match' becomes a Blocker; matches stay
    # Non-Blocker. This keeps the rule generic - no per-consumer literals.
    if non_match_is_blocker and not consolidated_df.empty:
        _is_match = consolidated_df['Match Status'] == 'Match'
        consolidated_df.loc[~_is_match, 'Severity'] = 'Blocker'
        consolidated_df.loc[_is_match, 'Severity']  = 'Non-Blocker'

    # Claim Match Summary
    claim_match_df = (
        pd.DataFrame(claim_match_rows, columns=CLAIM_MATCH_COLUMNS)
        if claim_match_rows
        else pd.DataFrame(columns=CLAIM_MATCH_COLUMNS)
    )

    # Missing Records
    missing_records_df = (
        pd.DataFrame(missing_records_rows, columns=MISSING_RECORDS_COLUMNS)
        if missing_records_rows
        else pd.DataFrame(columns=MISSING_RECORDS_COLUMNS)
    )

    # Schema Coverage Analysis
    schema_rows = build_schema_coverage(
        mapping_all_wc, ppkg_paths_all, alex_paths_all,
        mapping_ppkg_wc=mapping_ppkg_wc, mapping_alex_wc=mapping_alex_wc,
    )
    schema_df = (
        pd.DataFrame(schema_rows, columns=SCHEMA_COVERAGE_COLUMNS)
        if schema_rows
        else pd.DataFrame(columns=SCHEMA_COVERAGE_COLUMNS)
    )


    # Stats By Element
    ordered_stat_paths = ordered_by_schema(field_stats.keys(), schema_order)
    stats_rows = [
        {
            'PPKG Field Path': path,
            '# Occurrences':   field_stats[path]['total'],
            '# Matched':       field_stats[path]['matched'],
            '# Mismatched':    field_stats[path]['total'] - field_stats[path]['matched'],
            '% Matched':       round(field_stats[path]['matched'] / field_stats[path]['total'] * 100, 2)
                                if field_stats[path]['total'] > 0 else 0.0,
        }
        for path in ordered_stat_paths
    ]
    stats_df = (
        pd.DataFrame(stats_rows)
        if stats_rows
        else pd.DataFrame(columns=['PPKG Field Path', '# Occurrences', '# Matched', '# Mismatched', '% Matched'])
    )

    # Run-level metrics (for the console summary only)
    total_rows    = len(consolidated_df)
    match_rows    = _count_rows(consolidated_df, **{'Match Status': 'Match'})
    mismatch_rows = _count_rows(consolidated_df, **{'Match Status': 'Mismatch'})
    fmp           = _count_rows(consolidated_df, **{'Match Status': 'Value Missing in Source'})
    fma           = _count_rows(consolidated_df, **{'Match Status': 'Value Missing in Target'})
    fmb           = _count_rows(consolidated_df, **{'Match Status': 'Value Missing in Both'})
    new_ppkg      = len([p for p in ppkg_paths_all if p not in mapping_all_wc])
    new_alex      = len([p for p in alex_paths_all if p not in mapping_all_wc])
    blocker_total     = _count_rows(consolidated_df, Severity='Blocker')
    non_blocker_total = _count_rows(consolidated_df, Severity='Non-Blocker')

    # Business-focused Summary sheet
    summary_blocks = build_summary_blocks(consolidated_df, duplicate_rows=duplicate_rows)

    # Console summary
    print(f"\n{'='*65}")
    print(f"  Consumer                 : {consumer_name}")
    print(f"  Total mapping fields     : {len(combined_mapping)}")
    print(f"  Fields compared          : {total_rows}")
    print(f"  Matched / Mismatched     : {match_rows} / {mismatch_rows}")
    print(f"  Missing PPKG/Alex/Both   : {fmp} / {fma} / {fmb}")
    if total_rows:
        print(f"  Overall coverage         : {(match_rows / total_rows * 100):.2f}%")
    else:
        print(f"  Overall coverage         : N/A")
    print(f"  New fields PPKG/Alex     : {new_ppkg} / {new_alex}")
    print(f"  Blockers / Non-Blockers  : {blocker_total} / {non_blocker_total}")
    print(f"  Claim type mismatches    : {type_mismatch_count}")
    print(f"  Duplicate claims         : {len(duplicate_rows)}")
    print(f"  Missing records total    : {len(missing_records_df)}")
    print(f"  Schema coverage paths    : {len(schema_df)}")
    print(f"{'='*65}\n")

    # Write report
    # Auto-parse SOURCE (PPKG) + TARGET (Alex) feature files for URLs / envs so
    # the report header carries both endpoints and both environments.
    try:
        st_meta = _vf.build_source_target_metadata(config)
    except Exception as _exc:
        print(f"[WARN]  Source/target metadata parsing skipped: {_exc}")
        st_meta = {}

    try:
        request_type = _cr.determine_request_type(config)
    except Exception:
        request_type = 'Summary API' if not clm_filter else 'Detailed API'

    resolved_meta = {
        'consumer_label':  config.get('consumer_name') or consumer_name,
        'expected_source': expected_source,
        'actual_source':   actual_source,
        'validation_type': validation_type,
        'request_type':    request_type,
        'search_type':     config.get('search_type') or validation_type,
        'source_url':      st_meta.get('source_url', ''),
        'target_url':      st_meta.get('target_url', ''),
        'source_env':      st_meta.get('source_env', ''),
        'target_env':      st_meta.get('target_env', ''),
        # Legacy single-environment key kept for backward compatibility.
        'environment':     st_meta.get('target_env', '') or (config.get('metadata') or {}).get('environment', ''),
        'module':          (config.get('metadata') or {}).get('module', ''),
    }
    try:
        report_name = _vf.build_report_name(consumer_name, config, resolved_meta)
    except Exception:
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"{consumer_name}_validation_report_{timestamp}.xlsx"
    report_path = os.path.join(report_dir, report_name)

    # The exported 'Validation Results' sheet shows only the business-facing
    validation_results_df = consolidated_df.reindex(columns=VALIDATION_RESULTS_COLUMNS)

    write_excel_report(
        report_path,
        summary_blocks, validation_results_df,
        claim_match_df, missing_records_df, schema_df,
        stats_df,
    )

    # Additive consumer-based report sheets (does NOT alter existing report
    # logic above) - Sheet 1 "Run Information" + Sheet 2 "Validation Summary".
    # See consumer_report.py.
    try:
        _cr.inject_consumer_report_sheets(
            report_path, consumer_name, config, resolved_meta, consolidated_df,
        )
    except Exception as _exc:
        print(f"[WARN]  Consumer report sheets skipped: {_exc}")

    return report_path


# Entry point
if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) >= 2 else os.environ.get('CONSUMER_NAME')

    if arg and arg.strip().lower() in ('--all', 'all', '*'):
        # Generic "run every registered consumer" mode. CONSUMER_CONFIG already
        # merges the static feature_config.CONSUMER_CONFIG entries with anything
        # auto-discovered from validation_config/*/config.json, so this stays
        # fully generic - onboarding a new consumer NEVER requires touching this
        # file or the Karate runner feature; only feature_config.py (or a new
        # validation_config/<Name>/config.json) changes.
        names = list(CONSUMER_CONFIG.keys())
        print(f"[INFO] --all mode: running {len(names)} consumer(s): {', '.join(names)}\n")
        failures: List[str] = []
        for name in names:
            print(f"\n{'#'*70}\n# Consumer: {name}\n{'#'*70}")
            try:
                run(name)
            except Exception as exc:
                failures.append(name)
                print(f"[ERROR] Consumer '{name}' failed: {exc}")
        if failures:
            print(f"\n[WARN]  {len(failures)}/{len(names)} consumer(s) failed: {', '.join(failures)}")
            sys.exit(1)
    elif arg:
        run(arg)
    else:
        consumer = 'HCPvsAlex_Physician'
        print(f"[WARN]  No consumer specified, defaulting to: {consumer}")
        print(f"   Usage  : python Schema_Validation.py <consumer_name> | --all")
        print(f"   Options: {', '.join(CONSUMER_CONFIG.keys())}\n")
        run(consumer)

