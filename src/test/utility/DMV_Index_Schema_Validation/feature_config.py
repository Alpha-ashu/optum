"""
Feature / Consumer Configuration
================================
This module is the **single place to update the information that comes from a
Karate feature file** (test-data path, mapping sheet, claim filter, API/env
metadata, ...). The comparison / validation / reporting *engine* lives in
``Schema_Validation.py`` and stays 100% generic — it never hardcodes anything
about a specific consumer. When you onboard a new validation you only edit the
data structures below (or drop a ``validation_config/<Name>/config.json`` for
the fully auto-discovered path).

What to update here (per consumer)
----------------------------------
Everything under :data:`CONSUMER_CONFIG` is a plain ``dict`` keyed by the CLI
name you run with. For each entry, fill the values you read off the feature
file / mapping workbook:

    test_data       : CSV of member/claim/icn rows the feature exercises
    claim_filter    : "PHYSICIAN" | "HOSPITAL" | ... | None (validate all)
    claim_type      : folder label under target/All_Responses/<claim_type>
    mapping_sheets  : list of field-mapping .xlsx paths
    # ---- optional metadata (surfaces on the report header) --------------
    feature_file    : path to the .feature (auto-parsed for the fields below)
    feature_name    : Feature: title
    scenario_name   : Scenario: title
    api_url         : the API under test
    environment     : QAE / STAGE / UAT / PROD / ...

Use :data:`NEW_VALIDATION_TEMPLATE` as a copy-paste starting point — every
field marked ``TODO`` is something you pull from the feature file.

The matching-behaviour dictionaries (:data:`CSV_COLUMN_ALIASES`,
:data:`BUSINESS_KEY_FIELDS`, :data:`ARRAY_MATCH_CONFIG`, ...) are the
domain-specific knobs the generic engine reads. They live here so the engine
file contains only generic logic.
"""

from __future__ import annotations

import os
from typing import Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# Project base directory (resolved the same way as the engine / framework).
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if not os.path.exists(os.path.join(BASE_DIR, 'pom.xml')):
    BASE_DIR = os.getcwd().split("src")[0] if "src" in os.getcwd() else os.getcwd()


def _p(*parts: str) -> str:
    """Join path parts under the project base directory."""
    return os.path.join(BASE_DIR, *parts)


# Common locations, defined once so entries below stay short and consistent.
# NOTE: mapping .xlsx files physically live under src/test/resources/... (NOT
# src/test/utility/...) - this path previously pointed at a non-existent
# 'utility/validation_mapping' folder, silently causing every consumer's
# mapping_sheets path to resolve to a missing file.
_TESTDATA_DIR = ('src', 'test', 'resources', 'testdata', 'alex_ppkg')
_MAPPING_DIR = ('src', 'test', 'resources', 'json_mapping', 'ppkg_alex', 'ppkg_alex')
# Feature files exercised by the runner. Two per validation: the SOURCE (PPKG /
# HCP, the "expected" system) and the TARGET (Alex, the "actual" system). Their
# endpoint URL + X-Upstream-Env header are auto-parsed for the report header.
_FEATURE_DIR = ('src', 'test', 'resources', 'feature_files', 'ppkg_alex', 'alex', 'hcp_dev_vs_alex_qae')
# PROD (PPKG) vs QAE (Alex) variant (Physician only today) - same layout as
# _FEATURE_DIR above, different source folder.
_FEATURE_DIR_PROD = ('src', 'test', 'resources', 'feature_files', 'ppkg_alex', 'alex', 'hcp_prod_vs_alex_qae')


