/**
 * Map Event Handlers
 * UI event handlers for controls and interactions
 */

// ========== View Toggle Event Handlers ==========

/**
 * Initialize view toggle button handlers
 */
function initViewToggle() {
    var btnDetail = document.getElementById('btn-detail');
    var btnHeatmap = document.getElementById('btn-heatmap');
    var btnHazard = document.getElementById('btn-hazard');
    var btnSimpleHazard = document.getElementById('btn-simple-hazard');
    var btnImpact = document.getElementById('btn-impact');
    
    if (btnDetail) {
        btnDetail.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'detail');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            window.location.href = url.toString();
        });
    }
    
    if (btnHeatmap) {
        btnHeatmap.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'heatmap');
            url.searchParams.delete('sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            url.searchParams.set('heatmap_sector', 'combined');
            window.location.href = url.toString();
        });
    }
    
    if (btnHazard) {
        btnHazard.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'hazard');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            url.searchParams.set('hazard_type', 'flood');
            window.location.href = url.toString();
        });
    }
    
    if (btnSimpleHazard) {
        btnSimpleHazard.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'simple_hazard');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            url.searchParams.set('simple_hazard_type', 'wfir');
            window.location.href = url.toString();
        });
    }
    
    if (btnImpact) {
        btnImpact.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'impact');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('population_type');
            url.searchParams.set('impact_type', 'poweroutage_2022');
            url.searchParams.set('impact_metric', 'total_customers');
            window.location.href = url.toString();
        });
    }
    
    var btnPopulation = document.getElementById('btn-population');
    if (btnPopulation) {
        btnPopulation.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'population');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('energy_vulnerability_type');
            url.searchParams.set('population_type', 'population_2023');
            window.location.href = url.toString();
        });
    }
    
    var btnEnergyVulnerability = document.getElementById('btn-energy-vulnerability');
    if (btnEnergyVulnerability) {
        btnEnergyVulnerability.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'energy_vulnerability');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            url.searchParams.set('energy_vulnerability_type', 'energy_vulnerability');
            window.location.href = url.toString();
        });
    }
    
    var btnExposure = document.getElementById('btn-exposure');
    if (btnExposure) {
        btnExposure.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'exposure');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            url.searchParams.delete('energy_vulnerability_type');
            url.searchParams.set('exposure_type', 'flood');
            window.location.href = url.toString();
        });
    }
    
    var btnEnergyDetail = document.getElementById('btn-energy-detail');
    if (btnEnergyDetail) {
        btnEnergyDetail.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'energy_detail');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            url.searchParams.delete('energy_vulnerability_type');
            url.searchParams.delete('exposure_type');
            url.searchParams.delete('svi_metric');
            window.location.href = url.toString();
        });
    }
    
    var btnSocialVulnerability = document.getElementById('btn-social-vulnerability');
    if (btnSocialVulnerability) {
        btnSocialVulnerability.addEventListener('click', function() {
            var url = new URL(window.location);
            url.searchParams.set('view_type', 'social_vulnerability');
            url.searchParams.delete('sector');
            url.searchParams.delete('heatmap_sector');
            url.searchParams.delete('hazard_type');
            url.searchParams.delete('simple_hazard_type');
            url.searchParams.delete('impact_type');
            url.searchParams.delete('impact_metric');
            url.searchParams.delete('population_type');
            url.searchParams.delete('energy_vulnerability_type');
            url.searchParams.delete('exposure_type');
            url.searchParams.set('svi_metric', 'RPL_THEMES');
            window.location.href = url.toString();
        });
    }
}

// ========== Detail View Event Handlers ==========

/**
 * Initialize sector checkbox handlers for detail view
 */
function initDetailControls() {
    var sectorCheckboxes = document.querySelectorAll('#sector-panel input.sector-cb');
    var selectAll = document.getElementById('select-all');
    
    if (!selectAll || sectorCheckboxes.length === 0) return;
    
    function updateSelectAll() {
        var all = document.querySelectorAll('#sector-panel input.sector-cb');
        var checked = document.querySelectorAll('#sector-panel input.sector-cb:checked');
        selectAll.checked = all.length === checked.length && all.length > 0;
        selectAll.indeterminate = checked.length > 0 && checked.length < all.length;
    }
    
    selectAll.addEventListener('change', function() {
        sectorCheckboxes.forEach(cb => cb.checked = this.checked);
        var checkedSectors = Array.from(document.querySelectorAll('#sector-panel input.sector-cb:checked')).map(cb => cb.value);
        var url = new URL(window.location);
        url.searchParams.delete('sector');
        checkedSectors.forEach(sector => url.searchParams.append('sector', sector));
        window.location.href = url.toString();
    });
    
    sectorCheckboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            var checkedSectors = Array.from(document.querySelectorAll('#sector-panel input.sector-cb:checked')).map(cb => cb.value);
            var url = new URL(window.location);
            url.searchParams.delete('sector');
            checkedSectors.forEach(sector => url.searchParams.append('sector', sector));
            window.location.href = url.toString();
        });
    });
    
    updateSelectAll();
}

// ========== Heatmap View Event Handlers ==========

/**
 * Initialize heatmap controls (sector dropdown, LOD sliders)
 * @param {object} HeatmapLOD - HeatmapLOD system instance
 * @param {boolean} useGeoTiff - Whether GeoTIFF mode is enabled
 */
