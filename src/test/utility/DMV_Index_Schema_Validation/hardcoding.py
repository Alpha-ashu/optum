"""
DMV Index Schema Validation - Hardcoded Override Configuration
================================================================
Same pattern as ``src/test/utility/upm_ppkg_validation/hardcoding.py``: a
plain, developer-editable file with a single ``validate_match(df, var, ...)``
function that applies KNOWN, deliberate row-level overrides on top of the
generic comparison engine's output - using explicit rules, exactly like the
UPM version. The comparison logic in ``Schema_Validation.py`` is never
touched; this file is the ONLY place overrides are added.

Generic across consumers - no hardcoded column names
------------------------------------------------------
Different consumers/reports can use different column names for the same
concept (e.g. one report might call it 'PPKGPath'/'AlexPath', another
'SourcePath'/'TargetPath'). This module NEVER hardcodes a literal column
name. Every rule reads its column names from a :class:`ColumnMap`, which the
caller resolves (see :func:`resolve_column_map`) from the consumer's
``feature_config.py`` entry - keeping this file, and the engine, 100%
consumer-agnostic. Only ``feature_config.py`` (feature file + mapping +
column-name aliases) is ever consumer-specific.

Why this file exists
---------------------
The generic engine compares mapped field pairs value-by-value. Some mapped
pairs are intentionally "null on one side, null on the other" for perfectly
valid business reasons (e.g. the source system's `claimIdentifier` is simply
never populated while the target system's `recordIdentifier` counterpart is
also never populated for that same record type). Reviewers want these treated
as a genuine Match rather than a Blocker/Mismatch.

How to add a new override (same recipe as upm_ppkg_validation/hardcoding.py)
-----------------------------------------------------------------------------
Add a new ``_mark_matched(...)`` block inside :func:`validate_match` below -
no other file needs to change. Use ``cols.source_path`` / ``cols.target_path``
/ ``cols.source_value`` / ``cols.target_value`` instead of a literal column
name so the rule keeps working for every consumer:

    _mark_matched(
        df, cols,
        df[cols.source_path].str.contains('claimIdentifier', case=False, na=False)
        & df[cols.target_path].str.contains('recordIdentifier', case=False, na=False)
        & _is_blank_col(df[cols.source_value])
        & _is_blank_col(df[cols.target_value]),
        'Null in Both (Override) - claimIdentifier -> recordIdentifier treats null/null as Matched',
    )

Scope a rule to a specific consumer (optional) exactly like UPM's
``if var in [...]:`` blocks - just wrap the ``_mark_matched(...)`` call:

    if var in ["HCPvsAlex_Physician", "HCPvsAlex_Hospital"]:
        _mark_matched(df, cols, mask, note)

Integration point
------------------
``Schema_Validation.py`` calls :func:`validate_match` exactly ONCE, immediately
after the consolidated comparison DataFrame is built and BEFORE the report is
written, passing the consumer's config so column names resolve automatically.
That is the only line Schema_Validation.py needs; every rule lives here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Generic column-name resolution (consumer-agnostic)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ColumnMap:
    """
    The set of column names this module needs, resolved once per consumer.
    Defaults match the DMV Schema_Validation.py engine's CONSOLIDATED_COLUMNS
    so existing behaviour is unchanged when a consumer supplies no overrides.
    """
    source_path:   str = 'PPKGPath'
    target_path:   str = 'AlexPath'
    source_value:  str = 'PPKGValue'
    target_value:  str = 'AlexValue'
    match_status:  str = 'Match Status'
    severity:      str = 'Severity'
    category:      str = 'Category'
    conclusion:    str = 'Conclusion'

    def required(self) -> set:
        """The columns that MUST exist in the DataFrame for rules to run."""
        return {self.source_path, self.target_path, self.source_value,
                self.target_value, self.match_status}


# Default column map, used when a consumer supplies no 'report_columns'
# override in feature_config.py. Kept as a module-level constant (not a
# hardcoded literal inside validate_match) so it is overridden in ONE place.
DEFAULT_COLUMN_MAP = ColumnMap()


def resolve_column_map(config: Optional[dict] = None) -> ColumnMap:
    """
    Build the :class:`ColumnMap` to use for one consumer/run.

    `config` is the CONSUMER_CONFIG entry from ``feature_config.py``. If it
    carries an optional ``report_columns`` dict (any subset of the
    :class:`ColumnMap` field names), those values override the defaults for
    THIS consumer only - e.g.:

        "SomeConsumer": {
            ...
            "report_columns": {"source_path": "SourcePath", "target_path": "TargetPath"},
        }

    Consumers that specify nothing keep the engine's current column names.
    """
    overrides = dict((config or {}).get('report_columns') or {})
    valid_fields = ColumnMap.__dataclass_fields__.keys()
    overrides = {k: v for k, v in overrides.items() if k in valid_fields}
    return ColumnMap(**{**DEFAULT_COLUMN_MAP.__dict__, **overrides})


def _is_blank_col(series: pd.Series) -> pd.Series:
    """Vectorised blank/null check: None, NaN, '', 'null', 'none', 'nan'."""
    as_str = series.astype(str).str.strip()
    return series.isna() | as_str.eq('') | as_str.str.lower().isin(['null', 'none', 'nan'])


def _mark_matched(df: pd.DataFrame, cols: ColumnMap, mask: pd.Series, note: str) -> None:
    """Rewrite the rows selected by `mask` to a Matched outcome, in place.

    Unlike UPM's df (which only carries a single Match-Status-style column),
    the DMV consolidated DataFrame also drives Severity/Category/Conclusion
    for the Summary sheet, cell colouring and the Validation Summary counts -
    so those are kept in sync here too, using the SAME resolved column names
    as everything else (no literal column names). This helper is called from
    the rule blocks below; it does not change the rule-writing style, only
    avoids repeating these column assignments in every block.
    """
    if not mask.any():
        return
    df.loc[mask, cols.match_status] = 'Match'
    if cols.severity in df.columns:
        df.loc[mask, cols.severity] = 'Non-Blocker'
    if cols.category in df.columns:
        df.loc[mask, cols.category] = 'Match'
    if cols.conclusion in df.columns:
        df.loc[mask, cols.conclusion] = note


def validate_match(
    df: pd.DataFrame,
    var: str = None,
    columns: Optional[ColumnMap] = None,
    config: Optional[dict] = None,
) -> pd.DataFrame:
    """
    DMV Index Schema Validation - hardcoded override rules.

    Same shape as ``upm_ppkg_validation.hardcoding.validate_match(df, var)``,
    with the addition of a generic, per-consumer resolved `columns` map so
    this function never needs to know a literal column name:

    - `var`     : the consumer/validation name, e.g. 'HCPvsAlex_Physician'.
                  Accepted for parity with the UPM signature and to let a
                  rule be scoped with ``if var in [...]:`` exactly like UPM.
    - `columns` : a resolved :class:`ColumnMap`. If omitted, it is resolved
                  from `config` (the consumer's feature_config.py entry) via
                  :func:`resolve_column_map`, falling back to the engine's
                  current column names when neither is supplied.
    """
    cols = columns or resolve_column_map(config)
    if df is None or df.empty or not cols.required().issubset(df.columns):
        return df

    # Requirement 1: Null vs Null Validation Override
    # $.claimIdentifier -> $.recordIdentifier
    _mark_matched(
        df, cols,
        df[cols.source_path].str.contains('claimIdentifier', case=False, na=False)
        & df[cols.target_path].str.contains('recordIdentifier', case=False, na=False)
        & _is_blank_col(df[cols.source_value])
        & _is_blank_col(df[cols.target_value]),
        'Null in Both (Override) - claimIdentifier -> recordIdentifier treats null/null as Matched',
    )

    # $.memberIdentifier -> $.subscriberIdentifier
    _mark_matched(
        df, cols,
        df[cols.source_path].str.contains('memberIdentifier', case=False, na=False)
        & df[cols.target_path].str.contains('subscriberIdentifier', case=False, na=False)
        & _is_blank_col(df[cols.source_value])
        & _is_blank_col(df[cols.target_value]),
        'Null in Both (Override) - memberIdentifier -> subscriberIdentifier treats null/null as Matched',
    )

    return df