# ─────────────────────────────────────────────────────────────────────────────
# Consumer configuration  (folder-style dict — one entry per validation).
# Update / add entries here using details from the feature file.
# ─────────────────────────────────────────────────────────────────────────────
CONSUMER_CONFIG: Dict[str, dict] = {
    "HCPvsAlex_Physician": {
        "test_data":      _p(*_TESTDATA_DIR, "hcp_vs_alex_sample_testdata.csv"),
        "claim_filter":   "PHYSICIAN",
        "claim_type":     "Physician",
        "mapping_sheets": [_p(*_MAPPING_DIR, "hcp_alex_physicianMapping.xlsx")],
        # ── Report metadata (auto-parsed from the feature files below) ──
        "consumer_name":       "PPKG vs Alex",
        "source_feature_file": _p(*_FEATURE_DIR, "physician", "ppkg_dev_physician.feature"),
        "target_feature_file": _p(*_FEATURE_DIR, "physician", "alex_qae_physician.feature"),
        "search_type":         "Claim Search",
    },
    "HCPvsAlex_Hospital": {
        "test_data":      _p(*_TESTDATA_DIR, "hcp_vs_alex_sample_testdata.csv"),
        "claim_filter":   "HOSPITAL",
        "claim_type":     "Hospital",
        "mapping_sheets": [_p(*_MAPPING_DIR, "hcp_alex_hospitalMapping.xlsx")],
        # ── Report metadata (auto-parsed from the feature files below) ──
        "consumer_name":       "PPKG vs Alex",
        "source_feature_file": _p(*_FEATURE_DIR, "hospital", "ppkg_prod_hospital.feature"),
        "target_feature_file": _p(*_FEATURE_DIR, "hospital", "clink.feature"),
        "search_type":         "Claim Search",
    },
    "HCPvsAlex_Summary": {
        "test_data":      _p(*_TESTDATA_DIR, "hcp_vs_alex_sample_testdata.csv"),
        "claim_filter":   None,
        "claim_type":     "Summary",
        "mapping_sheets": [_p(*_MAPPING_DIR, "hcp_alex_summaryMapping.xlsx")],
        # ── Report metadata (auto-parsed from the feature files below) ──
        "consumer_name":       "PPKG vs Alex",
        "source_feature_file": _p(*_FEATURE_DIR, "summary", "ppkg_test_summary.feature"),
        "target_feature_file": _p(*_FEATURE_DIR, "summary", "alex_qae_summary.feature"),
        "search_type":         "Claim Summary Search",
    },
    "HCPvsAlex_Physician_Prod": {
        # PROD (PPKG) vs QAE (Alex) Physician claim details. The feature files
        # write responses to 'All_Responses/{PPKG,Alex}_Responses' directly
        # (no per-claim-type subfolder), hence the explicit response_base
        # override below instead of the target/All_Responses/<claim_type>
        # default.
        "test_data":      _p(*_TESTDATA_DIR, "hcp_alex_physician_prod_data.csv"),
        "claim_filter":   "PHYSICIAN",
        "claim_type":     "Physician_Prod",
        "mapping_sheets": [_p(*_MAPPING_DIR, "hcp_alex_physicianMapping.xlsx")],
        "response_base":  _p('target', 'All_Responses'),
        # ── Report metadata (auto-parsed from the feature files below) ──
        "consumer_name":       "PPKG vs Alex (PROD)",
        "source_feature_file": _p(*_FEATURE_DIR_PROD, "ppkg_prod_physician.feature"),
        "target_feature_file": _p(*_FEATURE_DIR_PROD, "alex_qae_physician.feature"),
        "search_type":         "Claim Search",
    },
    "ISET_Summary": {
        "test_data":      _p("src", "test", "resources", "testdata", "upm_ppkg", "ISET", "summary_testdata.csv"),
        "claim_filter":   None,
        "claim_type":     "Summary",
        "mapping_sheets": [_p("src", "test", "resources", "json_mapping", "legacy_ppkg", "upm_ppkg", "ISET", "ISET_Summary_mapping.xlsx")],
        "response_base":  _p("target", "All_Responses", "ISET"),
        "expected_source": "UPM",
        "actual_source":   "PPKG",
        "sources": {
            "UPM":  {"folder": "UPM_Responses/Summary",  "suffix": "_upm.json"},
            "PPKG": {"folder": "PPKG_Responses/Summary", "suffix": "_ppkg.json"},
        },
        "consumer_name":       "ISET",
        "source_feature_file": _p("src", "test", "resources", "feature_files", "upm_ppkg", "cosmos", "ISET", "summary", "upm_summary.feature"),
        "target_feature_file": _p("src", "test", "resources", "feature_files", "upm_ppkg", "cosmos", "ISET", "summary", "ppkg_summary.feature"),
        "search_type":         "Claim Summary Search",
    },
    "ISET_Hospital": {
        "test_data":      _p("src", "test", "resources", "testdata", "upm_ppkg", "ISET", "hospital_testdata.csv"),
        "claim_filter":   "HOSPITAL",
        "claim_type":     "Hospital",
        "mapping_sheets": [_p("src", "test", "resources", "json_mapping", "legacy_ppkg", "upm_ppkg", "ISET", "ISET_Hospital_mapping.xlsx")],
        "response_base":  _p("target", "All_Responses", "ISET"),
        "expected_source": "UPM",
        "actual_source":   "PPKG",
        "sources": {
            "UPM":  {"folder": "UPM_Responses/Hospital",  "suffix": "_upm.json"},
            "PPKG": {"folder": "PPKG_Responses/Hospital", "suffix": "_ppkg.json"},
        },
        "consumer_name":       "ISET",
        "source_feature_file": _p("src", "test", "resources", "feature_files", "upm_ppkg", "cosmos", "ISET", "read-claim-details", "hospital", "upm_hospital.feature"),
        "target_feature_file": _p("src", "test", "resources", "feature_files", "upm_ppkg", "cosmos", "ISET", "read-claim-details", "hospital", "ppkg_hospital.feature"),
        "search_type":         "Claim Search",
    },
    "ISET_Physician": {
        "test_data":      _p("src", "test", "resources", "testdata", "upm_ppkg", "ISET", "physician_testdata.csv"),
        "claim_filter":   "PHYSICIAN",
        "claim_type":     "Physician",
        "mapping_sheets": [_p("src", "test", "resources", "json_mapping", "legacy_ppkg", "upm_ppkg", "ISET", "ISET_Physician_mapping.xlsx")],
        "response_base":  _p("target", "All_Responses", "ISET"),
        "expected_source": "UPM",
        "actual_source":   "PPKG",
        "sources": {
            "UPM":  {"folder": "UPM_Responses/Physician",  "suffix": "_upm.json"},
            "PPKG": {"folder": "PPKG_Responses/Physician", "suffix": "_ppkg.json"},
        },
        "consumer_name":       "ISET",
        "source_feature_file": _p("src", "test", "resources", "feature_files", "upm_ppkg", "cosmos", "ISET", "read-claim-details", "physician", "upm_physician.feature"),
        "target_feature_file": _p("src", "test", "resources", "feature_files", "upm_ppkg", "cosmos", "ISET", "read-claim-details", "physician", "ppkg_physician.feature"),
        "search_type":         "Claim Search",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Copy-paste template for a NEW validation.
# Copy this dict into CONSUMER_CONFIG under a new key and fill every TODO with
# the value taken from the feature file / mapping workbook. Delete the optional
# metadata keys you do not need — the engine treats them as best-effort.
# ─────────────────────────────────────────────────────────────────────────────
NEW_VALIDATION_TEMPLATE: dict = {
    # ── Required ─────────────────────────────────────────────────────────────
    "test_data":      _p(*_TESTDATA_DIR, "TODO_testdata.csv"),   # TODO
    "claim_filter":   None,                                       # TODO: "PHYSICIAN" / "HOSPITAL" / None
    "claim_type":     "TODO_ClaimType",                           # TODO: folder under target/All_Responses/
    "mapping_sheets": [_p(*_MAPPING_DIR, "TODO_mapping.xlsx")],   # TODO
    # ── Optional metadata (read off the feature file) ────────────────────────
    "feature_file":   None,        # TODO: path to the .feature (auto-parsed)
    "feature_name":   "",          # TODO: Feature: title
    "scenario_name":  "",          # TODO: Scenario: title
    "api_url":        "",          # TODO: API under test
    "environment":    "",          # TODO: QAE / STAGE / UAT / PROD
    # ── Optional: override hardcoding.py's report column names for THIS ──────
    # consumer only (see hardcoding.ColumnMap) - leave out entirely to keep
    # the engine's default column names (PPKGPath/AlexPath/PPKGValue/...).
    # "report_columns": {"source_path": "SourcePath", "target_path": "TargetPath"},
}


# ─────────────────────────────────────────────────────────────────────────────
# CSV column aliases  (canonical name → possible column names in the CSV).
# claimtype is OPTIONAL — only required when a claim_filter is set.
# ─────────────────────────────────────────────────────────────────────────────
CSV_COLUMN_ALIASES: Dict[str, List[str]] = {
    'memberNumber':            ['memberNumber', 'member_number', 'membernumber', 'member', 'MemberNumber'],
    'payerClaimControlNumber': ['payerClaimControlNumber', 'claim_number', 'claimnumber', 'claim', 'PayerClaimControlNumber',
                                'reqClmNbr', 'reqclmnbr', 'clmNbr', 'ClmNbr',
                                'claimNumber', 'ClaimNumber', 'claimNbr', 'ClaimNbr',
                                'reqClaimNumber', 'reqClaimNbr', 'reqClmNumber'],
    'icn':                     ['icn', 'ICN', 'icn_number', 'Icn', 'reqInvnCtlNbr', 'rspInvnCtlNbr', 'InvnCtlNbr', 'invnCtlNbr'],
    'claimtype':               ['claimtype', 'claimType', 'claimType_filter', 'claim_type_filter', 'ClaimType', 'claim_type'],
}

# Columns that are always required in the test-data CSV. Nothing is universally
# required: member number / ICN / claim number are all optional, and a
# validation can name its response files by ANY column via the config
# "identifier_column" knob (e.g. member search uses reqSbmtProvId). This keeps
# the engine fully generic - a new same-shape search reuses it with zero code
# changes, only a config.json.
CSV_REQUIRED_COLUMNS: set = set()


# ─────────────────────────────────────────────────────────────────────────────
# Mapping-sheet column aliases (source-side → target-side path columns).
# The engine resolves the two mapping columns from these aliases (or from a
# per-validation ``mapping_columns`` override) instead of hardcoding a single
# 'PPKG Path' / 'ALEX Path' header — so any two-column mapping workbook works.
# ─────────────────────────────────────────────────────────────────────────────
MAPPING_COLUMN_ALIASES: Dict[str, List[str]] = {
    'source': [
        'PPKG Path', 'PPKGPath', 'Source Path', 'SourcePath', 'Expected Path',
        'HCP Path', 'UPM Path', 'Clink Path', 'Claim360_Path', 'Claim360 Path','SourcePath', 'Source_Path_1',
        'Legacy', 'legacy',
    ],
    'target': [
        'ALEX Path', 'AlexPath', 'Target Path', 'TargetPath', 'Actual Path',
        'Decanary_Path', 'Decanary Path', 'PPKG Target Path','target_path', 'Target_Path_2',
        'pp claim path', 'pp_claim_path', 'PP Claim Path',
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Record-matching configuration (domain knobs read by the generic engine).
# ─────────────────────────────────────────────────────────────────────────────
# Business/identifying leaf fields used to align records across arrays. These
# are the highest-confidence identity keys — tried first when auto-deriving keys
# for any array that has no explicit ARRAY_MATCH_CONFIG entry.
BUSINESS_KEY_FIELDS: List[str] = [
    'claimReviewReversalIdentifier', 'claimReviewIdentifier',
    'claimPaymentAmount', 'paymentTrackingNumber',
    'claimSubmittedServiceIdentifier', 'providerTaxId', 'npi',
]

# Per array container (normalized/wildcarded, 'claim'-rooted JSON pointer), the
# ordered business keys used to align expected vs actual records BEFORE any
# child-field value comparison. Array position is only a fast-path/tie-breaker,
# never the sole proof of identity. Each key spec is either:
#   • a single field name (str)  — matched by case-insensitive substring
#                                   against the record's flattened leaf keys
#   • a tuple of field names     — a COMPOSITE key; ALL fields must be equal
# Specs are tried in priority order; the first spec that matches wins.
ARRAY_MATCH_CONFIG: Dict[str, List] = {
    'claim/*/claimSupportingInformation/sourceSpecificAttributes': [
        'attributeName',
    ],
    'claim/*/serviceLines': [
        # claimSubmittedServiceIdentifier is the unique, mandatory key. Fall
        # back to a composite key only when it is absent, so each submitted
        # service line aligns to exactly one actual record.
        'claimSubmittedServiceIdentifier',
        (
            'claimServiceLineIdentifier',
            'serviceProcedureCode',
            'revenueCode',
        ),
    ],
    'claim/*/insurance/claimReviews': [
        # claimReviewIdentifier is NOT unique — the same identifier repeats
        # across multiple review records. Use a composite key so a review is
        # not reused for multiple expected reviews.
        (
            'claimReviewIdentifier',
            'claimReviewReasonCode',
            'reviewProcessorIdentifier',
        ),
        (
            'claimReviewReasonCode',
            'reviewProcessorIdentifier',
        ),
    ],
    'claim/*/providers': [
        # Providers can share the same NPI / tax id across roles (BILLING vs
        # PAYTO). Composite keys keyed on role keep them distinct. A trailing
        # role-only fallback aligns provider records that carry a role but no
        # npi/taxId (e.g. RENDERING/PAYTO).
        ('npi', 'role'),
        ('providerTaxId', 'role'),
        'role',
    ],
}

# Leaf-key-name fragments that make a field a good business/identity key when
# NO explicit ARRAY_MATCH_CONFIG entry exists for an array container. Used to
# auto-derive keys so EVERY array is aligned by identity instead of position.
# Amount/date-only fields are intentionally excluded — they are values to
# validate, not stable record identities, and would produce false matches.
_GENERIC_KEY_FRAGMENTS = (
    'identifier', 'number', 'code', 'npi', 'taxid', 'name', 'sequence', 'role', 'type',
)


# ─────────────────────────────────────────────────────────────────────────────
# Ignorable missing fields (blocker suppression exception list).
# ─────────────────────────────────────────────────────────────────────────────
# By DEFAULT, any field that exists in PPKG (source of truth) but is genuinely
# absent from Alex (target) - including when the containing array RECORD
# itself is missing at that index - is a BLOCKER ("Missing In Alex"). This
# list is the ONLY way to downgrade a specific field to Non-Blocker instead.
#
# Each entry is matched case-insensitively as a SUBSTRING against either the
# leaf field name or the full normalized/resolved JSON pointer, so both of
# these are valid:
#   "claimAdjudicationTime"                      -> matches the leaf name
#   "claim/*/payments/*/claimAdjudicationTime"   -> matches the full path
#
# Leave EMPTY by default - nothing is ignored unless explicitly added here.
IGNORABLE_MISSING_FIELDS: List[str] = [
    # "someKnownAlexGapField",
]


# ─────────────────────────────────────────────────────────────────────────────
# Value-comparison tuning.
# ─────────────────────────────────────────────────────────────────────────────
# Two textual values are treated as matching when their fuzzy similarity ratio
# is at or above this threshold (1.0 == exact match only).
FUZZY_MATCH_THRESHOLD = 0.95