function initHeatmapControls(HeatmapLOD, useGeoTiff) {
    // Heatmap sector selector
    var heatmapSelect = document.getElementById('heatmap-select');
    if (heatmapSelect) {
        heatmapSelect.addEventListener('change', function() {
            var url = new URL(window.location);
            url.searchParams.set('heatmap_sector', this.value);
            window.location.href = url.toString();
        });
    }
    
    // GeoTIFF toggle
    var tiffToggleCheckbox = document.getElementById('tiff-toggle');
    if (tiffToggleCheckbox) {
        tiffToggleCheckbox.addEventListener('change', function() {
            var url = new URL(window.location);
            if (this.checked) {
                url.searchParams.set('use_geotiff', 'true');
            } else {
                url.searchParams.delete('use_geotiff');
            }
            window.location.href = url.toString();
        });
    }
    
    // Threshold slider
    var heatmapThresholdSlider = document.getElementById('heatmap-threshold-slider');
    if (heatmapThresholdSlider) {
        if (useGeoTiff) {
            heatmapThresholdSlider.disabled = true;
            heatmapThresholdSlider.style.opacity = '0.5';
            heatmapThresholdSlider.style.cursor = 'not-allowed';
        } else {
            heatmapThresholdSlider.addEventListener('input', function() {
                var thresholdValue = parseInt(this.value);
                var valueDisplay = document.getElementById('heatmap-threshold-value');
                if (valueDisplay) {
                    valueDisplay.textContent = thresholdValue + '%';
                }
            });
            
            heatmapThresholdSlider.addEventListener('change', function() {
                var thresholdValue = parseInt(this.value);
                console.log('Heatmap threshold changed to:', thresholdValue + '%');
                HeatmapLOD.updateByThreshold(thresholdValue);
            });
            
            // Note: Initial threshold is applied by applyInitialThreshold() after data loads
        }
    }
}

// ========== Hazard View Event Handlers ==========

/**
 * Initialize hazard controls (type dropdown, LOD sliders)
 * @param {object} HazardLOD - HazardLOD system instance
 */
function initHazardControls(HazardLOD) {
    // Hazard type selector
    var hazardSelect = document.getElementById('hazard-select');
    if (hazardSelect) {
        hazardSelect.addEventListener('change', function() {
            var url = new URL(window.location);
            url.searchParams.set('hazard_type', this.value);
            window.location.href = url.toString();
        });
    }
    
    // Threshold slider
    var hazardThresholdSlider = document.getElementById('hazard-threshold-slider');
    if (hazardThresholdSlider) {
        hazardThresholdSlider.addEventListener('input', function() {
            var thresholdValue = parseInt(this.value);
            var valueDisplay = document.getElementById('hazard-threshold-value');
            if (valueDisplay) {
                valueDisplay.textContent = thresholdValue + '%';
            }
        });
        
        hazardThresholdSlider.addEventListener('change', function() {
            var thresholdValue = parseInt(this.value);
            console.log('Hazard threshold changed to:', thresholdValue + '%');
            HazardLOD.updateByThreshold(thresholdValue);
        });
        
        // Apply initial threshold after data is loaded
        setTimeout(function() {
            if (HazardLOD.allFeatures.length > 0) {
                var initialThresholdValue = parseInt(hazardThresholdSlider.value);
                console.log('Applying initial hazard threshold value:', initialThresholdValue + '%');
                HazardLOD.updateByThreshold(initialThresholdValue);
            } else {
                // Data not loaded yet, try again
                setTimeout(function() {
                    var initialThresholdValue = parseInt(hazardThresholdSlider.value);
                    console.log('Retry applying initial hazard threshold value:', initialThresholdValue + '%');
                    HazardLOD.updateByThreshold(initialThresholdValue);
                }, 1500);
            }
        }, 1000);
    }
}

// ========== Common Event Handlers ==========

/**
 * Initialize background map toggle
 * @param {L.Map} map - Leaflet map instance
 * @param {boolean} showBackground - Initial state
 */
function initBackgroundToggle(map, showBackground) {
    var bgToggleCheckbox = document.getElementById('bg-toggle');
    if (bgToggleCheckbox) {
        bgToggleCheckbox.addEventListener('change', function() {
            var url = new URL(window.location);
            if (this.checked) {
                url.searchParams.set('show_background', 'true');
            } else {
                url.searchParams.set('show_background', 'false');
            }
            window.location.href = url.toString();
        });
    }
    
    if (showBackground) {
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
    }
}

/**
 * Initialize coordinate display on mouse move
 * @param {L.Map} map - Leaflet map instance
 */
function initCoordinateDisplay(map) {
    var currentCounty = null;
    var coordsDiv = document.getElementById('coords');
    
    map.on('mousemove', function(e) {
        var lat = e.latlng.lat.toFixed(6);
        var lng = e.latlng.lng.toFixed(6);
        var display = 'Lat: ' + lat + ', Lng: ' + lng;
        if (currentCounty) {
            display += ' | ' + currentCounty;
        }
        var coordsText = document.getElementById('coords-text');
        if (coordsText) {
            coordsText.innerHTML = display;
        } else if (coordsDiv) {
            coordsDiv.innerHTML = display;
        }
    });
    
    // Return a function to update currentCounty from outside
    return function(county) {
        currentCounty = county;
    };
}