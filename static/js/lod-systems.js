/**
 * Level of Detail (LOD) Systems
 * Manages visibility of features based on zoom level and user preferences
 */

// ========== Zoom-Based LOD Ratio ==========
// Shared zoom→ratio curve for asset-level views (Exposure, Energy Detail)
// Zoom in = more assets visible, zoom out = only top assets
function getZoomLodRatio(zoom) {
    if (zoom >= 14) return 1.0;    // 100% — street level
    if (zoom >= 13) return 0.80;
    if (zoom >= 12) return 0.60;
    if (zoom >= 11) return 0.45;
    if (zoom >= 10) return 0.30;
    if (zoom >= 9)  return 0.20;
    if (zoom >= 8)  return 0.12;
    if (zoom >= 7)  return 0.07;
    if (zoom >= 6)  return 0.04;
    return 0.02;                   // 2% — continent level
}

// ========== Detail View LOD System ==========

/**
 * LOD system for detail view (CI markers)
 * Manages feature visibility based on zoom level
 */
function createDetailLOD(map) {
    return {
        allFeatures: [],
        currentZoom: map.getZoom(),
        
        // Calculate detail ratio based on zoom level
        getDetailRatio: function(zoom) {
            if (zoom >= 14) return 1.0;
            if (zoom >= 12) return 0.8;
            if (zoom >= 10) return 0.5;
            if (zoom >= 8) return 0.3;
            if (zoom >= 6) return 0.15;
            return 0.05;
        },
        
        // Get feature priority for LOD ordering
        getFeaturePriority: function(feature) {
            var priority = 0;
            if (feature && feature.properties) {
                var tags = feature.properties.tags || {};
                if (tags.building === 'hospital' || tags.amenity === 'hospital') priority += 20;
                if (tags.power === 'plant' || tags.power === 'station') priority += 15;
                if (tags.aeroway === 'aerodrome') priority += 15;
                if (tags.amenity === 'fire_station' || tags.amenity === 'police') priority += 12;
            }
            priority += Math.random() * 5;
            return priority;
        },
        
        // Add feature to the LOD system
        addFeature: function(feature, latlng, sectorKey, layer) {
            this.allFeatures.push({
                feature: feature,
                latlng: latlng,
                sectorKey: sectorKey,
                layer: layer,
                priority: this.getFeaturePriority(feature)
            });
        },
        
        // Update visible features based on current zoom
        updateVisibility: function() {
            var zoomLevel = map.getZoom();
            var ratio = this.getDetailRatio(zoomLevel);
            var totalFeatures = this.allFeatures.length;
            var targetCount = Math.max(1, Math.ceil(totalFeatures * ratio));
            
            var sorted = this.allFeatures.slice().sort((a, b) => b.priority - a.priority);
            
            this.allFeatures.forEach(item => {
                if (map.hasLayer(item.layer)) {
                    map.removeLayer(item.layer);
                }
            });
            
            var visibleCount = 0;
            for (var i = 0; i < Math.min(targetCount, sorted.length); i++) {
                sorted[i].layer.addTo(map);
                visibleCount++;
            }
            
            // Update UI
            var percent = Math.round((visibleCount / totalFeatures) * 100);
            var barEl = document.getElementById('lod-bar');
            var textEl = document.getElementById('lod-text');
            if (barEl) barEl.style.width = percent + '%';
            if (textEl) textEl.textContent = percent + '%';
        },
        
        // Initialize zoom listener
        init: function() {
            var self = this;
            map.on('zoomend', function() {
                if (self.allFeatures.length > 0) {
                    self.updateVisibility();
                }
            });
            setTimeout(function() {
                if (self.allFeatures.length > 0) {
                    self.updateVisibility();
                }
            }, 1000);
        }
    };
}

// ========== Heatmap LOD System ==========

/**
 * LOD system for heatmap view (CI heatmaps)
 * Manages visibility based on score ranking or threshold
 */
