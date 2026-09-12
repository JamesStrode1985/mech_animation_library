"""Shared, project-relative configuration for independent mech libraries."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def libraries():
    registry = json.loads((ROOT / 'data/mechs.json').read_text(encoding='utf-8'))
    return [(mech, json.loads((ROOT / mech['manifest']).read_text(encoding='utf-8')))
            for mech in registry['mechs']]


def pages_for(mech, data):
    # Retain the established Hellcat entry point and revision bookmark.
    return [mech['page']] + ([f"revision_{data['revision']}.html"]
                             if mech['id'] == 'hellcat' else [])
