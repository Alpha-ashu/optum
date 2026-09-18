from __future__ import annotations

import os
import sys
import json
import logging
import pandas as pd
from collections import defaultdict, deque
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

# ─────────────────────────────────────────────────────────────────────────────
# Resolve project base directory
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if not os.path.exists(os.path.join(BASE_DIR, 'pom.xml')):
    BASE_DIR = os.getcwd().split("src")[0] if "src" in os.getcwd() else os.getcwd()

# ─────────────────────────────────────────────────────────────────────────────
# Consumer Configuration
# ─────────────────────────────────────────────────────────────────────────────
CONSUMER_CONFIG = {
    "Hospital": {
        "test_data":      os.path.join(BASE_DIR, "src", "test", "resources", "testdata", "decanary", "decanary_detail_hospital.csv"),
        "claim_filter":   None,
        "claim_type":     "Hospital",
        "mapping_sheets": [
            os.path.join(BASE_DIR, "src", "test", "utility", "validation_mapping", "ppkg", "tops", "decanaryhospital.xlsx")
        ],
    },
    "Physician": {
        "test_data":      os.path.join(BASE_DIR, "src", "test", "resources", "testdata", "decanary", "decanary_detail_physician.csv"),
        "claim_filter":   None,
        "claim_type":     "Physician",
        "mapping_sheets": [
            os.path.join(BASE_DIR, "src", "test", "utility", "validation_mapping", "ppkg", "tops", "decanaryphysician.xlsx")
        ],
    },
    "Summary": {
        "test_data":      os.path.join(BASE_DIR, "src", "test", "resources", "testdata", "decanary", "decanary_detail_hospital.csv"),
        "claim_filter":   None,
        "claim_type":     "Summary",
        "mapping_sheets": [
            os.path.join(BASE_DIR, "src", "test", "utility", "validation_mapping", "ppkg", "tops", "decanarysummary.xlsx")
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# CSV column aliases  (canonical name → list of possible column names in CSV)
# claimtype is OPTIONAL — only required when claim_filter is set
# ─────────────────────────────────────────────────────────────────────────────
CSV_COLUMN_ALIASES = {
    'memberNumber':            ['memberNumber', 'member_number', 'membernumber', 'member', 'MemberNumber'],
    'payerClaimControlNumber': ['payerClaimControlNumber','claimNumber', 'claim_number', 'claimnumber', 'claim', 'PayerClaimControlNumber'],
    'icn':                     ['internalReferenceIdentifier', 'icn', 'ICN', 'icn_number', 'Icn'],
    'claimtype':               ['ClaimType', 'claimtype', 'claimType_filter', 'claim_type_filter', 'claim_type'],
}

# Columns that are always required (decanary CSV only guarantees the ICN)
CSV_REQUIRED_COLUMNS = {'icn'}


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def resolve_column(df: pd.DataFrame, aliases: list) -> Optional[str]:
    for name in aliases:
        if name in df.columns:
            return name
    return None


def verify_csv_columns(df: pd.DataFrame, require_claimtype: bool = False) -> dict:
    """
    Resolve CSV column names using aliases.
    claimtype is only required when require_claimtype=True (i.e. claim_filter is set).
    """
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
    # meta paths stay as-is — they live at the response root, not inside claim array
    if stripped.startswith('meta/'):
        return '/' + stripped
    # /data/*/ and /data/N/ → /claim/*/  (wildcard the index)
    path = path.replace('/data/*/', '/claim/*/')
    # Replace hardcoded numeric indices: /data/0/ → /claim/*/
    import re
    path = re.sub(r'/data/\d+/', '/claim/*/', path)
    stripped = path.lstrip('/')
    if not (stripped.startswith('claim/') or stripped.startswith('data/') or stripped.startswith('meta/')):
        path = '/claim/*/' + stripped
    return path


def wildcard_path(path: str) -> str:
    return '/'.join(['*' if p.isdigit() else p for p in path.strip('/').split('/')])


def extract_values(json_obj, pointer: str) -> list:
    """
    Extract all values matching a JSON pointer (supports * wildcards).
    Returns list of (resolved_path, value) tuples with actual array indices.
    """
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
    return s


def load_mapping(excel_path: str) -> List[Tuple[str, str]]:
    
    df = pd.read_excel(excel_path, engine='openpyxl')

    def _pick(*candidates) -> str:
        for c in candidates:
            if c in df.columns:
                return c
        raise ValueError(
            f"Mapping sheet '{os.path.basename(excel_path)}' is missing expected columns. "
            f"Looked for {candidates}, found {list(df.columns)}"
        )

    ppkg_col = _pick('PPKG_Path', 'PPKG Path')
    tgt_col  = _pick('Decanary_Path', 'ALEX Path', 'Decanary Path')

    df.dropna(subset=[ppkg_col, tgt_col], inplace=True)
    return [
        (normalize_path(str(row[ppkg_col])), normalize_path(str(row[tgt_col])))
        for _, row in df.iterrows()
    ]


def wrap_response(data: dict) -> Tuple[dict, str]:
    """
    Return the FULL claim array with ALL transactions at their original indices.
    Resolved paths will be: /claim/0/..., /claim/1/..., /claim/2/..., /claim/3/...
    """
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
    # Summary API returns warnings in meta with no data key when not found
    if 'meta' in data and 'data' not in data and 'claim' not in data:
        warnings = data.get('meta', {}).get('warnings', [])
        if warnings:
            return True
    return False


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
    """
    Build the member number part of the response filename.
    Matches karate's: memberId + '_' + claimIdentifier
    memberNumber is zero-padded to 9 digits to match zfill(9).
    """
    try:
        # Strip any trailing .0 from CSV integer read as float
        s = str(member_number_raw).strip()
        if s.endswith('.0'):
            s = s[:-2]
        return s.zfill(9)
    except Exception:
        return str(member_number_raw).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Claim Match Summary helpers
# ───────────────────────────────────────────────────────────────────────────────

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
    """
    Match PPKG (HCP) claim transactions to Alex claim transactions by ICN
    (internalReferenceIdentifier).

    Returns:
        (claim_match_rows, missing_records_rows)

    A PPKG or Alex claim transaction that has no counterpart on the other side is
    recorded in Missing Records under the MATCHING_RECORD_NOT_FOUND category — it
    is never silently skipped.
    """
    ppkg_claims = get_claims_list(hcp_data)
    alex_claims = get_claims_list(alex_data)

    # Build Alex ICN → deque of indices (same ICN may appear multiple times)
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


# ─────────────────────────────────────────────────────────────────────────────
# Column definitions for all 5 sheets
# ─────────────────────────────────────────────────────────────────────────────

CONSOLIDATED_COLUMNS = [
    'Test Case', 'Member Number', 'Claim Number', 'ICN Number',
    'Claim Type', 'ClaimTransaction',
    'PPKG Claim Index', 'Alex Claim Index',
    'PPKG ICN', 'Alex ICN',
    'PPKGPath', 'AlexPath',
    'PPKGValue', 'AlexValue',
    'Match Status', 'Category', 'Severity',
]

# Explicit exception list: fields that should stay Non-Blocker even when
# genuinely missing on one side. Empty by default - nothing is ignored unless
# a developer explicitly adds a rule here (same policy as DMV Schema_Validation
# and the shared_validation_framework project-wide standard).
IGNORABLE_MISSING_FIELDS: List[str] = [
    # "someKnownAlexGapField",
]


def _is_ignorable_missing_field(*paths: str) -> bool:
    if not IGNORABLE_MISSING_FIELDS:
        return False
    haystacks = [str(p or '').lower() for p in paths]
    for needle in IGNORABLE_MISSING_FIELDS:
        n = str(needle).lower().strip()
        if n and any(n in h for h in haystacks):
            return True
    return False


def classify_severity(status: str, ppkg_path: str = '', alex_path: str = '') -> Tuple[str, str]:
    """
    Single, project-wide classification policy (mirrors DMV Schema_Validation
    and shared_validation_framework.classify_missing_field):
      - Match                  -> ('Matched', 'Non-Blocker')
      - Mismatch                -> ('Data Mismatch', 'Blocker')
      - Value Missing in Alex   -> ('Missing In Alex (True Missing)', 'Blocker')
                                    unless field is on the ignore list
      - Value Missing in PPKG   -> ('Missing In PPKG (True Missing)', 'Blocker')
                                    unless field is on the ignore list
      - Value Missing in Both   -> ('Missing In Both', 'Non-Blocker') (nothing to compare)
    """
    if status == 'Match':
        return 'Matched', 'Non-Blocker'
    if status == 'Mismatch':
        return 'Data Mismatch', 'Blocker'
    if status == 'Value Missing in Alex':
        if _is_ignorable_missing_field(ppkg_path, alex_path):
            return 'Missing In Alex (Ignored)', 'Non-Blocker'
        return 'Missing In Alex (True Missing)', 'Blocker'
    if status == 'Value Missing in PPKG':
        if _is_ignorable_missing_field(ppkg_path, alex_path):
            return 'Missing In PPKG (Ignored)', 'Non-Blocker'
        return 'Missing In PPKG (True Missing)', 'Blocker'
    if status == 'Value Missing in Both':
        return 'Missing In Both', 'Non-Blocker'
    return status or 'Uncategorized', 'Non-Blocker'

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
)


def _yn(flag) -> str:
    """Boolean → 'Y' / 'N'."""
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


# ─────────────────────────────────────────────────────────────────────────────
# Core comparison engine helpers
# ───────────────────────────────────────────────────────────────────────────────

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
    """
    Return a copy of a mapping path with its top-level claim index replaced by `idx`.
    e.g. '/claim/0/claimLevelTotals/x' + idx=2 -> '/claim/2/claimLevelTotals/x'
    Handles both numeric ('0') and wildcard ('*') second segments.
    """
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


def _row(test_case, member_number, claim_number, icn_number,
         claim_type, claim_transaction,
         ppkg_idx, alex_idx, ppkg_icn, alex_icn,
         hcp_path, alex_path,
         hcp_val, alex_val, status,
         mapping_order=0) -> dict:
    """Build a single consolidated data row. Consumer and Type are intentionally excluded."""
    category, severity = classify_severity(status, hcp_path, alex_path)
    return {
        'Test Case':        test_case,
        'Member Number':    member_number,
        'Claim Number':     claim_number,
        'ICN Number':       icn_number,
        'Claim Type':       claim_type,
        'ClaimTransaction': claim_transaction,
        'PPKG Claim Index': ppkg_idx,
        'Alex Claim Index': alex_idx,
        'PPKG ICN':         ppkg_icn,
        'Alex ICN':         alex_icn,
        'PPKGPath':         hcp_path,
        'AlexPath':         alex_path,
        'PPKGValue':        normalize_value(hcp_val),
        'AlexValue':        normalize_value(alex_val),
        'Match Status':     status,
        'Category':         category,
        'Severity':         severity,
        '_mapping_order':   mapping_order,
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


# ─────────────────────────────────────────────────────────────────────────────
# Schema-drift helpers
# ─────────────────────────────────────────────────────────────────────────────

def _wildcard_parts(parts: List[str]) -> str:
    """Join path segments, collapsing numeric array indices to '*'."""
    return '/'.join('*' if p.isdigit() else p for p in parts)


def extract_all_paths(data) -> Dict[str, object]:
    """
    Walk an entire response and return {wildcard_leaf_path: sample_value} for
    every leaf field it contains. Array indices are collapsed to '*' so the
    result aligns with the wildcard form of the mapping paths.

    Paths are rooted at 'claim/*/...' (claim array) and 'meta/...' (response meta).
    """
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


def build_schema_coverage(
    mapping_all_wc: set,
    ppkg_paths: Dict[str, object],
    alex_paths: Dict[str, object],
) -> List[dict]:
    """
    Build the Schema Coverage Analysis rows by cross-referencing every path that
    appears in the mapping and/or either response. Covers BOTH drift directions:
      • Response paths absent from mapping  → 'Missing In Mapping'  (new schema)
      • Mapping paths absent from responses → 'Missing In PPKG/Alex/Both' (obsolete)
    """
    rows: List[dict] = []
    all_paths = set(mapping_all_wc) | set(ppkg_paths) | set(alex_paths)

    for p in sorted(all_paths):
        in_map  = p in mapping_all_wc
        in_ppkg = p in ppkg_paths
        in_alex = p in alex_paths

        if in_ppkg and in_alex:
            source = 'Both'
        elif in_ppkg:
            source = 'PPKG'
        elif in_alex:
            source = 'Alex'
        else:
            source = 'Mapping'

        if not in_map:
            status = 'Missing In Mapping'
        elif in_ppkg and in_alex:
            status = 'Mapped And Present'
        elif in_ppkg and not in_alex:
            status = 'Missing In Alex'
        elif in_alex and not in_ppkg:
            status = 'Missing In PPKG'
        else:
            status = 'Missing In Both Responses'

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


# ───────────────────────────────────────────────────────────────────────────────
# Core comparison engine
# ─────────────────────────────────────────────────────────────────────────────

def compare_claim_pair(
    hcp_data: dict,
    alex_data: dict,
    mapping: List[Tuple[str, str]],
    meta: dict,
    mapping_order_offset: int = 0,
) -> Tuple[List[dict], int, int]:
    """
    Compare one HCP vs Alex response per claim index.
    PPKG /claim/N/field is compared ONLY against Alex /claim/N/field.
    If PPKG has the field at index N but Alex does not  → 'Value Missing in Alex'
    If Alex has the field at index N but PPKG does not  → 'Value Missing in PPKG'
    Returns: (rows, total_fields, matched_fields)
    """
    hcp_wrapped, hcp_root   = wrap_response(hcp_data)
    alex_wrapped, alex_root = wrap_response(alex_data)

    rows:    List[dict] = []
    total   = 0
    matched = 0

    # PPKG is the source of truth. When a mapped field is absent in BOTH
    # responses we still emit one row per source claim so every mapping row
    # is represented in the report (nothing is silently skipped).
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

        # ── Meta path: compare directly against raw response root ─────────
        if hcp_wild.lstrip('/').startswith('meta/') or alex_wild.lstrip('/').startswith('meta/'):
            hcp_vals  = extract_values(hcp_data,  hcp_wild.lstrip('/'))
            alex_vals = extract_values(alex_data, alex_wild.lstrip('/'))
            if not hcp_vals and not alex_vals:
                continue
            for (h_ptr, h_val), (a_ptr, a_val) in zip(hcp_vals, alex_vals):
                is_match = normalize_value(h_val) == normalize_value(a_val)
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
            # Field absent in BOTH PPKG and Alex — log explicitly (per claim)
            # instead of skipping, so every mapped field is reported.
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

        # ── Summation support (per claim index) ───────────────────────────
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
                        f"{safe_float(hcp_val):.2f}", '', 'Value Missing in Alex',
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
                            '', f"{alex_comp_val:.2f}", 'Value Missing in PPKG',
                            mapping_order=_morder,
                        ))
                    total += 1
            continue

        # ── Direct comparison — matched by resolved path ──────────────────
        alex_schema_parts_direct = wildcard_path(alex_path).split('/')

        def _alex_ptr_for_hcp_ptr(hcp_ptr: str) -> str:
            hcp_parts   = hcp_ptr.strip('/').split('/')
            hcp_indices = [p for p in hcp_parts if p.isdigit()]
            result      = []
            idx_cursor  = 0
            for ap in alex_schema_parts_direct:
                if ap == '*':
                    result.append(hcp_indices[idx_cursor] if idx_cursor < len(hcp_indices) else '0')
                    idx_cursor += 1
                else:
                    result.append(ap)
            # Always use 'claim' as root key — alex_wrapped uses {"claim": [...]}
            # regardless of whether the original response had 'data' or 'claim'
            if result and result[0] in ('claim', 'data', alex_root):
                result[0] = 'claim'
            return '/'.join(result)

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
                is_match    = normalize_value(hcp_val) == normalize_value(alex_val)
                status      = 'Match' if is_match else 'Mismatch'
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
                expected_alex_path = _build_resolved_alex_path(resolved_hcp_ptr, alex_path, alex_root)
                rows.append(_row(
                    test_case, member_number, claim_number, icn_number,
                    claim_type, claim_transaction,
                    claim_idx, claim_idx, ppkg_icn, alex_icn,
                    r_hcp_path, expected_alex_path + ' (field absent in Alex)',
                    hcp_val, '', 'Value Missing in Alex',
                    mapping_order=_morder,
                ))
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
            expected_ppkg_path = _build_resolved_alex_path(ptr, hcp_path, hcp_root)
            rows.append(_row(
                test_case, member_number, claim_number, icn_number,
                claim_type, claim_transaction,
                claim_idx, claim_idx, ppkg_icn, alex_icn,
                expected_ppkg_path + ' (field absent in PPKG)', r_alex_path,
                '', val, 'Value Missing in PPKG',
                mapping_order=_morder,
            ))
            total += 1

    return rows, total, matched


# ───────────────────────────────────────────────────────────────────────────────
# Excel report writer — 5 sheets
# ─────────────────────────────────────────────────────────────────────────────

def write_excel_report(
    output_path: str,
    metrics_df: pd.DataFrame,
    summary_df: pd.DataFrame,
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
        if sv in ('MATCH', 'MATCHED') or sv == 'MAPPED AND PRESENT':
            return MATCH_FILL
        if 'MISMATCH' in sv:
            return MISMATCH_FILL
        if 'MISSING' in sv or 'NOT_FOUND' in sv or 'NOT FOUND' in sv or 'INVALID' in sv:
            return MISSING_FILL
        return None

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # ── Summary sheet: run metrics on top, per-claim coverage below ──
        metrics_df.to_excel(writer, sheet_name='Summary', index=False, startrow=0)
        detail_start = len(metrics_df) + 2
        summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=detail_start)

        consolidated_df.to_excel(writer,    sheet_name='Validation Results',      index=False)
        claim_match_df.to_excel(writer,     sheet_name='Claim Match Summary',     index=False)
        missing_records_df.to_excel(writer, sheet_name='Missing Records',         index=False)
        schema_df.to_excel(writer,          sheet_name='Schema Coverage Analysis', index=False)
        stats_df.to_excel(writer,           sheet_name='Stats By Element',        index=False)

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

        # ── Custom formatting for the two-table Summary sheet ──
        ws_sum = wb['Summary']
        for cell in ws_sum[1]:                       # metrics header
            _style_header(cell)
        detail_header_row = detail_start + 1
        for cell in ws_sum[detail_header_row]:       # per-claim header
            if cell.value is not None:
                _style_header(cell)
        # colour coverage column in the per-claim table
        cov_col = None
        for idx, cell in enumerate(ws_sum[detail_header_row], start=1):
            if cell.value == 'Coverage Percentage':
                cov_col = idx
                break
        for row in ws_sum.iter_rows(min_row=detail_header_row + 1):
            for cell in row:
                if cell.value is not None:
                    cell.border = THIN_BORDER
            if cov_col:
                fill = _fill_for(ws_sum.cell(row=row[0].row, column=cov_col).value)
                if fill:
                    for cell in row:
                        if cell.value is not None:
                            cell.fill = fill
        for row in ws_sum.iter_rows(min_row=2, max_row=len(metrics_df) + 1):
            for cell in row:
                cell.border = THIN_BORDER
        for col in ws_sum.columns:
            max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col)
            ws_sum.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 70)

        _format_sheet(wb['Validation Results'],       'Match Status')
        _format_sheet(wb['Claim Match Summary'],      'Match Status')
        _format_sheet(wb['Missing Records'],          'Failure Category')
        _format_sheet(wb['Schema Coverage Analysis'], 'Coverage Status')
        _format_sheet(wb['Stats By Element'],         None)

    print(f"  ✅ Report saved: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Summary row helper
# ─────────────────────────────────────────────────────────────────────────────

def _summary_row(test_case, claim_number, icn_number, claim_transaction, coverage, matched_values) -> dict:
    return {
        'Test Case':           test_case,
        'Claim Number':        claim_number,
        'ICN Number':          icn_number,
        'ClaimTransaction':    claim_transaction,
        'Coverage Percentage': coverage,
        'Matched Values':      matched_values,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main runner  (fully generic — works for any consumer in CONSUMER_CONFIG)
# ─────────────────────────────────────────────────────────────────────────────

def run(consumer_name: str) -> Optional[str]:
    if consumer_name not in CONSUMER_CONFIG:
        print(f"❌ Unknown consumer: '{consumer_name}'")
        print(f"   Available: {', '.join(CONSUMER_CONFIG.keys())}")
        sys.exit(1)

    config     = CONSUMER_CONFIG[consumer_name]
    csv_path   = config['test_data']
    clm_filter = config.get('claim_filter')         # e.g. "PHYSICIAN", "HOSPITAL", None
    claim_type = config['claim_type']               # e.g. "Physician", "Hospital", "Summary"
    mappings   = config['mapping_sheets']
    validation_type = clm_filter or claim_type      # label used in Missing Records

    response_base = os.path.join(BASE_DIR, 'target', 'All_Responses', 'TOPS')
    # PPKG (Non-Prod) is the source of truth ("hcp" internally).
    # Decanary (de-canary / dev) is the system under test ("alex" internally).
    ppkg_dir      = os.path.join(response_base, 'PPKG_Responses', claim_type)
    alex_dir      = os.path.join(response_base, 'Decanary_Responses', claim_type)
    report_dir    = os.path.join(response_base, 'ConsolidateReports')
    for d in (alex_dir, ppkg_dir, report_dir):
        os.makedirs(d, exist_ok=True)

    print("═" * 65)
    print(f"  Consumer        : {consumer_name}")
    print(f"  Claim Type      : {claim_type}")
    print(f"  Validation Type : {validation_type}")
    print(f"  Test Data       : {csv_path}")
    print(f"  Mappings        : {len(mappings)} sheet(s)")
    print(f"  PPKG Dir        : {ppkg_dir}")
    print(f"  Decanary Dir    : {alex_dir}")
    print("═" * 65)

    for path in [csv_path] + mappings:
        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            return None

    df_claims = pd.read_csv(csv_path, dtype=str).fillna('')
    # Strip whitespace from all string columns
    df_claims = df_claims.apply(lambda col: col.str.strip() if col.dtype == object else col)
    print(f"  Loaded {len(df_claims)} rows from test data")

    # claimtype column only required if we need to filter by it
    col_map = verify_csv_columns(df_claims, require_claimtype=(clm_filter is not None))

    combined_mapping: List[Tuple[str, str]] = []
    for mp in mappings:
        m = load_mapping(mp)
        combined_mapping.extend(m)
        print(f"  Loaded {len(m)} field mappings: {os.path.basename(mp)}")

    # Build wildcard mapping-path sets for Schema Coverage Analysis
    mapping_ppkg_wc: set = set()
    mapping_alex_wc: set = set()
    for hcp_path, alex_path in combined_mapping:
        mapping_ppkg_wc.add(wildcard_path(hcp_path))
        for ap in str(alex_path).split('+'):
            ap = ap.strip()
            if ap:
                mapping_alex_wc.add(wildcard_path(normalize_path(ap)))
    mapping_all_wc = mapping_ppkg_wc | mapping_alex_wc

    # NOTE: claims are NO LONGER filtered out. Every CSV row is processed and
    # reported — type mismatches are logged in Missing Records, not dropped.
    summary_rows:         List[dict] = []
    consolidated_rows:    List[dict] = []
    claim_match_rows:     List[dict] = []
    missing_records_rows: List[dict] = []
    field_stats = defaultdict(lambda: {'total': 0, 'matched': 0})
    seen_identifiers: set = set()

    # Schema-drift collectors (aggregated across all validated claim pairs)
    ppkg_paths_all: Dict[str, object] = {}
    alex_paths_all: Dict[str, object] = {}
    type_mismatch_count = 0

    for _, row in df_claims.iterrows():
        # ── Read CSV row values — all already strings due to dtype=str ──
        icn_number        = str(row[col_map['icn']]).strip()
        # member/claim numbers are optional in the decanary CSV — fall back to ICN
        member_number     = (build_member_identifier(str(row[col_map['memberNumber']]))
                             if 'memberNumber' in col_map else '')
        claim_number      = (str(row[col_map['payerClaimControlNumber']]).strip()
                             if 'payerClaimControlNumber' in col_map else icn_number)
        claim_transaction = str(row.get('claimTransactionIdentifier', '') or '').strip()
        # testcase preserved as-is (e.g. "01", "02") — matches karate filename exactly
        test_case         = str(row.get('testcase', '') or '').strip()
        # claimtype from CSV row (e.g. HOSPITAL) — used in Claim Match & Missing Records
        row_claim_type    = str(row[col_map['claimtype']] if 'claimtype' in col_map else claim_type).strip() or claim_type

        # File identifier matches karate naming: testcase + '_' + ICN
        # PPKG:     <testcase>_<ICN>_hcp.json   (source of truth)
        # Decanary: <testcase>_<ICN>_ppkg.json  (system under test)
        identifier = f"{test_case}_{icn_number}"
        # Dedup key uses testcase+ICN to prevent processing the same claim twice
        dedup_key  = identifier

        alex_file  = os.path.join(alex_dir, f"{identifier}_ppkg.json")
        ppkg_file  = os.path.join(ppkg_dir, f"{identifier}_hcp.json")
        ppkg_avail = os.path.exists(ppkg_file)
        alex_avail = os.path.exists(alex_file)

        # ── 1. Claim-type validation ─────────────────────────────────────
        # A returned claim that belongs to a different category is REPORTED —
        # never silently skipped.
        if clm_filter and row_claim_type.upper() != clm_filter.upper():
            reason = (f"Claim returned but belongs to {row_claim_type.title()} category. "
                      f"Cannot be validated under {validation_type.title()} validation.")
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'INVALID_CLAIM_TYPE', reason))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A — Invalid claim type', '0/0'))
            type_mismatch_count += 1
            print(f"  ⚠  {claim_number} | INVALID CLAIM TYPE ({row_claim_type} != {clm_filter})")
            continue

        # ── Duplicate guard ─────────────────────────────────────────────
        if dedup_key in seen_identifiers:
            print(f"  ⚠  DUPLICATE — skipping {claim_number} | ICN: {icn_number}")
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'DUPLICATE', 'See earlier row',
            ))
            continue
        seen_identifiers.add(dedup_key)

        # ── 2. Response-availability validation ───────────────────────────
        if not ppkg_avail and not alex_avail:
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'RESPONSE_MISSING_BOTH',
                'Response Missing in Both Systems'))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A — Response missing (both)', '0/0'))
            print(f"  ✗  {claim_number} | Response missing in BOTH systems")
            continue
        if not alex_avail:
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'RESPONSE_MISSING_ALEX', 'Alex Response Missing'))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A — Alex response missing', '0/0'))
            print(f"  ✗  {claim_number} | Alex response missing")
            continue
        if not ppkg_avail:
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'RESPONSE_MISSING_PPKG', 'PPKG Response Missing'))
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                'N/A — PPKG response missing', '0/0'))
            print(f"  ✗  {claim_number} | PPKG response missing")
            continue

        # ── Load JSON responses ──────────────────────────────────────────
        with open(alex_file, 'r', encoding='utf-8') as f:
            alex_data = json.load(f)
        with open(ppkg_file, 'r', encoding='utf-8') as f:
            hcp_data = json.load(f)

        # ── Skip guard ───────────────────────────────────────────────────
        skip_reason = None
        if is_error_response(alex_data):
            skip_reason = f"Alex returned {alex_data.get('status', 'error')}: {alex_data.get('detail', '')}"
        elif is_error_response(hcp_data):
            skip_reason = f"PPKG returned {hcp_data.get('status', 'error')}: {hcp_data.get('detail', '')}"
        elif not has_claim_data(alex_data):
            skip_reason = 'Alex response returned no claim data'
        elif not has_claim_data(hcp_data):
            skip_reason = 'PPKG response returned no claim data'

        if skip_reason:
            missing_records_rows.append(_missing_row(
                test_case, claim_number, icn_number, row_claim_type, validation_type,
                ppkg_avail, alex_avail, 'CLAIM_NOT_FOUND', skip_reason))
            print(f"  ⚠  {claim_number} | SKIPPED — {skip_reason}")
            summary_rows.append(_summary_row(
                test_case, claim_number, icn_number, claim_transaction,
                f'N/A — {skip_reason}', '0/0',
            ))
            continue

        # ── Schema-path collection (drift analysis) ───────────────────────
        for p, v in extract_all_paths(hcp_data).items():
            ppkg_paths_all.setdefault(p, v)
        for p, v in extract_all_paths(alex_data).items():
            alex_paths_all.setdefault(p, v)

        # ── Claim-level match summary ────────────────────────────────────
        cm_rows, mr_rows = build_claim_match_and_missing(
            hcp_data, alex_data,
            claim_number, icn_number, member_number, row_claim_type,
            consumer_name, validation_type, test_case=test_case,
        )
        claim_match_rows.extend(cm_rows)
        missing_records_rows.extend(mr_rows)

        # ── Field-level comparison ───────────────────────────────────────
        meta = {
            'claim_number':      claim_number,
            'icn_number':        icn_number,
            'claim_transaction': claim_transaction,
            'member_number':     member_number,
            'claim_type':        row_claim_type,
            'test_case':         test_case,
        }

        comp_rows, total, matched_count = compare_claim_pair(
            hcp_data, alex_data, combined_mapping, meta,
        )
        consolidated_rows.extend(comp_rows)

        for r in comp_rows:
            schema_path = wildcard_path(r['PPKGPath'])
            field_stats[schema_path]['total']   += 1
            field_stats[schema_path]['matched'] += int(r['Match Status'] == 'Match')

        coverage = (matched_count / total * 100) if total > 0 else 0.0
        summary_rows.append(_summary_row(
            test_case, claim_number, icn_number, claim_transaction,
            f"{coverage:.2f}%", f"{matched_count}/{total}",
        ))
        print(f"  ✓  {claim_number} | ICN: {icn_number} | {matched_count}/{total} ({coverage:.1f}%)")

    # ── Schema (document) ordering ────────────────────────────────────────
    # Preserve the ORDER in which fields appear in the actual response schema
    # (claimIdentifiers → claimCategories → claimState → ...) instead of the
    # mapping-sheet order (which may be alphabetical). extract_all_paths()
    # returns paths in document order, so dict insertion order == schema order.
    schema_order_list = list(ppkg_paths_all.keys())
    for _p in alex_paths_all:
        if _p not in ppkg_paths_all:
            schema_order_list.append(_p)
    schema_pos = {p: i for i, p in enumerate(schema_order_list)}

    def _schema_pos_of(path_str, default: int = 10 ** 9) -> int:
        base = str(path_str).split(' (')[0].strip().lstrip('/')
        return schema_pos.get(wildcard_path(base), default)

    # ── Final Consolidated Data (Validation Results) ──────────────────────
    if consolidated_rows:
        consolidated_df = pd.DataFrame(consolidated_rows)

        def _claim_idx_int(val) -> int:
            try:
                return int(val)
            except (ValueError, TypeError):
                return 9999

        consolidated_df['_claim_idx_int'] = consolidated_df['PPKG Claim Index'].apply(_claim_idx_int)
        # Order by response schema position first; mapping order breaks ties.
        consolidated_df['_schema_order'] = consolidated_df['PPKGPath'].apply(_schema_pos_of)
        consolidated_df = consolidated_df.sort_values(
            by=['Claim Number', '_claim_idx_int', '_schema_order', '_mapping_order'],
            kind='stable',
        ).drop(columns=['_claim_idx_int', '_schema_order', '_mapping_order'], errors='ignore').reset_index(drop=True)
    else:
        consolidated_df = pd.DataFrame(columns=CONSOLIDATED_COLUMNS)

    # Enforce exact column list (removes Consumer, Type, and any other extras)
    consolidated_df = consolidated_df.reindex(columns=CONSOLIDATED_COLUMNS)

    # ── Claim Match Summary ───────────────────────────────────────────────
    claim_match_df = (
        pd.DataFrame(claim_match_rows, columns=CLAIM_MATCH_COLUMNS)
        if claim_match_rows
        else pd.DataFrame(columns=CLAIM_MATCH_COLUMNS)
    )

    # ── Missing Records ───────────────────────────────────────────────────
    missing_records_df = (
        pd.DataFrame(missing_records_rows, columns=MISSING_RECORDS_COLUMNS)
        if missing_records_rows
        else pd.DataFrame(columns=MISSING_RECORDS_COLUMNS)
    )

    # ── Schema Coverage Analysis ──────────────────────────────────────────
    schema_rows = build_schema_coverage(mapping_all_wc, ppkg_paths_all, alex_paths_all)
    # Keep the response schema (document) order instead of alphabetical.
    schema_rows.sort(key=lambda r: _schema_pos_of(r['Path']))
    schema_df = (
        pd.DataFrame(schema_rows, columns=SCHEMA_COVERAGE_COLUMNS)
        if schema_rows
        else pd.DataFrame(columns=SCHEMA_COVERAGE_COLUMNS)
    )

    # ── Stats By Element ──────────────────────────────────────────────────
    stats_rows = [
        {
            'PPKG Field Path': path,
            '# Occurrences':   s['total'],
            '# Matched':       s['matched'],
            '# Mismatched':    s['total'] - s['matched'],
            '% Matched':       round(s['matched'] / s['total'] * 100, 2) if s['total'] > 0 else 0.0,
        }
        for path, s in field_stats.items()
    ]
    # Keep the response schema (document) order instead of insertion/alpha order.
    stats_rows.sort(key=lambda r: _schema_pos_of(r['PPKG Field Path']))
    stats_df = (
        pd.DataFrame(stats_rows)
        if stats_rows
        else pd.DataFrame(columns=['PPKG Field Path', '# Occurrences', '# Matched', '# Mismatched', '% Matched'])
    )

    # ── Run-level metrics (Summary enhancement) ───────────────────────────
    total_rows    = len(consolidated_df)
    match_rows    = int((consolidated_df['Match Status'] == 'Match').sum()) if total_rows else 0
    mismatch_rows = int((consolidated_df['Match Status'] == 'Mismatch').sum()) if total_rows else 0
    fmp           = int((consolidated_df['Match Status'] == 'Value Missing in PPKG').sum()) if total_rows else 0
    fma           = int((consolidated_df['Match Status'] == 'Value Missing in Alex').sum()) if total_rows else 0
    fmb           = int((consolidated_df['Match Status'] == 'Value Missing in Both').sum()) if total_rows else 0
    new_ppkg      = len([p for p in ppkg_paths_all if p not in mapping_all_wc])
    new_alex      = len([p for p in alex_paths_all if p not in mapping_all_wc])

    cat_counts = (
        missing_records_df['Failure Category'].value_counts().to_dict()
        if not missing_records_df.empty else {}
    )
    claims_missing_ppkg = int(cat_counts.get('RESPONSE_MISSING_PPKG', 0))
    claims_missing_alex = int(cat_counts.get('RESPONSE_MISSING_ALEX', 0))
    claims_missing_both = int(cat_counts.get('RESPONSE_MISSING_BOTH', 0))

    # ── Blocker Breakdown (derived directly from Validation Results Severity/
    #    Category columns, so it can never disagree with the detail sheet) ──
    blocker_df = consolidated_df[consolidated_df['Severity'] == 'Blocker'] if total_rows else pd.DataFrame()
    blocker_breakdown = (
        blocker_df['Category'].value_counts().to_dict() if not blocker_df.empty else {}
    )
    total_blockers = int(sum(blocker_breakdown.values()))

    metrics = [
        ('Total Mapping Fields',                len(combined_mapping)),
        ('Fields Compared',                     total_rows),
        ('Fields Missing In PPKG',              fmp),
        ('Fields Missing In Alex',              fma),
        ('Fields Missing In Both',              fmb),
        ('New Fields Detected In PPKG',         new_ppkg),
        ('New Fields Detected In Alex',         new_alex),
        ('Claims Skipped Due To Type Mismatch', type_mismatch_count),
        ('Claims Missing In PPKG',              claims_missing_ppkg),
        ('Claims Missing In Alex',              claims_missing_alex),
        ('Claims Missing In Both',              claims_missing_both),
        ('Total Blockers',                      total_blockers),
    ]
    for _cat, _cnt in sorted(blocker_breakdown.items()):
        metrics.append((f'Blocker - {_cat}', int(_cnt)))
    metrics_df = pd.DataFrame(metrics, columns=['Metric', 'Value'])

    # ── Per-claim Summary (with OVERALL row prepended) ────────────────────
    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    if not summary_df.empty:
        overall_pct = (match_rows / total_rows * 100) if total_rows > 0 else 0.0
        overall_row = pd.DataFrame([_summary_row(
            'OVERALL', 'OVERALL', 'SUMMARY', '',
            f"{overall_pct:.2f}%", f"{match_rows}/{total_rows}",
        )], columns=SUMMARY_COLUMNS)
        summary_df = pd.concat([overall_row, summary_df], ignore_index=True)

    # ── Console summary ───────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print(f"  Consumer                 : {consumer_name}")
    print(f"  Total mapping fields     : {len(combined_mapping)}")
    print(f"  Fields compared          : {total_rows}")
    print(f"  Matched / Mismatched     : {match_rows} / {mismatch_rows}")
    print(f"  Missing PPKG/Alex/Both   : {fmp} / {fma} / {fmb}")
    print(f"  Total Blockers           : {total_blockers}")
    if total_rows:
        print(f"  Overall coverage         : {(match_rows / total_rows * 100):.2f}%")
    else:
        print(f"  Overall coverage         : N/A")
    print(f"  New fields PPKG/Alex     : {new_ppkg} / {new_alex}")
    print(f"  Claim type mismatches    : {type_mismatch_count}")
    print(f"  Missing records total    : {len(missing_records_df)}")
    print(f"  Schema coverage paths    : {len(schema_df)}")
    print(f"{'─'*65}\n")

    # ── Write report ──────────────────────────────────────────────────────
    # Relabel EVERYTHING referring to the system-under-test from the internal
    # "Alex" naming to "Decanary" — both column headers AND cell values
    # (status text, failure categories, reasons, metric labels, etc.).
    def _relabel(df: pd.DataFrame) -> pd.DataFrame:
        df = df.rename(columns={
            c: str(c).replace('Alex', 'Decanary').replace('ALEX', 'DECANARY')
            for c in df.columns
        })
        # Replace substrings inside all string/object cells too.
        return df.replace(
            {'Alex': 'Decanary', 'ALEX': 'DECANARY'},
            regex=True,
        )

    consolidated_df    = _relabel(consolidated_df)
    claim_match_df     = _relabel(claim_match_df)
    missing_records_df = _relabel(missing_records_df)
    schema_df          = _relabel(schema_df)
    summary_df         = _relabel(summary_df)
    stats_df           = _relabel(stats_df)
    metrics_df         = _relabel(metrics_df)

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"{consumer_name}_validation_report_{timestamp}.xlsx"
    report_path = os.path.join(report_dir, report_name)

    write_excel_report(
        report_path,
        metrics_df, summary_df, consolidated_df,
        claim_match_df, missing_records_df, schema_df,
        stats_df,
    )
    return report_path


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) >= 2:
        consumer = sys.argv[1]
    elif os.environ.get('CONSUMER_NAME'):
        consumer = os.environ['CONSUMER_NAME']
    else:
        consumer = 'Hospital'
        print(f"⚠️  No consumer specified, defaulting to: {consumer}")
        print(f"   Usage  : python decanary_compare.py <consumer_name>")
        print(f"   Options: {', '.join(CONSUMER_CONFIG.keys())}\n")

    run(consumer)

