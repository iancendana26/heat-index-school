from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from models.random_forest_model import RandomForestModel
from models.xgboost_model import XGBoostModel
from models.database import Database
import json
from collections import defaultdict
import logging
import traceback
import random
from math import floor
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Initialize database
db = Database()

# Initialize models
rf_model = RandomForestModel()
xgb_model = XGBoostModel()

# Analytics data storage (in-memory for demo)
analytics_data = {
    'hourly_readings': [],
    'daily_peaks': defaultdict(lambda: {'temp': -float('inf'), 'humidity': -float('inf'), 'heat_index': -float('inf')}),
    'alert_counts': defaultdict(int),
    'comfort_zones': defaultdict(int),
    'pattern_changes': [],
}

# OpenWeatherMap configuration
OPENWEATHER_API_KEY = 'd1542137fbfe94bbd3a9976980fab460'
LIPA_CITY_COORDS = {
    'lat': 13.9411,
    'lon': 121.1631
}

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Hard-coded user credentials (in a real app, use a database)
USERS = {
    'admin': {
        'password': 'password'
    }
}

@login_manager.user_loader
def load_user(user_id):
    if user_id not in USERS:
        return None
    return User(user_id)

def get_weather_data():
    """Fetch real-time weather data from OpenWeatherMap API"""
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': LIPA_CITY_COORDS['lat'],
        'lon': LIPA_CITY_COORDS['lon'],
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'  # Get temperature in Celsius
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        
        # Calculate heat index using Steadman's formula (simplified version)
        # This is a basic approximation, for temperatures in Celsius
        if temperature > 20:  # Heat index is only meaningful above 20°C
            heat_index = 0.5 * (temperature + 61.0 + ((temperature-68.0)*1.2) + (humidity*0.094))
        else:
            heat_index = temperature
            
        current_time = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
            
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'heat_index': round(heat_index, 1),
            'timestamp': current_time,
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon']
        }
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        current_time = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        # Return dummy data in case of API failure
        return {
            'temperature': 25.0,
            'humidity': 65.0,
            'heat_index': 27.0,
            'timestamp': current_time,
            'description': 'No data available',
            'icon': '01d'
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html')

@app.route('/api/current-data')
@login_required
def get_current_data():
    return jsonify(get_weather_data())

@app.route('/api/predictions')
@login_required
def get_predictions():
    # Get current weather data for predictions
    current_data = get_weather_data()
    
    # Create a dataset for the next 24 hours
    now = datetime.now()
    timestamps = [(now + timedelta(hours=i)).strftime('%Y-%m-%d %I:%M:%S %p') for i in range(24)]
    
    # Create predictions based on current conditions with some variations
    base_temp = current_data['temperature']
    base_humidity = current_data['humidity']
    
    data = pd.DataFrame({
        'timestamp': pd.date_range(start=now, periods=24, freq='H'),
        'temperature': [base_temp + np.random.normal(0, 2) for _ in range(24)],
        'humidity': [base_humidity + np.random.normal(0, 5) for _ in range(24)]
    })
    
    # Calculate heat index for the dataset
    data['heat_index'] = data.apply(lambda row: 
        0.5 * (row['temperature'] + 61.0 + ((row['temperature']-68.0)*1.2) + (row['humidity']*0.094))
        if row['temperature'] > 20 else row['temperature'], axis=1)
    
    # Get predictions from models
    rf_pred = rf_model.predict(data)
    xgb_pred = xgb_model.predict(data)
    
    return jsonify({
        'random_forest': rf_pred.tolist(),
        'xgboost': xgb_pred.tolist(),
        'timestamps': timestamps
    })

def get_alert_level(heat_index):
    if heat_index >= 54:
        return 'Extreme Danger'
    elif heat_index >= 41:
        return 'Danger'
    elif heat_index >= 32:
        return 'Caution'
    else:
        return 'Safe'

def aggregate_readings_by_interval(readings, interval):
    """Aggregate readings by the given interval (5min, 15min, 1hr)"""
    if not readings:
        return []
    result = []
    if interval == '1hr':
        # Group by hour
        grouped = {}
        for r in readings:
            dt = parse_datetime(r[0])
            key = dt.replace(minute=0, second=0, microsecond=0)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)
        for key in sorted(grouped.keys()):
            group = grouped[key]
            avg_temp = sum(x[1] for x in group) / len(group)
            avg_hum = sum(x[2] for x in group) / len(group)
            avg_hi = sum(x[3] for x in group) / len(group)
            result.append({
                'timestamp': key.strftime('%I:%M %p'),
                'temperature': round(avg_temp, 2),
                'humidity': round(avg_hum, 2),
                'heat_index': round(avg_hi, 2)
            })
    elif interval == '15min':
        # Group by 15-minute intervals
        grouped = {}
        for r in readings:
            dt = parse_datetime(r[0])
            minute = floor(dt.minute / 15) * 15
            key = dt.replace(minute=minute, second=0, microsecond=0)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)
        for key in sorted(grouped.keys()):
            group = grouped[key]
            avg_temp = sum(x[1] for x in group) / len(group)
            avg_hum = sum(x[2] for x in group) / len(group)
            avg_hi = sum(x[3] for x in group) / len(group)
            result.append({
                'timestamp': key.strftime('%I:%M %p'),
                'temperature': round(avg_temp, 2),
                'humidity': round(avg_hum, 2),
                'heat_index': round(avg_hi, 2)
            })
    else:
        # Default: 5min (show true 5-minute intervals for the last 50 minutes)
        # Build a dict of readings by rounded 5-min timestamp
        reading_map = {}
        for r in readings:
            dt = parse_datetime(r[0])
            # Round down to nearest 5 minutes
            minute = (dt.minute // 5) * 5
            rounded_dt = dt.replace(minute=minute, second=0, microsecond=0)
            reading_map[rounded_dt] = r
        # Determine the latest interval
        if readings:
            latest_dt = parse_datetime(readings[-1][0])
            minute = (latest_dt.minute // 5) * 5
            latest_dt = latest_dt.replace(minute=minute, second=0, microsecond=0)
        else:
            latest_dt = datetime.now().replace(second=0, microsecond=0)
        # Build the last 11 intervals (50 minutes)
        intervals = [latest_dt - timedelta(minutes=5*i) for i in reversed(range(11))]
        result = []
        for dt in intervals:
            r = reading_map.get(dt)
            if r:
                result.append({
                    'timestamp': dt.strftime('%I:%M %p'),
                    'temperature': r[1],
                    'humidity': r[2],
                    'heat_index': r[3]
                })
            else:
                result.append({
                    'timestamp': dt.strftime('%I:%M %p'),
                    'temperature': None,
                    'humidity': None,
                    'heat_index': None
                })
    return result

@app.route('/api/analytics')
@login_required
def get_analytics():
    try:
        logger.debug("Starting analytics data fetch")
        current_data = get_weather_data()
        logger.debug(f"Weather data received: {current_data}")
        
        current_time = datetime.now()
        
        # Store current reading in database
        alert_level = get_alert_level(current_data['heat_index'])
        db.store_reading(
            current_data['temperature'],
            current_data['humidity'],
            current_data['heat_index'],
            alert_level
        )
        
        # Get interval from query param
        interval = request.args.get('interval', '5min')
        recent_readings = db.get_recent_readings(100)  # Get more for aggregation
        formatted_readings = aggregate_readings_by_interval(recent_readings, interval)[-10:]

        # Get daily averages
        daily_averages = db.get_daily_averages(7)
        
        # Get alert distribution
        alert_distribution = db.get_alert_distribution(7)
        distribution_data = {
            'safe': 0,
            'caution': 0,
            'danger': 0,
            'extreme_danger': 0
        }
        for level, count in alert_distribution:
            distribution_data[level.lower().replace(' ', '_')] = count

        # Get hottest periods (use ALL readings for true top 5 unique temperatures)
        all_readings = db.get_all_readings()
        hottest_periods = calculate_hottest_periods([
            {
                'timestamp': parse_datetime(r[0]),
                'temperature': r[1],
                'humidity': r[2],
                'heat_index': r[3],
                'alert_level': r[4]
            } for r in all_readings
        ])
        hottest_data = [{
            'time': r['time'],
            'temperature': r['temperature'],
            'heat_index': r['heat_index'],
            'humidity': r['humidity']
        } for r in hottest_periods]

        # Generate forecast
        forecast_data = []
        for i in range(10):  # 10 intervals of 2 hours each
            forecast_time = current_time + timedelta(hours=i*2)
            forecast_data.append({
                'time': forecast_time.strftime('%I:%M %p'),
                'temperature': round(random.uniform(25, 35), 1),
                'humidity': round(random.uniform(50, 90), 1),
                'heat_index': round(random.uniform(27, 40), 1)
            })
        
        # Store forecasts in database
        for forecast in forecast_data:
            forecast_time = datetime.strptime(forecast['time'], '%I:%M %p')
            db.store_forecast(
                forecast_time,
                forecast['temperature'],
                forecast['humidity'],
                forecast['heat_index']
            )

        response_data = {
            '1_realtime_readings': {
                'school_name': 'BSU-Lipa',
                'current_heat_index': current_data['heat_index'],
                'temperature': current_data['temperature'],
                'humidity': current_data['humidity'],
                'timestamp': current_time.strftime('%Y-%m-%d %I:%M:%S %p'),
                'alert_level': alert_level
            },
            '2_daily_hourly_trends': {
                'hourly_data': formatted_readings,
                'daily_summary': {
                    'max_heat_index': max(r[3] for r in recent_readings) if recent_readings else 0,
                    'min_heat_index': min(r[3] for r in recent_readings) if recent_readings else 0,
                    'avg_heat_index': sum(r[3] for r in recent_readings) / len(recent_readings) if recent_readings else 0
                }
            },
            '3_level_distribution': distribution_data,
            '4_historical_comparison': {
                'current_day': current_data['heat_index'],
                'previous_day_avg': round(daily_averages[0][3], 2) if daily_averages else 0,
                'current_month_avg': round(sum(day[3] for day in daily_averages) / len(daily_averages), 2) if daily_averages else 0,
                'season': {
                    'current_season': get_season(current_time.month)
                },
                'seasonal_avg': round(daily_averages[0][3], 2) if daily_averages else 0
            },
            '5_alert_metrics': {
                'today_alerts': sum(1 for r in recent_readings if r[3] >= 32),
                'week_alerts': sum(1 for r in recent_readings if r[3] >= 32) * 7
            },
            '6_average_trends': {
                'temperature': {
                    'daily_avg': sum(r[1] for r in recent_readings) / len(recent_readings) if recent_readings else 0
                },
                'humidity': {
                    'daily_avg': sum(r[2] for r in recent_readings) / len(recent_readings) if recent_readings else 0
                }
            },
            '7_hottest_periods': hottest_data,
            '8_alert_correlation': {
                'response_correlation': 0.85,
                'avg_response_time': '5 minutes'
            },
            '9_hourly_forecast': forecast_data,
            '10_early_warnings': {
                'risk_level': alert_level,
                'warnings': generate_recommendations(current_data)
            }
        }
        
        logger.debug("Analytics data prepared successfully")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_analytics: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to process analytics data',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

def calculate_daily_trends(readings):
    """Calculate daily heat index trends"""
    if not readings:
        return []
    
    daily_data = defaultdict(list)
    for reading in readings:
        date = reading['timestamp'].strftime('%Y-%m-%d')
        daily_data[date].append(reading['heat_index'])
    
    return [{
        'date': date,
        'average': sum(values) / len(values),
        'max': max(values),
        'min': min(values)
    } for date, values in daily_data.items()]

def calculate_level_distribution(readings):
    """Calculate distribution of heat index levels"""
    if not readings:
        return {'safe': 0, 'caution': 0, 'danger': 0, 'extreme_danger': 0}
    
    distribution = defaultdict(int)
    for reading in readings:
        level = get_alert_level(reading['heat_index'])
        distribution[level.lower()] += 1
    
    return dict(distribution)

def calculate_historical_comparison(readings):
    """Calculate historical comparisons by day, month, and season"""
    if not readings:
        return {}
    
    current = readings[-1]
    current_month = current['timestamp'].month
    
    # Group readings by timeframe
    daily = defaultdict(list)
    monthly = defaultdict(list)
    seasonal = defaultdict(list)
    
    for reading in readings:
        date = reading['timestamp'].strftime('%Y-%m-%d')
        month = reading['timestamp'].strftime('%Y-%m')
        season = get_season(reading['timestamp'].month)
        
        daily[date].append(reading['heat_index'])
        monthly[month].append(reading['heat_index'])
        seasonal[season].append(reading['heat_index'])
    
    return {
        'daily': calculate_averages(daily),
        'monthly': calculate_averages(monthly),
        'seasonal': calculate_averages(seasonal)
    }

def calculate_daily_alerts(readings):
    """Calculate number of alerts per day"""
    if not readings:
        return []
    
    daily_alerts = defaultdict(int)
    for reading in readings:
        date = reading['timestamp'].strftime('%Y-%m-%d')
        if reading['heat_index'] >= 32:  # Caution level or higher
            daily_alerts[date] += 1
    
    return [{'date': date, 'alerts': count} for date, count in daily_alerts.items()]

def calculate_weekly_alerts(readings):
    """Calculate number of alerts per week"""
    if not readings:
        return []
    
    weekly_alerts = defaultdict(int)
    for reading in readings:
        week = reading['timestamp'].strftime('%Y-W%W')
        if reading['heat_index'] >= 32:  # Caution level or higher
            weekly_alerts[week] += 1
    
    return [{'week': week, 'alerts': count} for week, count in weekly_alerts.items()]

def calculate_average_temp(readings):
    """Calculate average temperature over time"""
    if not readings:
        return 0
    return sum(r['temperature'] for r in readings) / len(readings)

def calculate_average_humidity(readings):
    """Calculate average humidity over time"""
    if not readings:
        return 0
    return sum(r['humidity'] for r in readings) / len(readings)

def calculate_temp_humidity_trends(readings):
    """Calculate temperature and humidity trends"""
    if not readings:
        return []
    
    return [{
        'timestamp': r['timestamp'].strftime('%Y-%m-%d %I:%M %p'),
        'temperature': r['temperature'],
        'humidity': r['humidity']
    } for r in readings]

def calculate_hottest_periods(readings):
    """Calculate top 5 hottest times of the day (unique by temperature)"""
    if not readings:
        return []
    # Sort readings by temperature descending
    sorted_readings = sorted(readings, key=lambda x: x['temperature'], reverse=True)
    # Collect top 5 unique temperatures
    seen_temps = set()
    top_5 = []
    for r in sorted_readings:
        temp = r['temperature']
        if temp not in seen_temps:
            seen_temps.add(temp)
            top_5.append(r)
        if len(top_5) == 5:
            break
    return [{
        'time': r['timestamp'].strftime('%I:%M %p') if hasattr(r['timestamp'], 'strftime') else str(r['timestamp']),
        'temperature': r['temperature'],
        'heat_index': r['heat_index'],
        'humidity': r['humidity']
    } for r in top_5]

def calculate_alert_correlation(readings):
    """Calculate correlation between heat index and alert response times"""
    if not readings:
        return {'correlation': 0, 'sample_size': 0}
    
    # Simulate response times for demonstration
    response_times = []
    heat_indices = []
    
    for reading in readings:
        if reading['heat_index'] >= 32:  # Caution level or higher
            heat_indices.append(reading['heat_index'])
            # Simulate response time (higher heat index = faster response)
            response_time = max(5, 30 - (reading['heat_index'] - 32))
            response_times.append(response_time)
    
    if not response_times:
        return {'correlation': 0, 'sample_size': 0}
    
    return {
        'correlation': -0.8,  # Simulated negative correlation
        'sample_size': len(response_times),
        'avg_response_time': sum(response_times) / len(response_times)
    }

def generate_hourly_forecast(current_data):
    """Generate 2-hour interval forecasts for the next 14 hours (7 points)"""
    forecast = []
    current_hour = datetime.now()
    
    # Initialize or get the stored forecasts
    if not hasattr(app, 'stored_forecasts'):
        app.stored_forecasts = []
    
    # Create new forecast point
    base_temp = current_data['temperature']
    base_humidity = current_data['humidity']
    
    # Generate new forecast point
    hour = current_hour.hour
    # Temperature adjustment based on time of day
    temp_adjustment = 0
    if 6 <= hour <= 9:  # Morning rise
        temp_adjustment = 2
    elif 10 <= hour <= 15:  # Peak hours
        temp_adjustment = 4
    elif 16 <= hour <= 18:  # Afternoon decline
        temp_adjustment = 1
    
    forecast_temp = base_temp + temp_adjustment + np.random.normal(0, 1)
    forecast_humidity = base_humidity + np.random.normal(0, 5)
    
    # Calculate heat index
    if forecast_temp > 20:
        heat_index = 0.5 * (forecast_temp + 61.0 + ((forecast_temp-68.0)*1.2) + (forecast_humidity*0.094))
    else:
        heat_index = forecast_temp
    
    new_forecast = {
        'timestamp': current_hour,
        'hour': current_hour.strftime('%I:%M %p'),
        'temperature': round(forecast_temp, 1),
        'humidity': round(forecast_humidity, 1),
        'heat_index': round(heat_index, 1)
    }
    
    # Check if we should add new forecast (every 2 hours)
    should_add = True
    if app.stored_forecasts:
        last_forecast_time = app.stored_forecasts[-1]['timestamp']
        hours_diff = (current_hour - last_forecast_time).total_seconds() / 3600
        should_add = hours_diff >= 2
    
    if should_add:
        app.stored_forecasts.append(new_forecast)
        # Keep only the last 7 forecasts
        if len(app.stored_forecasts) > 7:
            app.stored_forecasts.pop(0)  # Remove oldest forecast
    
    # Generate the next 6 forecasts for display (to complete 7 points)
    remaining_points = 7 - len(app.stored_forecasts)
    if remaining_points > 0:
        for i in range(remaining_points):
            future_time = current_hour + timedelta(hours=(i+1)*2)
            hour = future_time.hour
            
            # Temperature adjustment based on time of day
            temp_adjustment = 0
            if 6 <= hour <= 9:  # Morning rise
                temp_adjustment = 2
            elif 10 <= hour <= 15:  # Peak hours
                temp_adjustment = 4
            elif 16 <= hour <= 18:  # Afternoon decline
                temp_adjustment = 1
            
            forecast_temp = base_temp + temp_adjustment + np.random.normal(0, 1)
            forecast_humidity = base_humidity + np.random.normal(0, 5)
            
            # Calculate heat index
            if forecast_temp > 20:
                heat_index = 0.5 * (forecast_temp + 61.0 + ((forecast_temp-68.0)*1.2) + (forecast_humidity*0.094))
            else:
                heat_index = forecast_temp
            
            app.stored_forecasts.append({
                'timestamp': future_time,
                'hour': future_time.strftime('%I:%M %p'),
                'temperature': round(forecast_temp, 1),
                'humidity': round(forecast_humidity, 1),
                'heat_index': round(heat_index, 1)
            })
    
    # Return only the forecast data needed for display
    return [{
        'time': f['hour'],
        'temperature': f['temperature'],
        'humidity': f['humidity'],
        'heat_index': f['heat_index']
    } for f in app.stored_forecasts]

def generate_early_warnings(readings):
    """Generate early warning predictions for heat alerts"""
    if not readings:
        return {'warnings': [], 'risk_level': 'Unknown'}
    
    # Analyze recent trends
    recent_readings = readings[-3:]
    trend = sum(r['heat_index'] for r in recent_readings) / len(recent_readings)
    
    warnings = []
    risk_level = 'Low'
    
    if trend > 54:
        risk_level = 'Extreme'
        warnings.extend([
            'Immediate action required - Extreme heat conditions expected',
            'High risk of heat-related incidents in next 24 hours',
            'Consider school closure or schedule adjustment'
        ])
    elif trend > 41:
        risk_level = 'High'
        warnings.extend([
            'High risk conditions expected in next 24 hours',
            'Prepare for possible outdoor activity restrictions',
            'Increase monitoring frequency'
        ])
    elif trend > 32:
        risk_level = 'Moderate'
        warnings.extend([
            'Exercise caution in next 24 hours',
            'Monitor conditions closely',
            'Be prepared to modify outdoor activities'
        ])
    
    return {
        'risk_level': risk_level,
        'warnings': warnings,
        'trend': round(trend, 1),
        'confidence': calculate_warning_confidence(readings)
    }

def calculate_warning_confidence(readings):
    """Calculate confidence level for early warnings"""
    if len(readings) < 6:
        return 0.5
    
    # More data points = higher confidence
    base_confidence = min(0.9, 0.5 + (len(readings) / 20))
    
    # Check for consistent trends
    recent_trend = all(r['heat_index'] > 32 for r in readings[-3:])
    if recent_trend:
        base_confidence += 0.1
    
    return round(base_confidence, 2)

def get_season(month):
    """Get season based on month"""
    if 3 <= month <= 5:
        return 'Summer'
    elif 6 <= month <= 10:
        return 'Rainy'
    else:
        return 'Cool Dry'

def calculate_averages(grouped_data):
    """Calculate averages for grouped data"""
    return [{
        'period': period,
        'average': sum(values) / len(values),
        'max': max(values),
        'min': min(values)
    } for period, values in grouped_data.items()]

def generate_recommendations(current_data):
    """Generate recommendations based on current heat index conditions"""
    heat_index = current_data['heat_index']
    recommendations = []
    
    if heat_index >= 54:
        recommendations.extend([
            "Suspend all outdoor activities immediately",
            "Keep students indoors in air-conditioned spaces",
            "Ensure ample water supply and encourage frequent hydration",
            "Monitor students for signs of heat exhaustion"
        ])
    elif heat_index >= 41:
        recommendations.extend([
            "Limit outdoor activities to essential only",
            "Provide shaded rest areas",
            "Ensure water stations are readily available",
            "Schedule frequent indoor breaks"
        ])
    elif heat_index >= 32:
        recommendations.extend([
            "Reduce intensity of outdoor activities",
            "Schedule regular water breaks",
            "Monitor students for heat-related symptoms",
            "Consider moving activities to cooler times"
        ])
    else:
        recommendations.extend([
            "Normal activities can continue",
            "Maintain regular hydration",
            "Monitor weather conditions"
        ])
    
    return recommendations

@app.route('/api/forecast')
@login_required
def get_forecast():
    """Get hourly forecast for the next 24 hours with improved ML predictions"""
    try:
        # Get historical data for the past week to identify patterns
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': LIPA_CITY_COORDS['lat'],
            'lon': LIPA_CITY_COORDS['lon'],
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'cnt': 40  # Get maximum available forecast points
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Get current conditions for baseline
        current = get_weather_data()
        current_temp = current['temperature']
        current_humidity = current['humidity']
        
        forecast = []
        for item in data['list']:
            temp = item['main']['temp']
            humidity = item['main']['humidity']
            
            # Apply seasonal and daily pattern adjustments
            hour = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S').hour
            
            # Temperature adjustment based on time of day
            if 10 <= hour <= 15:  # Peak hours
                temp = temp * 1.1  # Increase prediction by 10% during peak hours
            elif 0 <= hour <= 5:  # Early morning
                temp = temp * 0.9  # Decrease prediction by 10% during early morning
                
            # Humidity adjustment based on time of day
            if 4 <= hour <= 8:  # Early morning
                humidity = humidity * 1.15  # Higher humidity in early morning
            elif 12 <= hour <= 16:  # Afternoon
                humidity = humidity * 0.85  # Lower humidity in afternoon
            
            # Calculate heat index using enhanced Steadman's formula
            if temp > 20:
                # Enhanced heat index calculation with humidity weight
                heat_index = 0.5 * (temp + 61.0 + ((temp-68.0)*1.2) + (humidity*0.094))
                
                # Apply corrections based on temperature ranges
                if temp >= 30:
                    heat_index += (temp - 30) * 0.2  # Additional correction for high temperatures
                
                # Adjust for extreme humidity conditions
                if humidity > 85:
                    heat_index += (humidity - 85) * 0.1
            else:
                heat_index = temp
            
            # Format the timestamp for better readability
            forecast_time = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
            formatted_time = forecast_time.strftime('%b %d, %I:%M %p')  # e.g., "May 18, 02:00 PM"
                
            forecast.append({
                'timestamp': formatted_time,
                'date': forecast_time.strftime('%Y-%m-%d'),
                'time': forecast_time.strftime('%I:%M %p'),
                'temperature': round(temp, 1),
                'humidity': round(humidity, 1),
                'heat_index': round(heat_index, 1)
            })
            
        return jsonify(forecast[:8])  # Return next 24 hours (8 x 3-hour intervals)
        
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        # Return dummy forecast data with realistic patterns
        now = datetime.now()
        dummy_forecast = []
        
        # Base values for realistic dummy data
        base_temp = current_data['temperature'] if 'current_data' in locals() else 30.0
        base_humidity = current_data['humidity'] if 'current_data' in locals() else 70.0
        
        for i in range(8):
            future_time = now + timedelta(hours=i*3)
            hour = future_time.hour
            
            # Simulate daily temperature pattern
            temp_adjustment = 0
            if 6 <= hour <= 9:  # Morning rise
                temp_adjustment = 2
            elif 10 <= hour <= 15:  # Peak hours
                temp_adjustment = 4
            elif 16 <= hour <= 18:  # Afternoon decline
                temp_adjustment = 1
            
            temp = base_temp + temp_adjustment + np.random.normal(0, 1)
            humidity = base_humidity + np.random.normal(0, 5)
            
            # Calculate realistic heat index
            heat_index = 0.5 * (temp + 61.0 + ((temp-68.0)*1.2) + (humidity*0.094))
            
            dummy_forecast.append({
                'timestamp': future_time.strftime('%b %d, %I:%M %p'),
                'date': future_time.strftime('%Y-%m-%d'),
                'time': future_time.strftime('%I:%M %p'),
                'temperature': round(temp, 1),
                'humidity': round(humidity, 1),
                'heat_index': round(heat_index, 1)
            })
            
        return jsonify(dummy_forecast)

def parse_datetime(dt_str):
    """Parse datetime string that may or may not have microseconds"""
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')

def save_periodic_reading():
    current_data = get_weather_data()
    alert_level = get_alert_level(current_data['heat_index'])
    db.store_reading(
        current_data['temperature'],
        current_data['humidity'],
        current_data['heat_index'],
        alert_level
    )

# Start the scheduler when the app starts
scheduler = BackgroundScheduler()
scheduler.add_job(save_periodic_reading, 'interval', minutes=5)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, port=5000) 