"""Read approved frozen dashboard inputs; never compute analytical estimates."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import pandas as pd
from . import paths


class DashboardDataError(ValueError):
    """A required dashboard input is missing, changed, or incompatible."""


def _require(condition, message):
    if not condition:
        raise DashboardDataError(message)


def _read_csv(path, *, text=False):
    path = Path(path)
    _require(path.is_file(), f"Required file not found: {path}")
    try:
        options = {"dtype": str, "keep_default_na": False} if text else {}
        return pd.read_csv(path, **options)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise DashboardDataError(f"Cannot read CSV {path}: {exc}") from exc


def _columns(table, required, label):
    missing = sorted(set(required) - set(table.columns))
    _require(not missing, f"{label}: missing columns {missing}")
    _require(not table.empty, f"{label}: table is empty")


def _relative(value):
    name = str(value).strip().replace("\\", "/")
    parts = PurePosixPath(name)
    _require(bool(name) and not parts.is_absolute() and ":" not in name
             and ".." not in parts.parts, f"Invalid source path: {value}")
    return parts.as_posix()


def load_specifications():
    """Preserve literal text, including interaction='None', in specification CSVs."""
    visual = _read_csv(paths.SOURCE_VISUAL_SPEC_PATH, text=True)
    equity = _read_csv(paths.EQUITY_REGISTRY_PATH, text=True)
    regional = _read_csv(paths.REGIONAL_REGISTRY_PATH, text=True)
    _columns(visual, ['visual_id', 'page_order', 'visual_order', 'source_paths',
                     'denominator_note', 'interpretation_boundary'], 'Visual specification')
    common = ['indicator', 'estimate_column', 'denominator', 'denominator_n_column',
              'numerator_n_column', 'ci_lower_column', 'ci_upper_column']
    _columns(equity, common + ['wealth_source', 'travel_source'], 'Equity registry')
    _columns(regional, common + ['region_source', 'group_column', 'psu_column'], 'Regional registry')
    _require(len(visual) == 21 and visual.visual_id.is_unique, 'Expected 21 unique visuals')
    _require(set(visual.page_order) == {'1', '2', '3', '4'}, 'Expected four dashboard pages')
    for label, registry in [('Equity', equity), ('Regional', regional)]:
        _require(len(registry) == 5 and registry.indicator.is_unique,
                 f'{label}: expected five unique indicators')
        _require(registry.ne('').all().all(), f'{label}: registry contains blank values')
    return {'visual': visual, 'equity': equity, 'regional': regional}


def _approved_sources(specifications):
    return {_relative(item) for entry in specifications['visual'].source_paths
            for item in entry.split(';') if item.strip()}


def load_frozen_table(relative_path):
    """Load a blueprint-approved NB4 CSV only after its manifest hash matches."""
    name = _relative(relative_path)
    _require(name in _approved_sources(load_specifications()),
             f'Source is not approved in the visual blueprint: {name}')
    _require(not name.startswith('geography/') and name.endswith('.csv'),
             f'Expected an NB4 CSV, received: {name}')
    root = paths.NB4_OUTPUT_DIR.resolve()
    target = (root / name).resolve()
    _require(target.is_relative_to(root), f'Source is outside the NB4 package: {name}')
    manifest = _read_csv(root / 'FINAL_MANIFEST_SHA256.csv', text=True)
    _columns(manifest, ['file', 'bytes', 'sha256'], 'NB4 manifest')
    selected = manifest.loc[manifest['file'].map(_relative) == name]
    _require(len(selected) == 1, f'Manifest must contain exactly one entry for {name}')
    _require(target.is_file(), f'Required NB4 source not found: {target}')
    row = selected.iloc[0]
    try:
        expected_bytes = int(row['bytes'])
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
    except (ValueError, OSError) as exc:
        raise DashboardDataError(f'Cannot verify {name}: {exc}') from exc
    _require(target.stat().st_size == expected_bytes and digest == row['sha256'].lower(),
             f'Frozen NB4 file differs from its manifest: {name}')
    return _read_csv(target)


def load_geography():
    """Return display geometry and a typed crosswalk; Contested stays non-analytical."""
    _require(paths.DASHBOARD_GEOJSON_PATH.is_file(),
             f'Missing GeoJSON: {paths.DASHBOARD_GEOJSON_PATH}')
    try:
        geography = json.loads(paths.DASHBOARD_GEOJSON_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise DashboardDataError(f'Cannot read GeoJSON: {exc}') from exc
    crosswalk = _read_csv(paths.REGION_CROSSWALK_PATH, text=True)
    _columns(crosswalk, ['source_region', 'source_reg_pcode', 'dashboard_region',
                        'nb4_region', 'analytical_region', 'mapping_rule'], 'Crosswalk')
    flags = crosswalk.analytical_region.str.lower()
    _require(flags.isin(['true', 'false']).all(), 'Crosswalk has invalid analytical flags')
    crosswalk['analytical_region'] = flags.eq('true')
    _require(len(crosswalk) == 15 and crosswalk.dashboard_region.is_unique,
             'Crosswalk must contain 15 unique geography units')
    analytical = crosswalk.loc[crosswalk.analytical_region]
    other = crosswalk.loc[~crosswalk.analytical_region]
    _require(len(analytical) == 14 and analytical.nb4_region.is_unique
             and analytical.nb4_region.ne('').all(), 'Expected 14 unique analytical regions')
    _require(set(other.dashboard_region) == {'Contested'} and other.nb4_region.eq('').all(),
             'Contested must have no analytical NB4 match')
    authoritative = load_frozen_table('dashboard_attendance/region_timing_synthesis.csv')
    _columns(authoritative, ['Region'], 'NB4 regional source')
    _require(len(authoritative) == 14 and authoritative.Region.is_unique
             and set(analytical.nb4_region) == set(authoritative.Region),
             'Crosswalk does not match the 14 NB4 regions')
    _require(isinstance(geography, dict) and geography.get('type') == 'FeatureCollection',
             'Expected a GeoJSON FeatureCollection')
    features = geography.get('features', [])
    _require(isinstance(features, list) and len(features) == 15, 'Expected 15 GeoJSON features')
    lookup = crosswalk.set_index('dashboard_region')
    names = []
    for feature in features:
        _require(isinstance(feature, dict) and feature.get('type') == 'Feature', 'Invalid GeoJSON feature')
        props, geometry = feature.get('properties'), feature.get('geometry')
        _require(isinstance(props, dict) and isinstance(geometry, dict), 'Missing feature properties or geometry')
        name = props.get('region')
        _require(name in lookup.index, f'Unmatched GeoJSON region: {name}')
        expected = lookup.loc[name]
        _require(props.get('analytical_region') is bool(expected.analytical_region)
                 and props.get('source_reg_pcode') == expected.source_reg_pcode
                 and props.get('source_region') == expected.source_region,
                 f'GeoJSON/crosswalk metadata mismatch: {name}')
        _require(geometry.get('type') in {'Polygon', 'MultiPolygon'} and bool(geometry.get('coordinates')),
                 f'Missing polygon coordinates: {name}')
        names.append(name)
    _require(len(set(names)) == 15, 'Duplicate GeoJSON regions')
    return geography, crosswalk


def load_indicator(dimension, indicator):
    """Return the untouched frozen table plus its denominator/column metadata."""
    specs = load_specifications()
    _require(dimension in {'wealth', 'travel', 'region'}, f'Unknown dimension: {dimension}')
    registry = specs['regional' if dimension == 'region' else 'equity']
    selected = registry.loc[registry.indicator == indicator]
    _require(len(selected) == 1, f'Unknown {dimension} indicator: {indicator}')
    metadata = selected.iloc[0].to_dict()
    table = load_frozen_table(metadata[f'{dimension}_source'])
    group = metadata.get('group_column', {'wealth': 'Wealth quintile', 'travel': 'Travel time'}.get(dimension))
    metadata['group_column'] = group
    required = [group] + [metadata[key] for key in ['estimate_column', 'denominator_n_column',
                            'numerator_n_column', 'ci_lower_column', 'ci_upper_column']]
    if dimension == 'region':
        required.append(metadata['psu_column'])
    _columns(table, required, f'{dimension}: {indicator}')
    _require(table[group].notna().all() and table[group].is_unique,
             f'{dimension}: missing or duplicate subgroup labels')
    if dimension == 'region':
        reference = load_frozen_table('dashboard_attendance/region_timing_synthesis.csv')
        _require(set(table[group]) == set(reference.Region), f'Regional indicator mismatch: {indicator}')
    return table, metadata


def validate_dashboard_inputs():
    """Read and verify all 36 blueprint dependencies and all 15 selector options."""
    specs = load_specifications()
    geography, crosswalk = load_geography()
    rows = []
    for _, visual in specs['visual'].iterrows():
        for item in visual.source_paths.split(';'):
            source = _relative(item)
            if source == 'geography/ethiopia_admin1_dashboard.geojson':
                count = len(geography['features'])
            elif source == 'geography/region_name_crosswalk.csv':
                count = len(crosswalk)
            else:
                count = len(load_frozen_table(source))
            rows.append({'visual_id': visual.visual_id, 'source': source, 'rows': count, 'valid': True})
    _require(len(rows) == 36, 'Expected 36 blueprint dependencies')
    for dimension in ['wealth', 'travel', 'region']:
        registry = specs['regional' if dimension == 'region' else 'equity']
        for indicator in registry.indicator:
            load_indicator(dimension, indicator)
    return pd.DataFrame(rows)