function createHeatmapLOD(map) {
    return {
        allFeatures: [],
        heatmapLayers: [],
        threshold: 0,
        lodPercentage: 100,
        mode: 'top',
        thresholdValue: 0,
        
        // Register a heatmap layer with the LOD system
        registerLayer: function(layer, features) {
            this.heatmapLayers.push(layer);
            var self = this;
            
            features.forEach(function(feature) {
                var score = feature.properties.total_normalized || 
                           feature.properties.score_normalized || 0;
                self.allFeatures.push({
                    feature: feature,
                    score: score,
                    visible: true
                });
            });
            
            this.updateStats();
        },
        
        // Update visibility based on LOD percentage (Top % mode)
        updateVisibility: function(lodPercent) {
            this.lodPercentage = lodPercent;
            this.mode = 'top';
            
            if (this.allFeatures.length === 0) return;
            
            var sorted = this.allFeatures.slice().sort((a, b) => b.score - a.score);
            var targetCount = Math.ceil(sorted.length * (lodPercent / 100));
            targetCount = Math.max(1, targetCount);
            
            if (targetCount >= sorted.length) {
                this.threshold = 0;
            } else {
                this.threshold = sorted[targetCount - 1].score;
            }
            
            this._applyFilter();
        },
        
        // Update visibility based on score threshold (Threshold mode)
        // thresholdPercent: 99 means show cells with score >= top 1% (hide bottom 99%)
        // thresholdPercent: 0 means show all cells
        updateByThreshold: function(thresholdPercent) {
            this.thresholdValue = thresholdPercent;
            this.mode = 'threshold';
            // Convert to threshold: 99% slider = show score >= 0.99, 0% = show all (score >= 0)
            this.threshold = thresholdPercent / 100;
            this._applyFilter();
        },
        
        // Apply current filter settings
        _applyFilter: function() {
            var self = this;
            var threshold = this.threshold;
            
            this.heatmapLayers.forEach(function(layer) {
                map.removeLayer(layer);
            });
            
            this.heatmapLayers = [];
            
            var filteredFeatures = this.allFeatures.filter(function(item) {
                return item.score >= threshold;
            });
            
            if (filteredFeatures.length === 0) {
                this.updateStats();
                return;
            }
            
            var newLayer = L.geoJSON({
                type: 'FeatureCollection',
                features: filteredFeatures.map(f => f.feature)
            }, {
                style: function(feature) {
                    var score = feature.properties.total_normalized || 
                               feature.properties.score_normalized || 0;
                    return {
                        color: 'transparent',
                        weight: 0,
                        opacity: 0,
                        fillColor: getHeatmapColor(score),
                        fillOpacity: 0.7
                    };
                },
                onEachFeature: function(feature, layer) {
                    var props = feature.properties;
                    var score = props.total_normalized || props.score_normalized || 0;
                    var popup = '<strong>Grid ID: ' + (props.grid_id || 'N/A') + '</strong><br>';
                    popup += 'Score: ' + (score * 100).toFixed(1) + '%';
                    layer.bindPopup(popup);
                }
            }).addTo(map);
            
            this.heatmapLayers.push(newLayer);
            this.updateStats();
        },
        
        // Update statistics display
        updateStats: function() {
            var totalFeatures = this.allFeatures.length;
            var visibleCount = 0;
            var visiblePercent = 0;
            
            if (this.mode === 'top') {
                visibleCount = Math.ceil(totalFeatures * this.lodPercentage / 100);
                visiblePercent = this.lodPercentage;
            } else {
                var threshold = this.threshold;
                visibleCount = this.allFeatures.filter(function(item) {
                    return item.score >= threshold;
                }).length;
                visiblePercent = totalFeatures > 0 ? Math.round(visibleCount / totalFeatures * 100) : 0;
            }
            
            var statsEl = document.getElementById('heatmap-lod-stats');
            var valueEl = document.getElementById('heatmap-lod-value');
            var thresholdValueEl = document.getElementById('heatmap-threshold-value');
            var barEl = document.getElementById('heatmap-lod-bar');
            var barTextEl = document.getElementById('heatmap-lod-bar-text');
            
            if (statsEl) {
                statsEl.textContent = 'Visible: ' + visibleCount + ' / ' + totalFeatures + ' cells';
            }
            
            if (barEl) {
                barEl.style.width = visiblePercent + '%';
                if (this.mode === 'threshold') {
                    if (this.thresholdValue >= 75) {
                        barEl.style.background = 'linear-gradient(to right, #ef9a9a, #c62828)';
                    } else if (this.thresholdValue >= 50) {
                        barEl.style.background = 'linear-gradient(to right, #ffcc80, #e65100)';
                    } else if (this.thresholdValue >= 25) {
                        barEl.style.background = 'linear-gradient(to right, #a5d6a7, #388e3c)';
                    } else {
                        barEl.style.background = 'linear-gradient(to right, #ce93d8, #7b1fa2)';
                    }
                } else {
                    barEl.style.background = 'linear-gradient(to right, #ce93d8, #7b1fa2)';
                }
            }
            
            if (barTextEl) {
                barTextEl.textContent = visiblePercent + '%';
            }
        },
        
        // Reset the LOD system
        reset: function() {
            this.allFeatures = [];
            this.heatmapLayers = [];
            this.threshold = 0;
            this.lodPercentage = 100;
            this.thresholdValue = 0;
            this.mode = 'top';
        }
    };
}

// ========== Hazard LOD System ==========

/**
 * LOD system for hazard view (flood, wildfire, etc.)
 * Manages visibility based on hazard score
 */
