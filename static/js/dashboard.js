// Analytics Dashboard JavaScript

// Chart.js default configuration
Chart.defaults.color = '#2c3e50';
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

// Initialize charts
let trendsChart = null;
let alertChart, comfortChart;

function updateAnalytics() {
    fetch('/api/analytics')
        .then(response => response.json())
        .then(data => {
            updateCurrentConditions(data['1_current_conditions']);
            updateDailyPeaks(data['2_daily_peaks']);
            updateHourlyTrends(data['3_hourly_trends']);
            updateAlertDistribution(data['4_alert_distribution']);
            updateComfortAnalysis(data['5_comfort_analysis']);
            updateRiskForecast(data['6_risk_forecast']);
            updatePatternAnalysis(data['7_pattern_analysis']);
            updateComparativeMetrics(data['8_comparative_metrics']);
            updateSeasonalImpact(data['9_seasonal_impact']);
            updateRecommendations(data['10_recommendations']);
        })
        .catch(error => console.error('Error fetching analytics:', error));
}

function updateCurrentConditions(data) {
    const element = document.getElementById('currentConditions');
    const alertClass = getAlertClass(data.alert_level);
    
    element.innerHTML = `
        <div class="metric">
            <div>Temperature: ${data.temperature}°C</div>
            <div>Humidity: ${data.humidity}%</div>
            <div>Heat Index: ${data.heat_index}°C</div>
            <div class="risk-indicator ${alertClass}">${data.alert_level}</div>
        </div>
    `;
}

function updateDailyPeaks(data) {
    const element = document.getElementById('dailyPeaks');
    const today = Object.keys(data)[Object.keys(data).length - 1];
    const peaks = data[today];
    
    element.innerHTML = `
        <div class="metric">
            <div>Peak Temperature: ${peaks.temp}°C</div>
            <div>Peak Humidity: ${peaks.humidity}%</div>
            <div>Peak Heat Index: ${peaks.heat_index}°C</div>
        </div>
    `;
}

function updateHourlyTrends(data) {
    const ctx = document.getElementById('trendsChart').getContext('2d');
    
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps,
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: data.temperatures,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Heat Index (°C)',
                    data: data.heat_indices,
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Humidity (%)',
                    data: data.humidity_levels,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                title: {
                    display: true,
                    text: '24-Hour Weather Trends',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    position: 'top'
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    },
                    ticks: {
                        maxTicksLimit: 8,
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    suggestedMin: 20,
                    suggestedMax: 40
                }
            }
        }
    });
}

