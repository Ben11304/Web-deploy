#!/usr/bin/env python3
"""
Build static site for GitHub Pages deployment.

Usage:
    python build_static.py                    # Build to docs/
    python build_static.py --data-url ./data  # Custom data base URL

Uses Jinja2 to render templates identically to the Flask app.
"""

import argparse
import json
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# ──────────────────────────────────────────
# Config
# ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / 'app'
TEMPLATES_DIR = APP_DIR / 'templates'
STATIC_DIR = APP_DIR / 'static'
GEOJSON_DIR = STATIC_DIR / 'geojson'
OUTPUT_DIR = PROJECT_ROOT / 'docs'

BUNDLE_DATA = [
    'us-states.geojson',
    'us-counties.geojson',
    'impact',
    'social_vulnerability',
]

# ──────────────────────────────────────────
# Discover data (same logic as app.py)
# ──────────────────────────────────────────
def discover_states():
    states_dir = GEOJSON_DIR / 'states'
    states = []
    if states_dir.exists():
        for item in states_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                folder = item.name
                states.append({'folder': folder, 'value': folder, 'display': folder.replace('_', ' ').title()})
        states.sort(key=lambda x: x['display'])
    return states


def discover_sectors():
    sectors_file = PROJECT_ROOT / 'vulnerability' / 'cisa_osm_mapping.json'
    sectors = []
    if sectors_file.exists():
        with open(sectors_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for sector in data.get('critical_infrastructure_sectors', []):
            name = sector.get('sector', '')
            if name:
                file_name = name.replace(' ', '_').replace(',', '_').replace('__', '_').lower()
                sectors.append({'display': name, 'value': file_name})
    return sectors


def discover_wildfire_states():
    wildfire_dir = GEOJSON_DIR / 'Hazard' / 'wildfire'
    states = []
    if wildfire_dir.exists():
        for f in wildfire_dir.glob('*.geojson'):
            states.append(f.stem)
        states.sort()
    return states


# ──────────────────────────────────────────
# Build all config (mirrors app.py exactly)
# ──────────────────────────────────────────
def build_template_context(states, sectors):
    heatmap_sectors = []
    for s in sectors:
        parts = s['value'].split('_')
        heatmap_name = '_'.join(w.capitalize() for w in parts)
        heatmap_sectors.append({'display': s['display'], 'value': heatmap_name})

    return {
        'available_states': states,
        'sectors': sectors,
        'heatmap_sectors': heatmap_sectors,
        'hazard_types': [
            {'display': '🌊 Flood Hazard', 'value': 'flood'},
            {'display': '🔥 Wildfire Historical', 'value': 'wildfire'},
            {'display': '🏜️ Drought Monitor', 'value': 'drought'},
            {'display': '🌋 Earthquake', 'value': 'earthquake'},
        ],
        'impact_types': [
            {'display': '⚡ Power Outage 2022', 'value': 'poweroutage_2022'},
            {'display': '⚡ Power Outage 2024', 'value': 'poweroutage_2024'},
        ],
        'energy_vulnerability_config': {
            'display': '⚡ Energy Vulnerability',
            'value': 'energy_vulnerability',
            'description': 'Power grid vulnerability analysis',
            'geojson_file': 'heatmap/energy_vulnerability_heatmap.geojson',
            'metric_field': 'normalized_score',
            'criticality_field': 'criticality',
        },
        'exposure_types': [
            {'display': '🌊 Flood Exposure', 'value': 'flood'},
            {'display': '🌋 Earthquake MMI', 'value': 'earthquake'},
            {'display': '🔥 Wildfire Exposure', 'value': 'wildfire'},
        ],
        'exposure_asset_types': [
            {'display': 'Plant', 'value': 'plant', 'default_visible': True},
            {'display': 'Substation', 'value': 'substation', 'default_visible': True},
            {'display': 'Line', 'value': 'line', 'default_visible': True},
            {'display': 'Tower', 'value': 'tower', 'default_visible': False},
            {'display': 'Generator', 'value': 'generator', 'default_visible': True},
            {'display': 'Pipeline', 'value': 'pipeline', 'default_visible': True},
            {'display': 'Fuel Station', 'value': 'fuel', 'default_visible': True},
            {'display': 'Other', 'value': 'other', 'default_visible': True},
        ],
        'energy_detail_asset_types': [
            {'display': '🏭 Plant', 'value': 'plant', 'default_visible': True, 'color': '#FF5722'},
            {'display': '⚡ Substation', 'value': 'substation', 'default_visible': True, 'color': '#9C27B0'},
            {'display': '🔌 Line', 'value': 'line', 'default_visible': True, 'color': '#2196F3'},
            {'display': '📡 Tower', 'value': 'tower', 'default_visible': False, 'color': '#607D8B'},
            {'display': '🔋 Generator', 'value': 'generator', 'default_visible': True, 'color': '#4CAF50'},
            {'display': '🛢️ Pipeline', 'value': 'pipeline', 'default_visible': True, 'color': '#795548'},
            {'display': '⛽ Fuel Station', 'value': 'fuel', 'default_visible': True, 'color': '#E91E63'},
            {'display': '📦 Other', 'value': 'other', 'default_visible': True, 'color': '#9E9E9E'},
        ],
        'earthquake_distance_rings': [
            {'display': '0-5 km', 'value': 5, 'inner': 0, 'outer': 5, 'color': '#FF0000'},
            {'display': '5-10 km', 'value': 10, 'inner': 5, 'outer': 10, 'color': '#FF4500'},
            {'display': '10-25 km', 'value': 25, 'inner': 10, 'outer': 25, 'color': '#FFA500'},
            {'display': '25-50 km', 'value': 50, 'inner': 25, 'outer': 50, 'color': '#FFD700'},
            {'display': '50-100 km', 'value': 100, 'inner': 50, 'outer': 100, 'color': '#ADFF2F'},
            {'display': '100-200 km', 'value': 200, 'inner': 100, 'outer': 200, 'color': '#90EE90'},
        ],
        'svi_config': {
            'display': '🏘️ Social Vulnerability (CDC SVI)',
            'value': 'social_vulnerability',
            'description': 'CDC/ATSDR Social Vulnerability Index 2022',
            'geojson_file': 'social_vulnerability/svi_us_county.geojson',
            'score_field': 'RPL_THEMES',
            'population_field': 'E_TOTPOP',
            'region': 'United States',
            'year': 2022,
        },
        'svi_metrics': [
            {'display': 'Overall SVI', 'value': 'RPL_THEMES'},
            {'display': 'Socioeconomic Status', 'value': 'RPL_THEME1'},
            {'display': 'Household Characteristics', 'value': 'RPL_THEME2'},
            {'display': 'Racial & Ethnic Minority', 'value': 'RPL_THEME3'},
            {'display': 'Housing Type & Transportation', 'value': 'RPL_THEME4'},
        ],
        'wildfire_year_range': {'min': 1984, 'max': 2024},
        'wildfire_states': discover_wildfire_states(),
    }


# ──────────────────────────────────────────
# Render index.html (identical to Flask /)
# ──────────────────────────────────────────
def render_index(env, ctx):
    template = env.get_template('index.html')
    return template.render(**ctx)


# ──────────────────────────────────────────
# Render map.html for EACH view_type as separate pages,
# PLUS a universal map.html that reads URL params client-side
# ──────────────────────────────────────────
def render_map_page(env, ctx, view_type, selected_regions=None):
    """Render map.html with specific view_type context (like Flask /map route)."""
    template = env.get_template('map.html')

    # Build same context as Flask show_map() route
    map_ctx = dict(ctx)
    map_ctx.update({
        'mode': 'select',
        'division_type': 'state',
        'selected_regions': selected_regions or [],
        'selected_sectors': [],
        'view_type': view_type,
        'heatmap_sector': 'combined',
        'hazard_type': 'flood',
        'wildfire_year_start': '1984',
        'wildfire_year_end': '2024',
        'impact_type': 'poweroutage_2022',
        'impact_metric': 'total_customers',
        'energy_vulnerability_type': 'energy_vulnerability',
        'exposure_type': 'flood',
        'exposure_assets': [a['value'] for a in ctx['exposure_asset_types'] if a['default_visible']],
        'energy_detail_assets': [a['value'] for a in ctx['energy_detail_asset_types'] if a['default_visible']],
        'energy_detail_lod': '100',
        'earthquake_rings': ['5', '10', '25', '50', '100', '200'],
        'svi_metric': 'RPL_THEMES',
        'show_background': True,
        'use_geotiff': False,
        'geojson_base_path': 'states',
        'embed': False,
    })
    return template.render(**map_ctx)


# ──────────────────────────────────────────
# Post-process: fix paths for static site
# ──────────────────────────────────────────
def fix_paths(html, data_url, ctx=None):
    """Replace Flask paths with static site paths."""
    ctx = ctx or {}
    import re

    # Fix navigation
    html = html.replace('href="/"', 'href="index.html"')
    html = html.replace("href='/'", "href='index.html'")
    html = html.replace('action="/map"', 'action="map.html"')

    # 1) GeoJSON data paths → DATA_BASE_URL (MUST run BEFORE general /static/ fix)
    #    Matches: '/static/geojson/  "/static/geojson/  `/static/geojson/
    #    Also:    './static/geojson/  "../static/geojson/
    html = re.sub(r"'(?:\.\./|\./|/)?static/geojson/", "window.DATA_BASE_URL + '/", html)
    html = re.sub(r'"(?:\.\./|\./|/)?static/geojson/', 'window.DATA_BASE_URL + "/', html)
    html = re.sub(r'`(?:\.\./|\./|/)?static/geojson/', '`${window.DATA_BASE_URL}/', html)

    # 2) Other static paths → ./static/
    while "../static/" in html:
        html = html.replace("../static/", "./static/")
    html = re.sub(r'(?<!\.)(?<!\.\.)\/static\/', './static/', html)

    # 3) Inject site-config.js before other scripts
    html = html.replace(
        '<script src="./static/js/map-utils.js"></script>',
        '<script src="./static/js/site-config.js"></script>\n    <script src="./static/js/map-utils.js"></script>'
    )

    # 4) Fix Jinja2-baked loops: replace empty functions with JS-driven versions
    #    Jinja2 loops like {% for region in selected_regions %} render empty at build time
    #    because selected_regions=[]. Replace with MAP_CONFIG.selectedRegions JS loops.
    import re as re2

    # Fix all Jinja2-baked load totals
    html = re2.sub(
        r'var heatmapLoadTotal = \d+;',
        'var heatmapLoadTotal = MAP_CONFIG.selectedRegions.length;',
        html
    )
    html = re2.sub(
        r'var hazardLoadTotal = \d+;',
        'var hazardLoadTotal = MAP_CONFIG.selectedRegions.length;',
        html
    )

    # Fix empty loadIndividualStateHeatmaps
    marker_start = 'function loadIndividualStateHeatmaps() {'
    marker_end = '\n}\n\n// Load Energy Sector County Scale data'
    if marker_start in html and marker_end in html:
        start_idx = html.index(marker_start)
        end_idx = html.index(marker_end) + len('\n}')
        js_load_fn = '''function loadIndividualStateHeatmaps() {
    heatmapLoadCount = 0;
    showGlobalLoading('Loading heatmap data...', heatmapLoadTotal);
    MAP_CONFIG.selectedRegions.forEach(function(regionName) {
        var heatmapSectorLocal = MAP_CONFIG.heatmapSector || "combined";
        updateGlobalLoading('Loading heatmap for ' + regionName + '...', false);
        if (heatmapSectorLocal === 'energy_county_scale') {
            loadEnergyCountyScale(regionName);
            return;
        }
        loadGeoJSONHeatmap(regionName);
    });
}'''
        html = html[:start_idx] + js_load_fn + html[end_idx:]

    # Fix empty loadHazardHeatmaps (same Jinja2 loop issue)
    marker_start2 = 'function loadHazardHeatmaps() {'
    # Find the end of this function by looking for the next top-level function
    if marker_start2 in html:
        start_idx2 = html.index(marker_start2)
        # Find matching closing brace — the function ends before the next top-level comment/function
        # Search for the pattern of calling loadHazardHeatmaps() at the end
        call_marker = 'loadHazardHeatmaps();'
        if call_marker in html[start_idx2:]:
            call_idx = html.index(call_marker, start_idx2)
            # Replace from function start to just before the call
            js_hazard_fn = '''function loadHazardHeatmaps() {
    console.log('=== Starting hazard heatmap loading ===');
    var hazardLoadTotal = MAP_CONFIG.selectedRegions.length;
    var hazardLoadCount = 0;
    var hazardNames = {'flood': 'Flood', 'drought': 'Drought', 'wildfire': 'Wildfire', 'earthquake': 'Earthquake'};
    showGlobalLoading('Loading ' + (hazardNames[hazardType] || hazardType) + ' data...', hazardLoadTotal);

    MAP_CONFIG.selectedRegions.forEach(function(regionName) {
        var regionFolders = findRegionFolder(regionName);
        var gridSizeVariants = ['5.0km', '5km'];
        var hazardUrls = [];
        regionFolders.forEach(function(folder) {
            gridSizeVariants.forEach(function(gridSize) {
                hazardUrls.push(window.DATA_BASE_URL + '/heatmap_' + hazardType + '_lite/' + folder + '/' + hazardType + '_heatmap_' + gridSize + '.geojson');
                hazardUrls.push(window.DATA_BASE_URL + '/heatmap_' + hazardType + '/' + folder + '/' + hazardType + '_heatmap_' + gridSize + '.geojson');
            });
        });

        function tryLoadHazard(urls) {
            if (urls.length === 0) {
                console.warn('No hazard data found for ' + regionName);
                hazardLoadCount++;
                if (hazardLoadCount >= hazardLoadTotal) hideGlobalLoading(500);
                return;
            }
            var url = urls.shift();
            fetch(url).then(function(r) {
                if (r.ok) return r.json();
                throw new Error(r.status);
            }).then(function(data) {
                console.log('Loaded hazard for ' + regionName + ':', data.features ? data.features.length : 0, 'features');
                var features = data.features || [];
                HazardLOD.registerLayer(null, features);
                var layer = L.geoJSON(data, {
                    style: function(feature) {
                        var score = feature.properties[hazardType + '_score_normalized'] || 0;
                        return { color: 'transparent', weight: 0, fillColor: getHazardColor(score, hazardType), fillOpacity: 0.7 };
                    },
                    onEachFeature: function(feature, layer) {
                        var score = feature.properties[hazardType + '_score_normalized'] || 0;
                        layer.bindPopup('<strong>Grid</strong><br>' + hazardType + ' Risk: ' + (score * 100).toFixed(1) + '%');
                    }
                }).addTo(map);
                HazardLOD.hazardLayers.push(layer);
                hazardLoadCount++;
                updateGlobalLoading('Loaded ' + regionName + ' (' + hazardLoadCount + '/' + hazardLoadTotal + ')', false);
                if (hazardLoadCount >= hazardLoadTotal) hideGlobalLoading(500);
            }).catch(function() { tryLoadHazard(urls); });
        }
        tryLoadHazard(hazardUrls);
    });
}

'''
            html = html[:start_idx2] + js_hazard_fn + html[call_idx:]

    # 5) Inject URL param override AFTER MAP_CONFIG definition
    url_override_js = '''
        // === URL param override (static site) ===
        (function() {
            var p = new URLSearchParams(window.location.search);
            if (p.getAll('region').length > 0) MAP_CONFIG.selectedRegions = p.getAll('region');
            if (p.get('mode') === 'entire') {
                MAP_CONFIG.mode = 'entire';
                MAP_CONFIG.selectedRegions = ALL_STATES;
            }
            if (p.get('heatmap_sector')) MAP_CONFIG.heatmapSector = p.get('heatmap_sector');
            if (p.get('hazard_type')) MAP_CONFIG.hazardType = p.get('hazard_type');
            if (p.get('impact_type')) MAP_CONFIG.impactType = p.get('impact_type');
            if (p.get('impact_metric')) MAP_CONFIG.impactMetric = p.get('impact_metric');
            if (p.get('exposure_type')) MAP_CONFIG.exposureType = p.get('exposure_type');
            if (p.getAll('exposure_asset').length > 0) MAP_CONFIG.exposureAssets = p.getAll('exposure_asset');
            if (p.getAll('energy_detail_asset').length > 0) MAP_CONFIG.energyDetailAssets = p.getAll('energy_detail_asset');
            if (p.get('energy_detail_lod')) MAP_CONFIG.energyDetailLod = p.get('energy_detail_lod');
            if (p.get('svi_metric')) MAP_CONFIG.sviMetric = p.get('svi_metric');
            if (p.get('show_background') === 'false') MAP_CONFIG.showBackground = false;
            console.log('MAP_CONFIG after URL override:', JSON.stringify(MAP_CONFIG));
        })();
'''
    # Inject ALL_STATES constant + URL override right after MAP_CONFIG
    all_states_json = json.dumps([s['value'] for s in ctx.get('available_states', [])])
    all_states_js = f'\n        var ALL_STATES = {all_states_json};\n'

    html = html.replace(
        '// ========== Initialize Map ==========',
        all_states_js + url_override_js + '\n        // ========== Initialize Map =========='
    )

    # 6) Override view toggle buttons for static site (multi-page navigation)
    #    initViewToggle() in map-controls.js sets onclick to same-page URL with ?view_type=X
    #    For static site, we need to navigate to map_X.html instead
    view_toggle_override = '''
    <script>
    // Static site: override view toggle to navigate to correct HTML file
    (function() {
        var viewMap = {
            'btn-heatmap': 'map_heatmap.html',
            'btn-hazard': 'map_hazard.html',
            'btn-impact': 'map_impact.html',
            'btn-energy-vulnerability': 'map_energy_vulnerability.html',
            'btn-exposure': 'map_exposure.html',
            'btn-energy-detail': 'map_energy_detail.html',
            'btn-social-vulnerability': 'map_social_vulnerability.html'
        };
        Object.keys(viewMap).forEach(function(btnId) {
            var btn = document.getElementById(btnId);
            if (btn) {
                // Remove ALL existing click listeners by cloning
                var newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
                // Add static site navigation
                newBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var url = new URL(window.location);
                    var params = new URLSearchParams(url.search);
                    // Keep region and mode params, remove view-specific ones
                    var keep = ['region', 'mode', 'division_type', 'show_background'];
                    var newParams = new URLSearchParams();
                    keep.forEach(function(k) {
                        params.getAll(k).forEach(function(v) { newParams.append(k, v); });
                    });
                    window.location.href = viewMap[btnId] + '?' + newParams.toString();
                });
            }
        });
    })();
    </script>
    '''
    html = html.replace('</body>', view_toggle_override + '\n</body>')

    return html


# ──────────────────────────────────────────
# Copy static assets
# ──────────────────────────────────────────
def copy_static_assets(output_dir):
    static_out = output_dir / 'static'

    for subdir in ['js', 'css', 'images', 'CI_icon']:
        src = STATIC_DIR / subdir
        dst = static_out / subdir
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    # Remove geojson from static if accidentally copied
    geojson_out = static_out / 'geojson'
    if geojson_out.exists():
        shutil.rmtree(geojson_out)


def copy_bundled_data(output_dir):
    data_out = output_dir / 'data'
    data_out.mkdir(parents=True, exist_ok=True)

    for item_name in BUNDLE_DATA:
        src = GEOJSON_DIR / item_name
        dst = data_out / item_name
        if src.is_file():
            shutil.copy2(src, dst)
            print(f'  Copied {item_name} ({src.stat().st_size / 1024 / 1024:.1f} MB)')
        elif src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            total = sum(f.stat().st_size for f in src.rglob('*') if f.is_file())
            print(f'  Copied {item_name}/ ({total / 1024 / 1024:.1f} MB)')


def write_site_config(output_dir, data_url):
    config_js = f'''// Site configuration — change DATA_BASE_URL for your deployment
//   Local Flask:  "http://localhost:5000/static/geojson"
//   Bundled:      "./data"
//   CDN / R2:     "https://your-bucket.r2.dev"
window.DATA_BASE_URL = "{data_url}";
'''
    (output_dir / 'static' / 'js' / 'site-config.js').write_text(config_js, encoding='utf-8')


# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Build static site for GitHub Pages')
    parser.add_argument('--data-url', default='https://pub-2d678d396f414cb681a74d123b7e90b4.r2.dev',
                        help='Base URL for GeoJSON data')
    parser.add_argument('--output', default=str(OUTPUT_DIR), help='Output directory')
    args = parser.parse_args()

    output = Path(args.output)

    print(f'Building static site → {output}/')
    print(f'DATA_BASE_URL = {args.data_url}')

    # Clean output
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    # Discover data
    states = discover_states()
    sectors = discover_sectors()
    print(f'Found {len(states)} states, {len(sectors)} sectors')

    # Setup Jinja2 with same template dir as Flask
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )
    # Add url_for replacement — return relative path from docs/
    env.globals['url_for'] = lambda endpoint, **kw: f"./static/{kw.get('filename', '')}"

    ctx = build_template_context(states, sectors)

    # Render index.html
    print('Rendering index.html...')
    index_html = render_index(env, ctx)
    index_html = fix_paths(index_html, args.data_url)
    # Fix form action: JS dynamically sets form target based on view_type
    index_html = index_html.replace('action="map.html"', 'action="map_heatmap.html" id="main-form"')
    # Inject JS: update form action when view type changes (both click and radio change)
    form_js = '''
    <script>
    // Update form action when view type selection changes
    function updateFormAction(viewType) {
        var form = document.getElementById('main-form');
        if (form) form.action = 'map_' + viewType + '.html';
    }
    // Listen to view-type-item clicks (the actual UI interaction)
    document.querySelectorAll('.view-type-item').forEach(function(item) {
        item.addEventListener('click', function() {
            updateFormAction(this.dataset.value);
        });
    });
    // Also listen to radio changes as fallback
    document.querySelectorAll('input[name="view_type"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            updateFormAction(this.value);
        });
    });
    </script>
    '''
    index_html = index_html.replace('</body>', form_js + '</body>')
    (output / 'index.html').write_text(index_html, encoding='utf-8')

    # Render one map page per view type
    VIEW_TYPES = ['heatmap', 'hazard', 'impact', 'energy_vulnerability',
                  'exposure', 'energy_detail', 'social_vulnerability']

    for vt in VIEW_TYPES:
        filename = f'map_{vt}.html'
        print(f'Rendering {filename}...')
        map_html = render_map_page(env, ctx, vt)
        map_html = fix_paths(map_html, args.data_url, ctx)
        # Fix view toggle buttons to link to sibling map pages
        for other_vt in VIEW_TYPES:
            btn_id = 'btn-' + other_vt.replace('_', '-')
            old_btn = f'id="{btn_id}"'
            target = f'map_{other_vt}.html'
            new_btn = f'id="{btn_id}" onclick="window.location.href=\'{target}\'+window.location.search"'
            map_html = map_html.replace(old_btn, new_btn)
        (output / filename).write_text(map_html, encoding='utf-8')

    # Also create map.html as redirect to map_heatmap.html (default)
    redirect_html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<script>
var params = window.location.search;
var vt = new URLSearchParams(params).get('view_type') || 'heatmap';
window.location.replace('map_' + vt + '.html' + params);
</script>
</head><body>Redirecting...</body></html>'''
    (output / 'map.html').write_text(redirect_html, encoding='utf-8')

    # Copy assets
    print('Copying static assets...')
    copy_static_assets(output)

    # Write config
    write_site_config(output, args.data_url)

    # Copy bundled data
    print('Copying bundled data...')
    copy_bundled_data(output)

    # Summary
    total_size = sum(f.stat().st_size for f in output.rglob('*') if f.is_file())
    file_count = sum(1 for f in output.rglob('*') if f.is_file())
    print(f'\nBuild complete!')
    print(f'  Files: {file_count}')
    print(f'  Total: {total_size / 1024 / 1024:.1f} MB')
    print(f'\nPreview: cd {output} && python -m http.server 8080')


if __name__ == '__main__':
    main()
