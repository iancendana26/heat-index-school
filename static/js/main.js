document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    const temperatureEl = document.getElementById('temperature');
    const humidityEl = document.getElementById('humidity');
    const heatIndexEl = document.getElementById('heatIndex');
    const alertStatusEl = document.getElementById('alertStatus');
    const weatherIconEl = document.getElementById('weatherIcon');
    const weatherDescriptionEl = document.getElementById('weatherDescription');
    const lastUpdatedEl = document.getElementById('lastUpdated');
    const alertModal = document.getElementById('alertModal');
    const alertsBtn = document.getElementById('alertsBtn');
    const closeBtn = document.querySelector('.close');

    // Alert history
    let alertHistory = [];

    // Update data every minute
    function updateData() {
        fetch('/api/current-data')
            .then(response => response.json())
            .then(data => {
                // Update temperature
                temperatureEl.textContent = `${data.temperature}°C`;
                temperatureEl.classList.add('updated');
                setTimeout(() => temperatureEl.classList.remove('updated'), 1000);

                // Update humidity
                humidityEl.textContent = `${data.humidity}%`;
                humidityEl.classList.add('updated');
                setTimeout(() => humidityEl.classList.remove('updated'), 1000);

                // Update heat index
                heatIndexEl.textContent = `${data.heat_index}°C`;
                heatIndexEl.classList.add('updated');
                setTimeout(() => heatIndexEl.classList.remove('updated'), 1000);

                // Update weather icon and description
                weatherIconEl.src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
                weatherDescriptionEl.textContent = data.description;

                // Update last updated time
                lastUpdatedEl.textContent = data.timestamp;

                // Update alert status
                updateAlertStatus(data.heat_index);
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    // Update forecast
    function updateForecast() {
        fetch('/api/forecast')
            .then(response => response.json())
            .then(data => {
                const forecastTimeline = document.querySelector('.forecast-timeline');
                forecastTimeline.innerHTML = '';

                let currentDate = '';
                data.forEach(item => {
                    const forecastItem = document.createElement('div');
                    forecastItem.className = 'forecast-item';

                    // Check if this is a new date
                    if (item.date !== currentDate) {
                        currentDate = item.date;
                    }

                    // Get appropriate icon based on heat index
                    let icon = '🌡️';
                    let iconTitle = 'Normal conditions';
                    if (item.heat_index >= 54) {
                        icon = '⚠️';
                        iconTitle = 'Extreme Danger';
                    } else if (item.heat_index >= 41) {
                        icon = '⚡';
                        iconTitle = 'Danger';
                    } else if (item.heat_index >= 32) {
                        icon = '⚪';
                        iconTitle = 'Caution';
                    }

                    forecastItem.innerHTML = `
                        <div class="forecast-date">${item.timestamp.split(',')[0]}</div>
                        <div class="forecast-time">${item.timestamp.split(',')[1]}</div>
                        <div class="forecast-icon" title="${iconTitle}">${icon}</div>
                        <div class="forecast-temp">Temp: ${item.temperature}°C</div>
                        <div class="forecast-heat-index">Heat Index: ${item.heat_index}°C</div>
                    `;

                    forecastTimeline.appendChild(forecastItem);
                });
            })
            .catch(error => console.error('Error fetching forecast:', error));
    }

    // Update alert status based on heat index
    function updateAlertStatus(heatIndex) {
        let status, className;

        if (heatIndex >= 54) {
            status = 'Extreme Danger';
            className = 'status-extreme';
            addAlert('Extreme Danger: Heat index is at dangerous levels!');
        } else if (heatIndex >= 41) {
            status = 'Danger';
            className = 'status-danger';
            addAlert('Danger: Heat index is at concerning levels.');
        } else if (heatIndex >= 32) {
            status = 'Caution';
            className = 'status-caution';
        } else {
            status = 'Safe';
            className = 'status-safe';
        }

        alertStatusEl.className = `alert-status ${className}`;
        alertStatusEl.innerHTML = `
            <span class="status-indicator"></span>
            <span class="status-text">Status: ${status}</span>
        `;
    }

    // Add alert to history
    function addAlert(message) {
        const timestamp = new Date().toLocaleString();
        alertHistory.unshift({ timestamp, message });
        
        // Keep only last 50 alerts
        if (alertHistory.length > 50) {
            alertHistory.pop();
        }

        updateAlertList();
    }

    // Update alert list in modal
    function updateAlertList() {
        const alertList = document.querySelector('.alert-list');
        alertList.innerHTML = alertHistory
            .map(alert => `
                <div class="alert-item">
                    <div class="alert-time">${alert.timestamp}</div>
                    <div class="alert-message">${alert.message}</div>
                </div>
            `)
            .join('');
    }

    // Modal controls
    alertsBtn.onclick = () => {
        alertModal.style.display = 'block';
    };

    closeBtn.onclick = () => {
        alertModal.style.display = 'none';
    };

    window.onclick = (event) => {
        if (event.target === alertModal) {
            alertModal.style.display = 'none';
        }
    };

    // Initial update
    updateData();
    updateForecast();

    // Set up periodic updates
    setInterval(updateData, 60000); // Update every minute
    setInterval(updateForecast, 5 * 60 * 1000); // Update forecast every 5 minutes
}); 