function updateAlertDistribution(data) {
    const ctx = document.getElementById('alertChart').getContext('2d');
    
    if (alertChart) {
        alertChart.destroy();
    }
    
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    alertChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#2ecc71',  // Safe
                    '#f1c40f',  // Caution
                    '#e67e22',  // Danger
                    '#e74c3c'   // Extreme Danger
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function updateComfortAnalysis(data) {
    const ctx = document.getElementById('comfortChart').getContext('2d');
    
    if (comfortChart) {
        comfortChart.destroy();
    }
    
    const labels = Object.keys(data);
    const values = Object.values(data);
    
    comfortChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Comfort Levels',
                data: values,
                backgroundColor: '#3498db'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateRiskForecast(data) {
    const element = document.getElementById('riskForecast');
    const riskClass = getRiskClass(data.risk_level);
    
    element.innerHTML = `
        <div class="risk-content">
            <div class="risk-indicator ${riskClass}">${data.risk_level}</div>
            <div class="risk-confidence">Confidence: ${(data.confidence * 100).toFixed(1)}%</div>
        </div>
    `;
}

function updatePatternAnalysis(data) {
    const element = document.getElementById('patternAnalysis');
    
    element.innerHTML = `
        <div class="pattern-content">
            <div class="pattern-item">
                <strong>Identified Patterns</strong>
                <div class="pattern-item-value">${data.pattern}</div>
            </div>
            <div class="pattern-item">
                <strong>Reliability</strong>
                <div class="pattern-item-value">${data.reliability}%</div>
            </div>
            <div class="pattern-item">
                <strong>Data Points</strong>
                <div class="pattern-item-value">${data.data_points}</div>
            </div>
        </div>
    `;
}

function updateComparativeMetrics(data) {
    const element = document.getElementById('comparativeMetrics');
    
    const tempDiff = data.temp_vs_average;
    const humidityDiff = data.humidity_vs_average;
    
    element.innerHTML = `
        <div class="metric">
            <div class="metric-current">
                <strong>Current Temperature:</strong> ${data.current_temp}°C
            </div>
            <div class="metric-comparison ${tempDiff > 0 ? 'above-average' : 'below-average'}">
                <strong>vs Average:</strong> ${tempDiff > 0 ? '+' : ''}${tempDiff}°C
            </div>
            <div class="metric-current">
                <strong>Current Humidity:</strong> ${data.current_humidity}%
            </div>
            <div class="metric-comparison ${humidityDiff > 0 ? 'above-average' : 'below-average'}">
                <strong>vs Average:</strong> ${humidityDiff > 0 ? '+' : ''}${humidityDiff}%
            </div>
            <div class="metric-sample">
                Based on ${data.sample_size} measurements
            </div>
        </div>
    `;
}

function updateSeasonalImpact(data) {
    const element = document.getElementById('seasonalImpact');
    
    element.innerHTML = `
        <div class="seasonal-content">
            <div class="seasonal-header">Current Season:</div>
            <div class="seasonal-value">${data.current_season}</div>
            
            <div class="seasonal-risk">
                Seasonal Risk Level: ${data.seasonal_risk}
            </div>
            
            <div class="seasonal-severity">
                Temperature Severity: ${data.temperature_severity}
            </div>
            
            <div class="seasonal-impact">
                Current Impact: ${data.impact_level}
            </div>
            
            <div class="seasonal-note">
                <i class="fas fa-info-circle"></i> ${data.seasonal_note}
            </div>
        </div>
    `;
}

function updateRecommendations(recommendations) {
    const element = document.getElementById('recommendations');
    
    if (!recommendations || recommendations.length === 0) {
        element.innerHTML = '<div class="no-recommendations">No specific recommendations at this time.</div>';
        return;
    }
    
    const recommendationsList = recommendations.map(rec => {
        let className = 'recommendation-item';
        if (rec.includes('IMMEDIATE ACTION REQUIRED')) {
            className += ' extreme-danger';
        } else if (rec.includes('DANGER Level')) {
            className += ' danger';
        } else if (rec.includes('CAUTION Required')) {
            className += ' caution';
        } else if (rec.includes('NORMAL Conditions')) {
            className += ' normal';
        }
        
        return `<div class="${className}">${rec}</div>`;
    }).join('');
    
    element.innerHTML = `
        <div class="recommendations-container">
            ${recommendationsList}
        </div>
    `;
}

function getAlertClass(level) {
    switch (level) {
        case 'Extreme Danger': return 'risk-extreme';
        case 'Danger': return 'risk-high';
        case 'Caution': return 'risk-moderate';
        default: return 'risk-low';
    }
}

function getRiskClass(level) {
    switch (level) {
        case 'Extreme': return 'risk-extreme';
        case 'High': return 'risk-high';
        case 'Moderate': return 'risk-moderate';
        default: return 'risk-low';
    }
}

// Initial update
updateAnalytics();

// Update every 5 minutes
setInterval(updateAnalytics, 5 * 60 * 1000);

// Add these styles to the page
document.head.insertAdjacentHTML('beforeend', `
    <style>
        .metric-comparison.above-average { color: #e74c3c; }
        .metric-comparison.below-average { color: #2ecc71; }
        .metric-sample { font-size: 0.9em; color: #7f8c8d; margin-top: 10px; }
        
        .season-header { font-size: 1.1em; margin-bottom: 10px; }
        .season-risk, .temperature-severity { padding: 5px 10px; border-radius: 4px; margin: 5px 0; }
        .seasonal-note { margin-top: 10px; font-style: italic; color: #34495e; }
        
        .recommendations-container { display: flex; flex-direction: column; gap: 10px; }
        .recommendation-item {
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #3498db;
            background: #f8f9fa;
            margin: 5px 0;
        }
        .recommendation-item.extreme-danger {
            border-left-color: #e74c3c;
            background: #fde8e8;
        }
        .recommendation-item.danger {
            border-left-color: #e67e22;
            background: #fef3e8;
        }
        .recommendation-item.caution {
            border-left-color: #f1c40f;
            background: #fefae8;
        }
        .recommendation-item.normal {
            border-left-color: #2ecc71;
            background: #e8f8f0;
        }
        
        .high-risk { background: #fde8e8; }
        .moderate-risk { background: #fef3e8; }
        .low-risk { background: #e8f8f0; }
        
        .severe-severity { background: #fde8e8; color: #c0392b; }
        .moderate-severity { background: #fef3e8; color: #d35400; }
        .mild-severity { background: #e8f8f0; color: #27ae60; }
    </style>
`); 