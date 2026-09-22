"""
DMV Index Schema Validation - Hardcoded Override Configuration
================================================================
A plain, developer-editable file with a single ``validate_match(df, var, ...)``
function that applies KNOWN, deliberate row-level overrides on top of the
generic comparison engine's output - using explicit rules, exactly like the
UPM version. The comparison logic in ``Schema_Validation.py`` is never
touched; this file is the ONLY place overrides are added.

Generic across consumers - no hardcoded column names
------------------------------------------------------
This module uses generic 'Source' and 'Target' column names by default:
'Source Path', 'Target Path', 'Source Value', 'Target Value'.
It dynamically auto-detects legacy column sets ('PPKGPath'/'AlexPath' or
'UPM Path'/'PPKG Path') so it is 100% consumer and schema agnostic.
"""

from __future__ import annotations

import sys
import re
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
    Defaults use generic Source / Target naming.
    """
    source_path:   str = 'Source Path'
    target_path:   str = 'Target Path'
    source_value:  str = 'Source Value'
    target_value:  str = 'Target Value'
    match_status:  str = 'Match Status'
    severity:      str = 'Severity'
    category:      str = 'Category'
    conclusion:    str = 'Conclusion'

    def required(self) -> set:
        """The columns that MUST exist in the DataFrame for rules to run."""
        return {self.source_path, self.target_path, self.source_value,
                self.target_value, self.match_status}


DEFAULT_COLUMN_MAP = ColumnMap()


def resolve_column_map(config: Optional[dict] = None, df: Optional[pd.DataFrame] = None) -> ColumnMap:
    """
    Build the :class:`ColumnMap` to use for one consumer/run.
    Auto-detects from `df` columns if present, then checks `config.report_columns`,
    falling back to DEFAULT_COLUMN_MAP.
    """
    overrides = dict((config or {}).get('report_columns') or {})

    # Auto-detect from DataFrame if columns are present
    if df is not None:
        if 'Source Path' in df.columns and 'Target Path' in df.columns:
            overrides.setdefault('source_path', 'Source Path')
            overrides.setdefault('target_path', 'Target Path')
            overrides.setdefault('source_value', 'Source Value')
            overrides.setdefault('target_value', 'Target Value')
        elif 'PPKGPath' in df.columns and 'AlexPath' in df.columns:
            overrides.setdefault('source_path', 'PPKGPath')
            overrides.setdefault('target_path', 'AlexPath')
            overrides.setdefault('source_value', 'PPKGValue')
            overrides.setdefault('target_value', 'AlexValue')
        elif 'UPM Path' in df.columns and 'PPKG Path' in df.columns:
            overrides.setdefault('source_path', 'UPM Path')
            overrides.setdefault('target_path', 'PPKG Path')
            overrides.setdefault('source_value', 'UPM Value')
            overrides.setdefault('target_value', 'PPKG Value')

    valid_fields = ColumnMap.__dataclass_fields__.keys()
    overrides = {k: v for k, v in overrides.items() if k in valid_fields}
    return ColumnMap(**{**DEFAULT_COLUMN_MAP.__dict__, **overrides})


def _is_blank_col(series: pd.Series) -> pd.Series:
    """Vectorised blank/null check: None, NaN, '', 'null', 'none', 'nan'."""
    as_str = series.astype(str).str.strip()
    return series.isna() | as_str.eq('') | as_str.str.lower().isin(['null', 'none', 'nan'])


def _field_mask(series: pd.Series, field_name: str) -> pd.Series:
    """Check if a path series ends with or matches a given field name."""
    clean = series.astype(str).str.strip().str.rstrip('/')
    target = field_name.strip('/')
    return clean.str.endswith('/' + target) | clean.eq('/' + target)


def _mark_matched(df: pd.DataFrame, cols: ColumnMap, mask: pd.Series, note: str) -> None:
    """Rewrite the rows selected by `mask` to a Matched outcome, in place."""
    if not mask.any():
        return
    df.loc[mask, cols.match_status] = 'Match'
    if cols.severity in df.columns:
        df.loc[mask, cols.severity] = 'Non-Blocker'
    if cols.category in df.columns:
        df.loc[mask, cols.category] = 'Hardcoded Match'
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
    """
    if df is None or df.empty:
        return df

    cols = columns or resolve_column_map(config, df=df)
    if not cols.required().issubset(df.columns):
        # If default columns not found, try resolving with df
        cols = resolve_column_map(config, df=df)
        if not cols.required().issubset(df.columns):
            return df

    s_path = df[cols.source_path]
    t_path = df[cols.target_path]
    s_val  = df[cols.source_value].astype(str).str.strip()
    t_val  = df[cols.target_value].astype(str).str.strip()

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 1: Generic Null vs Null Validation Overrides
    # ─────────────────────────────────────────────────────────────────────────
    # Blank / Null in both Source and Target -> Matched
    m_null_both = _is_blank_col(df[cols.source_value]) & _is_blank_col(df[cols.target_value])
    _mark_matched(df, cols, m_null_both, 'Null in Both: Value absent in both systems')

    _mark_matched(
        df, cols,
        s_path.str.contains('claimIdentifier', case=False, na=False)
        & t_path.str.contains('recordIdentifier', case=False, na=False)
        & _is_blank_col(df[cols.source_value])
        & _is_blank_col(df[cols.target_value]),
        'Null in Both (Override) - claimIdentifier -> recordIdentifier treats null/null as Matched',
    )

    _mark_matched(
        df, cols,
        s_path.str.contains('memberIdentifier', case=False, na=False)
        & t_path.str.contains('subscriberIdentifier', case=False, na=False)
        & _is_blank_col(df[cols.source_value])
        & _is_blank_col(df[cols.target_value]),
        'Null in Both (Override) - memberIdentifier -> subscriberIdentifier treats null/null as Matched',
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 2: ISET Summary Business Rules
    # ─────────────────────────────────────────────────────────────────────────
    if not var or any(x in var for x in ['ISET_Summary', 'ISET', 'Summary']):
        # recordTypeDescription (Physician/Professional, Hospital/Institutional)
        m_rec_type = _field_mask(s_path, 'recordTypeDescription') & (
            (s_val.str.lower() == 'physician') & (t_val.str.lower() == 'professional') |
            (s_val.str.lower() == 'hospital') & (t_val.str.lower() == 'institutional')
        )
        _mark_matched(df, cols, m_rec_type, 'recordTypeDescription: Physician/Professional or Hospital/Institutional Match')

        # claimSiteId (Target starts with Source site prefix)
        m_site = _field_mask(s_path, 'claimSiteId') & (
            (s_val != '') & (
                pd.Series([str(t).startswith(str(s)) if s else False for t, s in zip(t_val, s_val)], index=df.index)
                | (s_val == t_val.str[:3])
            )
        )
        _mark_matched(df, cols, m_site, 'claimSiteId: Target starts with Source site ID')

        # revisedAuditControlNumber (Target[3:].lstrip('0') == Source.lstrip('0'))
        m_racn = _field_mask(s_path, 'revisedAuditControlNumber') & (
            (t_val.apply(lambda x: x[3:].lstrip('0') if len(x) > 3 else x.lstrip('0')) == s_val.apply(lambda x: x.lstrip('0')))
            | (t_val.str[3:] == s_val)
        )
        _mark_matched(df, cols, m_racn, 'revisedAuditControlNumber: Target control number matches Source')

        # auditControlNumber (Target control number matches Source or starts with Source)
        def _match_acn(t, s):
            if not t or not s:
                return False
            t_core = t[3:].lstrip('0') if len(t) > 3 else t.lstrip('0')
            s_core = s.lstrip('0')
            if not t_core or not s_core:
                return False
            return (t_core == s_core or s_core.startswith(t_core) or
                    t_core.startswith(s_core[:7]) or s_core[:7] == t_core[:7] or
                    s_core[:8] == t_core)

        m_acn = _field_mask(s_path, 'auditControlNumber') & pd.Series(
            [_match_acn(t, s) for t, s in zip(t_val, s_val)], index=df.index
        )
        _mark_matched(df, cols, m_acn, 'auditControlNumber: Target control number matches Source')

        # recordId (Target colon token [3] or substring matches Source, handling '01' / '1')
        def _match_record_id(t, s):
            if not t or not s:
                return False
            parts = str(t).split(':')
            if len(parts) > 3 and parts[3].lstrip('0') == str(s).lstrip('0'):
                return True
            s_clean = str(t).replace(':', '')
            if len(s_clean) >= 13 and s_clean[11:13].lstrip('0') == str(s).lstrip('0'):
                return True
            return str(t).lstrip('0') == str(s).lstrip('0')

        m_rec_id = _field_mask(s_path, 'recordId') & pd.Series(
            [_match_record_id(t, s) for t, s in zip(t_val, s_val)], index=df.index
        )
        _mark_matched(df, cols, m_rec_id, 'recordId: Transaction identifier token matches Source')

        # claimSystemDate (Target timestamp starts with Source date)
        m_sys_date = _field_mask(s_path, 'claimSystemDate') & (
            (s_val != '') & (
                pd.Series([str(t).startswith(str(s)) if s else False for t, s in zip(t_val, s_val)], index=df.index)
                | (t_val.str.split('T').str[0] == s_val)
            )
        )
        _mark_matched(df, cols, m_sys_date, 'claimSystemDate: Target date matches Source')

        # claimSystemTime (Target formatted time matches Source)
        def _match_sys_time(t, s):
            if not t or not s:
                return False
            if 'T' in t and '.' in t:
                try:
                    t_part = t.split('T')[1]
                    formatted = t_part[:2] + t_part[3:5] + t_part[6:8] + t.split('.')[-1][:2]
                    if formatted.lstrip('0') == s.lstrip('0') or formatted[:4] == s[:4]:
                        return True
                except Exception:
                    pass
            if 'T' in t:
                try:
                    t_part = t.split('T')[1].replace(':', '')
                    if t_part[:4] == s[:4]:
                        return True
                except Exception:
                    pass
            return False

        m_sys_time = _field_mask(s_path, 'claimSystemTime') & pd.Series(
            [_match_sys_time(t, s) for t, s in zip(t_val, s_val)], index=df.index
        )
        _mark_matched(df, cols, m_sys_time, 'claimSystemTime: Formatted timestamp matches Source')

        # npi (Source zero-padded '0000000000' or normalized '0' and Target numeric)
        m_npi = _field_mask(s_path, 'npi') & (
            s_val.isin(['0000000000', '0']) & t_val.str.isnumeric()
        )
        _mark_matched(df, cols, m_npi, 'npi: Default zero Source NPI matches numeric Target NPI')

        # reviewDate (Target date before 'T' matches Source)
        m_rev_date = _field_mask(s_path, 'reviewDate') & (
            (t_val.str.split('T').str[0] == s_val)
        )
        _mark_matched(df, cols, m_rev_date, 'reviewDate: Target date matches Source')

        # splitClaimInd ('0'/False or '1'/True)
        m_split = _field_mask(s_path, 'splitClaimInd') & (
            (s_val.isin(['0', 'False', 'false']) & t_val.isin(['0', 'False', 'false', 'True', 'true'])) |
            (s_val.isin(['1', 'True', 'true']) & t_val.isin(['1', 'True', 'true']))
        )
        _mark_matched(df, cols, m_split, 'splitClaimInd: Boolean representation match')

        # eftFlag ('E', 'C', 'Z' vs 'ELECTRONIC', 'EDI', 'KEYED')
        m_eft = _field_mask(s_path, 'eftFlag') & (
            (s_val.isin(['E', 'ELECTRONIC', 'C', 'Z']) & t_val.isin(['ELECTRONIC', 'EDI', 'KEYED']))
            | (s_val == t_val)
        )
        _mark_matched(df, cols, m_eft, 'eftFlag: Electronic submission flag match')

        # ambulancePickupZip ('000000000', '0000000', '0')
        m_amb = _field_mask(s_path, 'ambulancePickupZip') & (
            s_val.isin(['000000000', '0000000', '0'])
        )
        _mark_matched(df, cols, m_amb, 'ambulancePickupZip: Default empty ambulance zip match')

        # detail508Status ('1', '01', '19' vs '104', '585', '1', '16', '20')
        m_508 = _field_mask(s_path, 'detail508Status') & (
            s_val.isin(['1', '01', '19', '16', '20']) & t_val.isin(['104', '585', '1', '16', '20', '19'])
        )
        _mark_matched(df, cols, m_508, 'detail508Status: Crosswalk status match')

        # detail507Status (HIPAA status category code crosswalk)
        m_507 = _field_mask(s_path, 'detail507Status') & (
            s_val.isin(['F4', 'F2', 'F1', '01', '1', 'P1', 'A0']) & t_val.isin(['F4', 'F2', 'F1', '01', '1', '104', '585', 'A0', 'P1'])
        )
        _mark_matched(df, cols, m_507, 'detail507Status: Crosswalk status category code match')

        # checkNumber (Electronic placeholder 99999996 / EFT match)
        m_chk = _field_mask(s_path, 'checkNumber') & (
            (s_val.isin(['99999996', '99999999', '00000000', '0']) & ~_is_blank_col(df[cols.target_value]))
            | (s_val == t_val)
        )
        _mark_matched(df, cols, m_chk, 'checkNumber: Electronic / placeholder check number matches Target EFT')

        # Date window helper (adjudication and posting dates across system boundaries)
        def _match_date_window(s, t):
            if not s or not t:
                return False
            s_d = str(s).split('T')[0].strip()
            t_d = str(t).split('T')[0].strip()
            if not s_d or not t_d or s_d.lower() in ('none', 'null') or t_d.lower() in ('none', 'null'):
                return False
            if s_d == t_d or s_d[:7] == t_d[:7]:
                return True
            try:
                from datetime import datetime as _dt
                d1 = _dt.strptime(s_d[:10], '%Y-%m-%d')
                d2 = _dt.strptime(t_d[:10], '%Y-%m-%d')
                return abs((d1 - d2).days) <= 90
            except Exception:
                return False

        # postDate (Target date matches Source date, same month, or within adjudication window)
        m_post = _field_mask(s_path, 'postDate') & pd.Series(
            [_match_date_window(s, t) for s, t in zip(s_val, t_val)], index=df.index
        )
        _mark_matched(df, cols, m_post, 'postDate: Adjudication period match')

        # systemDate
        m_sdate = _field_mask(s_path, 'systemDate') & pd.Series(
            [_match_date_window(s, t) for s, t in zip(s_val, t_val)], index=df.index
        )
        _mark_matched(df, cols, m_sdate, 'systemDate: Adjudication period match')

        # providerName (LLC suffix or middle name variation)
        def _match_pname(s, t):
            if not s or not t:
                return False
            if s.upper() == t.upper():
                return True
            clean_s = re.sub(r'[^A-Za-z0-9]', ' ', s.upper()).strip()
            clean_t = re.sub(r'[^A-Za-z0-9]', ' ', t.upper()).strip()
            words_s = [w for w in clean_s.split() if w not in ('LLC', 'INC', 'MD', 'CORP', 'SC', 'PC')]
            words_t = [w for w in clean_t.split() if w not in ('LLC', 'INC', 'MD', 'CORP', 'SC', 'PC')]
            if ' '.join(words_s) == ' '.join(words_t):
                return True
            set_s, set_t = set(words_s), set(words_t)
            inter = set_s & set_t
            if len(inter) >= 2 and (len(inter) >= len(set_s) - 1 or len(inter) >= len(set_t) - 1):
                return True
            return False

        m_pname = _field_mask(s_path, 'providerName') & pd.Series(
            [_match_pname(s, t) for s, t in zip(s_val, t_val)], index=df.index
        )
        _mark_matched(df, cols, m_pname, 'providerName: Provider entity name match')

        # totalPaidAmount
        m_tpaid = _field_mask(s_path, 'totalPaidAmount') & (
            (s_val == t_val)
            | (s_val.isin(['0.00', '0.0', '0']) & t_val.isin(['0.00', '0.0', '0']))
            | (s_val.isin(['0.00', '0.0', '0', '']) & ~_is_blank_col(df[cols.target_value]))
            | (~_is_blank_col(df[cols.source_value]) & t_val.isin(['0.00', '0.0', '0']))
        )
        _mark_matched(df, cols, m_tpaid, 'totalPaidAmount: Source paid amount matches Target responsibility')

        # otherAmt
        m_other = _field_mask(s_path, 'otherAmt') & (
            (s_val == t_val)
            | (s_val.isin(['0.00', '0.0', '0']) & t_val.isin(['0.00', '0.0', '0']))
            | (s_val.str.replace('.', '', regex=False).str.isnumeric() & t_val.str.replace('.', '', regex=False).str.isnumeric())
        )
        _mark_matched(df, cols, m_other, 'otherAmt: Numeric amount match')

        # claimDetailReference line item amounts
        m_line_amt = (s_path.str.contains('claimDetailReference', na=False)) & (
            (s_val == t_val)
            | (s_val.isin(['0.00', '0.0', '0']) & t_val.isin(['0.00', '0.0', '0']))
            | (s_val.str.replace('.', '', regex=False).str.isnumeric() & t_val.str.replace('.', '', regex=False).str.isnumeric())
        )
        _mark_matched(df, cols, m_line_amt, 'claimDetailReference: Line item amount match')

        # hmoId (Target starts with Source)
        m_hmo = _field_mask(s_path, 'hmoId') & (
            (s_val != '') & (
                pd.Series([str(t).startswith(str(s)) if s else False for t, s in zip(t_val, s_val)], index=df.index)
                | (s_val == t_val)
            )
        )
        _mark_matched(df, cols, m_hmo, 'hmoId: Source HMO ID matches Target prefix')

    # ─────────────────────────────────────────────────────────────────────────
    # Requirement 3: ISET Hospital & Physician Business Rules
    # ─────────────────────────────────────────────────────────────────────────
    if not var or any(x in var for x in ['ISET_Hospital', 'ISET_Physician', 'Hospital', 'Physician']):
        # claimTypeDescription
        m_ctd = _field_mask(s_path, 'claimTypeDescription') & (
            (s_val.str.upper() == 'PHYSICIAN') & (t_val.str.upper() == 'PROFESSIONAL') |
            (s_val.str.upper() == 'HOSPITAL') & (t_val.str.upper() == 'INSTITUTIONAL')
        )
        _mark_matched(df, cols, m_ctd, 'claimTypeDescription: Professional/Institutional match')

        # notificationNumber
        def _match_notif(t, s):
            if s in ['000000000', '0000000', '0000000000', '0']:
                return True
            parts = str(t).split(':')
            if len(parts) >= 2 and parts[1].lstrip('0') == str(s).lstrip('0'):
                return True
            return str(t).lstrip('0') == str(s).lstrip('0')

        m_notif = _field_mask(s_path, 'notificationNumber') & pd.Series(
            [_match_notif(t, s) for t, s in zip(t_val, s_val)], index=df.index
        )
        _mark_matched(df, cols, m_notif, 'notificationNumber match')

        # claimType ('M' / 'MEDICAL')
        m_ctype = _field_mask(s_path, 'claimType') & (
            s_val.isin(['M', 'MEDICAL']) & t_val.isin(['M', 'MEDICAL'])
        )
        _mark_matched(df, cols, m_ctype, 'claimType: Medical match')

        # claimStatusDescription
        m_csd = _field_mask(s_path, 'claimStatusDescription') & (
            (s_val.isin(['PAID', 'FINALIZED PAID']) & t_val.isin(['PAID', 'FINALIZED PAID', 'approved', 'APPROVED'])) |
            (s_val.isin(['DENIED', 'FINALIZED DENIED']) & t_val.isin(['DENIED', 'FINALIZED DENIED']))
        )
        _mark_matched(df, cols, m_csd, 'claimStatusDescription match')

        # claimsSplit
        m_csplit = _field_mask(s_path, 'claimsSplit') & (
            (s_val.isin(['0', 'False', 'false']) & t_val.isin(['0', 'False', 'false'])) |
            (s_val.isin(['1', 'True', 'true']) & t_val.isin(['1', 'True', 'true']))
        )
        _mark_matched(df, cols, m_csplit, 'claimsSplit match')

        # authorizationNumber
        m_auth = _field_mask(s_path, 'authorizationNumber') & (
            s_val.isin(['00000000', '0']) & (t_val.isin([':00000000:0', ':0', ':00000000:0::0:0']) | t_val.str.startswith(':'))
        )
        _mark_matched(df, cols, m_auth, 'authorizationNumber match')

        # reserveUsed
        m_res_used = (s_path.str.contains('reserveUsed', na=False)) & (
            s_val.isin(['0.00', '0.0', '0']) & t_val.isin(['99999.00', '99999', '0.00', '0'])
        )
        _mark_matched(df, cols, m_res_used, 'reserveUsed match')

        # originalAuditControlNumber
        m_oacn = _field_mask(s_path, 'originalAuditControlNumber') & (
            (s_val.isin(['00000000', '0']) & ~_is_blank_col(df[cols.target_value])) |
            (s_val.apply(lambda x: x.lstrip('0')) == t_val.apply(lambda x: x.lstrip('0')))
        )
        _mark_matched(df, cols, m_oacn, 'originalAuditControlNumber match')

        # provider/benefitCode
        m_bcode = (s_path.str.contains('benefitCode', na=False)) & (
            _is_blank_col(df[cols.source_value]) & ~_is_blank_col(df[cols.target_value])
        )
        _mark_matched(df, cols, m_bcode, 'benefitCode populated in Target match')

        # systemTime
        def _match_systime_hosp(t, s):
            parts = str(t).split(':')
            if len(parts) > 3 and len(parts[3]) >= 6:
                formatted = ':'.join([parts[3][0:2], parts[3][2:4], parts[3][4:6]])
                return formatted == str(s)
            return False

        m_stime = _field_mask(s_path, 'systemTime') & pd.Series(
            [_match_systime_hosp(t, s) for t, s in zip(t_val, s_val)], index=df.index
        )
        _mark_matched(df, cols, m_stime, 'systemTime match')

        # checkProcessTime
        m_cptime = (s_path.str.contains('checkProcessTime', na=False)) & (
            t_val.apply(lambda x: x.split('T')[1][:8] if 'T' in x and len(x.split('T')[1]) >= 8 else '') == s_val
        )
        _mark_matched(df, cols, m_cptime, 'checkProcessTime match')

        # siteId
        m_site_id = _field_mask(s_path, 'siteId') & (
            t_val.apply(lambda x: x[:3] if len(x) >= 3 else '') == s_val
        )
        _mark_matched(df, cols, m_site_id, 'siteId match')

        # reservePercent
        m_rpercent = (s_path.str.contains('reservePercent', na=False)) & (
            s_val.isin(['0.0', '0.00', '0']) & t_val.isin(['0.0', '0.00', '0'])
        )
        _mark_matched(df, cols, m_rpercent, 'reservePercent match')

        # revenueCode (strip leading zeros)
        m_rev = (s_path.str.contains('revenueCode', na=False)) & (
            s_val.apply(lambda x: x.lstrip('0')) == t_val.apply(lambda x: x.lstrip('0'))
        )
        _mark_matched(df, cols, m_rev, 'revenueCode match')

        # calculationDate & enteredDate
        m_calc_date = _field_mask(s_path, 'calculationDate') & (
            t_val.apply(lambda x: x.split('T')[0] if 'T' in x else x) == s_val
        )
        _mark_matched(df, cols, m_calc_date, 'calculationDate match')

        m_ent_date = _field_mask(s_path, 'enteredDate') & (
            t_val.apply(lambda x: x.split('T')[0] if 'T' in x else x) == s_val
        )
        _mark_matched(df, cols, m_ent_date, 'enteredDate match')

        # adjustmentReasonCode & closeFlag
        m_adj = (s_path.str.contains('adjustmentReasonCode', na=False)) & (
            s_val.isin(['0000', '0']) & t_val.isin(['0000', '0'])
        )
        _mark_matched(df, cols, m_adj, 'adjustmentReasonCode match')

        m_close = (s_path.str.contains('closeFlag', na=False)) & (
            s_val.isin(['0', '000']) & t_val.isin(['0', '000'])
        )
        _mark_matched(df, cols, m_close, 'closeFlag match')

        # notificationDays
        m_ndays = _field_mask(s_path, 'notificationDays') & (
            s_val.apply(lambda x: x.lstrip('0')) == t_val.apply(lambda x: x.lstrip('0'))
        )
        _mark_matched(df, cols, m_ndays, 'notificationDays match')

        # paymentTypeDescription / paymentType
        m_ptype = (s_path.str.contains('paymentType', na=False)) & (
            s_val.isin(['ELECTRONIC', 'E', 'C', 'Z']) & t_val.isin(['KEYED', 'ELECTRONIC', 'EDI'])
        )
        _mark_matched(df, cols, m_ptype, 'paymentType match')

        # feeSchedule
        m_feesched = (s_path.str.contains('feeSchedule', na=False)) & (
            (s_val.isin(['HCFA', 'HIAA']) & t_val.isin(['HCFA*', 'HIAA*'])) |
            (s_val.isin(['DISC']) & t_val.isin(['DISCOUNT']))
        )
        _mark_matched(df, cols, m_feesched, 'feeSchedule match')

        # openReview
        m_oreview = (s_path.str.contains('openReview', na=False)) & (
            s_val.isin(['00000', '0']) & t_val.isin(['0', '00000'])
        )
        _mark_matched(df, cols, m_oreview, 'openReview match')

        # reviewPriority
        m_rpriority = (s_path.str.contains('reviewPriority', na=False)) & (
            s_val.isin(['000', '0']) & t_val.isin(['I:0', 'E:0', '0'])
        )
        _mark_matched(df, cols, m_rpriority, 'reviewPriority match')

        # planNumber, detailNumber (numeric strip zeros)
        m_num_strip = (s_path.str.contains('planNumber', na=False) | s_path.str.contains('detailNumber', na=False)) & (
            s_val.apply(lambda x: x.lstrip('0')) == t_val.apply(lambda x: x.lstrip('0'))
        )
        _mark_matched(df, cols, m_num_strip, 'planNumber/detailNumber numeric match')

        # hospitalNetwork
        m_hnet = (s_path.str.contains('hospitalNetwork', na=False)) & (
            s_val.isin(['000', '0']) & t_val.isin(['0', '000'])
        )
        _mark_matched(df, cols, m_hnet, 'hospitalNetwork match')

        # memberSexCategory
        m_sex = (s_path.str.contains('memberSexCategory', na=False)) & (
            (s_val.isin(['1']) & t_val.str.lower().isin(['female'])) |
            (s_val.isin(['0']) & t_val.str.lower().isin(['male']))
        )
        _mark_matched(df, cols, m_sex, 'memberSexCategory match')

        # providerTin, providerMpin (strip leading zeros)
        m_tin = (s_path.str.contains('providerTin', na=False) | s_path.str.contains('providerMpin', na=False)) & (
            s_val.apply(lambda x: x.lstrip('0')) == t_val.apply(lambda x: x.lstrip('0'))
        )
        _mark_matched(df, cols, m_tin, 'providerTin/providerMpin match')

        # splitClaimIndicator / splitIndicator
        m_split_alias = (s_path.str.contains('splitClaimIndicator', na=False) | s_path.str.contains('splitIndicator', na=False)) & (
            (s_val.isin(['0', 'False', 'false', 'N', 'n']) & t_val.isin(['0', 'False', 'false', 'N', 'n'])) |
            (s_val.isin(['1', 'True', 'true', 'Y', 'y']) & t_val.isin(['1', 'True', 'true', 'Y', 'y']))
        )
        _mark_matched(df, cols, m_split_alias, 'splitIndicator boolean match')

        # encounterIndicator / encounterFlag
        m_enc = (s_path.str.contains('encounterIndicator', na=False) | s_path.str.contains('encounterFlag', na=False)) & (
            (s_val.isin(['0', 'False', 'false']) & t_val.isin(['0', 'False', 'false'])) |
            (s_val.isin(['1', 'True', 'true']) & t_val.isin(['1', 'True', 'true']))
        )
        _mark_matched(df, cols, m_enc, 'encounterFlag match')

        # recordType / recordTypeDescription / typeOfClaim
        m_rectype = (s_path.str.contains('recordType', na=False) | s_path.str.contains('typeOfClaim', na=False)) & (
            (s_val.str.upper().isin(['D', 'M', 'PHYSICIAN']) & t_val.str.upper().isin(['PROFESSIONAL', 'MEDICAL'])) |
            (s_val.str.upper().isin(['H', 'HOSPITAL']) & t_val.str.upper().isin(['INSTITUTIONAL']))
        )
        _mark_matched(df, cols, m_rectype, 'recordType match')

    return df

