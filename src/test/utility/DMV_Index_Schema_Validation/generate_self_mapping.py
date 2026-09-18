"""
Self-Mapping Sheet Generator (direct-mode validations)
======================================================
For a "direct" comparison (PPKG vs Alex hitting the SAME API, identical
response shape) the field mapping is simply every leaf JSON pointer mapped to
itself. Curated mapping sheets (e.g. the Clink Summary sheet) are authored by
hand, but detail validations (Hospital / Physician) have no sheet yet.

This utility builds that self-mapping sheet automatically from a real PPKG
response so a direct-mode validation can run with zero hand-authored mapping.

Behaviour (fully generic, no hardcoding):
  * Resolve the consumer config exactly like Schema_Validation.py does
    (static feature_config.CONSUMER_CONFIG + discovered validation_config/*).
  * If the configured mapping sheet ALREADY exists -> do nothing (never clobber
    a curated sheet such as the Summary mapping).
  * Otherwise, enumerate every wildcard leaf pointer from the first available
    PPKG response JSON and write a two-column ('PPKG Path', 'ALEX Path')
    self-mapping .xlsx at the configured mapping-sheet path.

Usage:
    python generate_self_mapping.py <consumer_name>
"""

from __future__ import annotations

import os
import sys
import json
import glob

# Reuse the SAME config resolution + pointer extraction as the engine so the
# generated sheet always matches what the validator will read.
try:
    import feature_config as _fc
except ImportError:  # pragma: no cover - path fallback
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'feature_config', os.path.join(os.path.dirname(__file__), 'feature_config.py'))
    _fc = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_fc)

try:
    import validation_framework as _vf
except ImportError:  # pragma: no cover - path fallback
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'validation_framework', os.path.join(os.path.dirname(__file__), 'validation_framework.py'))
    _vf = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_vf)

try:
    import Schema_Validation as _sv
except ImportError:  # pragma: no cover - path fallback
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        'Schema_Validation', os.path.join(os.path.dirname(__file__), 'Schema_Validation.py'))
    _sv = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_sv)


BASE_DIR = _fc.BASE_DIR


def _resolve_config(consumer_name: str) -> dict:
    """Return the merged config for a consumer (static + discovered)."""
    config = dict(_fc.CONSUMER_CONFIG)
    try:
        config.update(_vf.discover_validation_configs())
    except Exception:
        pass
    if consumer_name not in config:
        raise SystemExit(f"[self-mapping] Unknown consumer: '{consumer_name}'")
    return config[consumer_name]


def generate(consumer_name: str) -> None:
    cfg = _resolve_config(consumer_name)

    # Only relevant for direct-mode validations (self-mapping makes no sense for
    # the claim-array PPKG-vs-Alex mode).
    if str(cfg.get('comparison_mode', '')).strip().lower() != 'direct':
        print(f"[self-mapping] {consumer_name} is not direct-mode - skipping.")
        return

    mapping_sheets = cfg.get('mapping_sheets') or []
    if not mapping_sheets:
        print(f"[self-mapping] {consumer_name} has no mapping_sheets configured - skipping.")
        return
    sheet_path = mapping_sheets[0]
    if not os.path.isabs(sheet_path):
        sheet_path = os.path.join(BASE_DIR, sheet_path)

    if os.path.exists(sheet_path):
        print(f"[self-mapping] Mapping sheet already exists, leaving it untouched: {sheet_path}")
        return

    # Locate a representative PPKG response to enumerate pointers from.
    expected_source = cfg.get('expected_source', 'PPKG')
    sources_cfg     = cfg.get('sources') or {}
    expected_folder = (sources_cfg.get(expected_source) or {}).get('folder', 'PPKG_Responses')
    claim_type      = cfg.get('claim_type') or ''
    resp_root = cfg.get('response_base') or os.path.join(BASE_DIR, 'target', 'All_Responses', claim_type)
    if not os.path.isabs(resp_root):
        resp_root = os.path.join(BASE_DIR, resp_root)
    ppkg_dir = os.path.join(resp_root, expected_folder)

    candidates = sorted(glob.glob(os.path.join(ppkg_dir, '*.json')))
    if not candidates:
        print(f"[self-mapping] No PPKG responses found in {ppkg_dir} - run the feature first. Skipping.")
        return

    # Merge pointers from every response so array/optional fields present in any
    # claim are all covered.
    pointers: dict = {}
    for path in candidates:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError, OSError):
            continue
        for p in _sv.extract_all_paths_generic(data).keys():
            pointers.setdefault(p, None)

    if not pointers:
        print(f"[self-mapping] Could not extract any pointers from PPKG responses in {ppkg_dir}. Skipping.")
        return

    ordered = ['/' + p for p in pointers.keys()]

    try:
        import pandas as pd
    except ImportError:
        raise SystemExit("[self-mapping] pandas is required to write the mapping sheet.")

    os.makedirs(os.path.dirname(sheet_path), exist_ok=True)
    df = pd.DataFrame({'PPKG Path': ordered, 'ALEX Path': ordered})
    df.to_excel(sheet_path, index=False, engine='openpyxl')
    print(f"[self-mapping] Wrote {len(ordered)} self-mapped pointers -> {sheet_path}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python generate_self_mapping.py <consumer_name>")
    generate(sys.argv[1])