function createHazardLOD(map, hazardType) {
    var hazardScoreProperty = hazardType + '_score_normalized';
    
    return {
        allFeatures: [],
        hazardLayers: [],
        lodPercentage: 100,
        thresholdValue: 0,
        mode: 'top',
        
        // Register a hazard layer with the LOD system
        registerLayer: function(layer, features) {
            var self = this;
            this.hazardLayers.push(layer);
            features.forEach(function(feature) {
                var score = feature.properties[hazardScoreProperty] || 0;
                self.allFeatures.push({
                    feature: feature,
                    score: score,
                    layer: layer
                });
            });
            
            this.allFeatures.sort(function(a, b) {
                return b.score - a.score;
            });
            
            this.updateStats();
        },
        
        // Update visibility based on LOD percentage (Top % mode)
        updateVisibility: function(percentage) {
            var self = this;
            this.lodPercentage = percentage;
            this.mode = 'top';
            
            var totalFeatures = this.allFeatures.length;
            var visibleCount = Math.ceil(totalFeatures * percentage / 100);
            
            this.hazardLayers.forEach(function(layer) {
                map.removeLayer(layer);
            });
            
            this.hazardLayers = [];
            
            var visibleFeatures = this.allFeatures.slice(0, visibleCount);
            
            if (visibleFeatures.length > 0) {
                var newLayer = L.geoJSON({
                    type: 'FeatureCollection',
                    features: visibleFeatures.map(f => f.feature)
                }, {
                    style: function(feature) {
                        var score = feature.properties[hazardScoreProperty] || 0;
                        return {
                            color: 'transparent',
                            weight: 0,
                            opacity: 0,
                            fillColor: getHazardColor(score, hazardType),
                            fillOpacity: 0.7
                        };
                    },
                    onEachFeature: function(feature, layer) {
                        var props = feature.properties;
                        var score = props[hazardScoreProperty] || 0;
                        var popup = '<strong>Grid ID: ' + (props.grid_id || 'N/A') + '</strong><br>';
                        popup += hazardType.charAt(0).toUpperCase() + hazardType.slice(1) + ' Risk: ' + (score * 100).toFixed(1) + '%';
                        layer.bindPopup(popup);
                    }
                }).addTo(map);
                
                self.hazardLayers.push(newLayer);
            }
            
            this.updateStats();
        },
        
        // Update visibility based on score threshold (Threshold mode)
        updateByThreshold: function(thresholdPercent) {
            var self = this;
            this.thresholdValue = thresholdPercent;
            this.mode = 'threshold';
            
            var threshold = thresholdPercent / 100;
            
            this.hazardLayers.forEach(function(layer) {
                map.removeLayer(layer);
            });
            
            this.hazardLayers = [];
            
            var visibleFeatures = this.allFeatures.filter(function(item) {
                return item.score >= threshold;
            });
            
            if (visibleFeatures.length > 0) {
                var newLayer = L.geoJSON({
                    type: 'FeatureCollection',
                    features: visibleFeatures.map(f => f.feature)
                }, {
                    style: function(feature) {
                        var score = feature.properties[hazardScoreProperty] || 0;
                        return {
                            color: 'transparent',
                            weight: 0,
                            opacity: 0,
                            fillColor: getHazardColor(score, hazardType),
                            fillOpacity: 0.7
                        };
                    },
                    onEachFeature: function(feature, layer) {
                        var props = feature.properties;
                        var score = props[hazardScoreProperty] || 0;
                        var popup = '<strong>Grid ID: ' + (props.grid_id || 'N/A') + '</strong><br>';
                        popup += hazardType.charAt(0).toUpperCase() + hazardType.slice(1) + ' Risk: ' + (score * 100).toFixed(1) + '%';
                        layer.bindPopup(popup);
                    }
                }).addTo(map);
                
                self.hazardLayers.push(newLayer);
            }
            
            this.updateStats();
        },
        
        // Update statistics display
        updateStats: function() {
            var totalFeatures = this.allFeatures.length;
            var visibleCount = 0;
            var visiblePercent = 0;
            
            if (this.mode === 'top') {
                visibleCount = Math.ceil(totalFeatures * this.lodPercentage / 100);
                visiblePercent = this.lodPercentage;
            } else {
                var threshold = this.thresholdValue / 100;
                visibleCount = this.allFeatures.filter(function(item) {
                    return item.score >= threshold;
                }).length;
                visiblePercent = totalFeatures > 0 ? Math.round(visibleCount / totalFeatures * 100) : 0;
            }
            
            var statsEl = document.getElementById('hazard-lod-stats');
            var barEl = document.getElementById('hazard-lod-bar');
            var barTextEl = document.getElementById('hazard-lod-bar-text');
            
            if (statsEl) {
                statsEl.textContent = 'Visible: ' + visibleCount + ' / ' + totalFeatures + ' cells';
            }
            
            if (barEl) {
                barEl.style.width = visiblePercent + '%';
            }
            
            if (barTextEl) {
                barTextEl.textContent = visiblePercent + '%';
            }
        },
        
        // Reset the LOD system
        reset: function() {
            this.allFeatures = [];
            this.hazardLayers = [];
            this.lodPercentage = 100;
            this.thresholdValue = 0;
            this.mode = 'top';
        }
    };
}