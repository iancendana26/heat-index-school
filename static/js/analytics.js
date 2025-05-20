// Analytics page specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Chart.js global configuration
    Chart.defaults.font.family = "'Arial', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#7f8c8d';

    // Handle alerts button click
    document.getElementById('alertsBtn').addEventListener('click', function(e) {
        e.preventDefault();
        // You can implement alerts modal or navigation here
    });

    // Format timestamps for better readability
    function formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Format duration for response times
    function formatDuration(minutes) {
        if (minutes < 60) {
            return `${minutes} min`;
        }
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours}h ${remainingMinutes}m`;
    }

    // Update chart colors based on risk levels
    function getColorForRiskLevel(level) {
        const colors = {
            'Safe': '#2ecc71',
            'Caution': '#f1c40f',
            'Danger': '#e67e22',
            'Extreme': '#e74c3c'
        };
        return colors[level] || '#95a5a6';
    }

    // Format temperature values
    function formatTemperature(value) {
        return `${value.toFixed(1)}°C`;
    }

    // Format humidity values
    function formatHumidity(value) {
        return `${value.toFixed(0)}%`;
    }

    // Error handling for failed API requests
    function handleApiError(error) {
        console.error('API Error:', error);
        // You can implement user-friendly error messages here
    }

    // Export functions for use in the main analytics page
    window.analyticsHelpers = {
        formatTime,
        formatDuration,
        getColorForRiskLevel,
        formatTemperature,
        formatHumidity,
        handleApiError
    };
}); 