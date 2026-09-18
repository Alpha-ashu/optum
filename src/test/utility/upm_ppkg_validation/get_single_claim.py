
import json
import os

def get_claim(upm_path, ppkg_path):
    """Load JSON data from upm and pp_claim files."""
    with open(upm_path) as f:
        upm = json.load(f)
    with open(ppkg_path) as f:
        pp_claim = json.load(f)
    return upm, pp_claim

def get_nested_value(data, path):
    """Safely traverse nested dictionaries and lists using a path."""
    for key in path:
        if isinstance(data, dict):
            data = data.get(key)
        elif isinstance(data, list):
            if data:
                data = data[0]
            else:
                return None
        else:
            return None
    return data

def _norm(value):
    """Normalize a value for comparison (string, trimmed, upper-case)."""
    if value is None:
        return ""
    return str(value).strip().upper()


def _claim_identifiers(claim):
    """
    Build every identifier a claim can legitimately be referenced by.

    Response files are named '<seq>_<claimSiteId><auditControlNumber>_upm.json'
    (e.g. '01_KLC1147381400_upm.json'), but inside the JSON the site id and the
    audit control number are stored in SEPARATE fields:
        claimSiteId              = 'KLC'
        auditControlNumber       = '1147381400'
    So a plain equality check against 'KLC1147381400' never matches. We
    therefore also generate the site-prefixed (concatenated) variants.
    """
    site = _norm(claim.get("claimSiteId"))
    identifiers = set()

    for field in ("claimNumber", "auditControlNumber", "revisedAuditControlNumber"):
        raw = _norm(claim.get(field))
        if not raw:
            continue
        identifiers.add(raw)
        if site:
            identifiers.add(site + raw)          # e.g. KLC1147381400

    return identifiers


def _matches(claim, claim_number):
    """True when the claim can be identified by claim_number."""
    if not isinstance(claim, dict):
        return False

    target = _norm(claim_number)
    if not target:
        return False

    identifiers = _claim_identifiers(claim)
    if target in identifiers:
        return True

    # Fall back: strip a leading 3-letter site code from the target
    # (handles 'KLC1147381400' -> '1147381400' when claimSiteId is absent)
    if len(target) > 3 and target[:3].isalpha():
        if target[3:] in identifiers:
            return True

    return False


def filter_claim_by_number(data, path, claim_number, var):
    """Filter and return a claim based on claim number and type."""
    claims = get_nested_value(data, path)

    if isinstance(claims, list):
        for claim in claims:
            if _matches(claim, claim_number):
                return claim

    elif isinstance(claims, dict):
        if _matches(claims, claim_number):
            return claims

    print(f"No matching claim found for claim number '{claim_number}' and type '{var}'.")
    return None

if __name__ == '__main__':
    print('get_single_claim')