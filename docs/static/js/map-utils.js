/**
 * Map Utility Functions
 * Helper functions for map operations
 */

// ========== Region Name Utilities ==========

/**
 * Find possible folder names for a region
 * @param {string} regionName - Display name of region
 * @returns {string[]} - Array of possible folder names
 */
function findRegionFolder(regionName) {
    var baseName = regionName.toLowerCase().replace(/\s+/g, '_');
    var candidates = [];
    
    // Remove _0 suffix if present, only use base name
    if (baseName.endsWith('_0')) {
        var withoutZero = baseName.slice(0, -2);
        candidates.push(withoutZero);
    } else if (baseName.match(/_\d+$/)) {
        // Has numeric suffix like _1, _2, etc - use as is
        candidates.push(baseName);
    } else {
        // No suffix - just use base name, don't try _0
        candidates.push(baseName);
    }
    
    return candidates;
}

/**
 * Try to load GeoJSON from multiple URL candidates
 * @param {string[]} urlCandidates - Array of URLs to try
 * @param {function} successCallback - Called with (data, url) on success
 * @param {function} errorCallback - Called with (error) if all fail
 */
function tryLoadGeoJSON(urlCandidates, successCallback, errorCallback) {
    if (urlCandidates.length === 0) {
        errorCallback('No valid folder found');
        return;
    }
    
    var url = urlCandidates.shift();
    fetch(url)
        .then(response => {
            if (response.ok) {
                return response.json().then(data => successCallback(data, url));
            } else {
                tryLoadGeoJSON(urlCandidates, successCallback, errorCallback);
            }
        })
        .catch(error => {
            tryLoadGeoJSON(urlCandidates, successCallback, errorCallback);
        });
}

// ========== Color Utilities ==========

/**
 * Get heatmap color based on normalized score (0-1)
 * Uses Reds color palette
 * @param {number} score - Normalized score (0-1)
 * @returns {string} - Hex color
 */
function getHeatmapColor(score) {
    var colors = ['#fff5f0', '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#a50f15', '#67000d'];
    var index = Math.floor(score * (colors.length - 1));
    index = Math.max(0, Math.min(colors.length - 1, index));
    return colors[index];
}

/**
 * Get hazard color based on normalized score (0-1) and hazard type
 * @param {number} score - Normalized score (0-1)
 * @param {string} hazardType - Type of hazard ('flood', 'wildfire', etc.)
 * @returns {string} - Hex color
 */
function getHazardColor(score, hazardType) {
    var colorPalettes = {
        // Blues palette for flood
        'flood': ['#e3f2fd', '#bbdefb', '#90caf9', '#64b5f6', '#42a5f5', '#2196f3', '#1976d2', '#1565c0', '#0d47a1'],
        // Reds/Oranges fire palette for wildfire
        'wildfire': ['#fff3e0', '#ffe0b2', '#ffcc80', '#ffb74d', '#ffa726', '#ff9800', '#f57c00', '#e65100', '#bf360c'],
        // Greens palette for earthquake (future)
        'earthquake': ['#e8f5e9', '#c8e6c9', '#a5d6a7', '#81c784', '#66bb6a', '#4caf50', '#43a047', '#388e3c', '#2e7d32'],
        // Default palette
        'default': ['#e3f2fd', '#bbdefb', '#90caf9', '#64b5f6', '#42a5f5', '#2196f3', '#1976d2', '#1565c0', '#0d47a1']
    };
    
    var colors = colorPalettes[hazardType] || colorPalettes['default'];
    var index = Math.floor(score * (colors.length - 1));
    index = Math.max(0, Math.min(colors.length - 1, index));
    return colors[index];
}

// ========== Marker Creation ==========

/**
 * Create a sector marker with icon or fallback to color point
 * @param {L.LatLng} latlng - Position
 * @param {string} sectorKey - Sector identifier
 * @param {object} feature - GeoJSON feature
 * @param {object} sectorIcons - Map of sector keys to icon URLs
 * @param {object} sectorColors - Map of sector keys to colors
 * @param {L.Map} map - Leaflet map instance
 * @param {object} LOD - LOD system instance
 * @returns {L.Marker} - Created marker
 */
function createSectorMarker(latlng, sectorKey, feature, sectorIcons, sectorColors, map, LOD) {
    var iconUrl = sectorIcons[sectorKey] || '/static/CI_icon/default.png';

    var sectorTitle = sectorKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    var popupContent = sectorTitle + ' Feature<br>';
    if (feature && feature.properties && feature.properties.tags) {
        for (var key in feature.properties.tags) {
            popupContent += key + ': ' + feature.properties.tags[key] + '<br>';
        }
    }

    var icon = L.icon({
        iconUrl: iconUrl,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
    });

    var marker = L.marker(latlng, { icon: icon });
    marker.bindPopup(popupContent);
    
    // Register with LOD system
    LOD.addFeature(feature, latlng, sectorKey, marker);

    var img = new Image();
    img.onload = function() {};
    img.onerror = function() {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        }
        var colorPoint = L.circleMarker(latlng, {
            color: sectorColors[sectorKey] || '#ff0000',
            radius: 8,
            fillOpacity: 0.8,
            weight: 2,
            fillColor: sectorColors[sectorKey] || '#ff0000'
        });
        colorPoint.bindPopup(popupContent);
        
        // Update LOD system with new layer
        var featureIndex = LOD.allFeatures.findIndex(f => f.layer === marker);
        if (featureIndex !== -1) {
            LOD.allFeatures[featureIndex].layer = colorPoint;
        }
        
        colorPoint.addTo(map);
    };
    img.src = iconUrl;

    return marker;
}

// ========== URL Parameter Utilities ==========

/**
 * Update URL parameter and navigate
 * @param {string} key - Parameter key
 * @param {string} value - Parameter value
 */
function updateUrlParam(key, value) {
    var url = new URL(window.location);
    url.searchParams.set(key, value);
    window.location.href = url.toString();
}

/**
 * Delete URL parameter and navigate
 * @param {string} key - Parameter key
 */
function deleteUrlParam(key) {
    var url = new URL(window.location);
    url.searchParams.delete(key);
    window.location.href = url.toString();
}