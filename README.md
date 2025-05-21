# Heat Index Monitoring and Danger Alert System

A machine learning-powered system for monitoring and predicting heat index levels in school environments in Lipa City, Batangas. The system provides real-time alerts and visualizations through an interactive dashboard.

## Features

- Real-time heat index monitoring (OpenWeatherMap integration)
- Multiple ML models for accurate predictions (Random Forest, XGBoost, LSTM)
- Interactive dashboard and analytics with Chart.js visualizations
- Alert system for dangerous heat levels
- Historical and pattern data analysis
- User authentication (Flask-Login)
- Professional, responsive UI (HTML/CSS/JS)

## Technical Stack

- Python 3.8+
- Flask (web framework)
- Flask-Login (authentication)
- Scikit-learn, TensorFlow, XGBoost (ML models)
- Pandas and NumPy (data processing)
- Chart.js (frontend visualizations)
- OpenWeatherMap API (real-time weather data)

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (see below)
4. Run the application (development):
```bash
python app.py
```

5. For production, use Gunicorn:
```bash
gunicorn -w 4 app:app
```

## Environment Variables
Create a `.env` file in the project root with the following:
```
FLASK_SECRET_KEY=Qw8k2n3Jv9pLz1xYb4t6s7u8v0wXyZ1aBcDeFgHiJkLmNoPqR
OPENWEATHER_API_KEY=d1542137fbfe94bbd3a9976980fab460
```

## Models

The system implements three different models for heat index prediction:
1. Random Forest Regressor
2. XGBoost
3. LSTM Neural Network

## Project Structure

```
├── app.py                 # Main Flask application
├── models/                # ML model implementations (random_forest_model.py, xgboost_model.py, lstm_model.py, database.py)
├── static/                # Static files (css/style.css, js/analytics.js, js/dashboard.js, js/main.js)
├── templates/             # HTML templates (dashboard, analytics, login, etc.)
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── Procfile               # For Heroku or Gunicorn deployment
└── heat_index_data.db     # SQLite database (auto-created)
```

## Usage

1. Access the dashboard at `http://localhost:5000`
2. Log in with your credentials (default: admin/password)
3. View real-time heat index measurements
4. Check predictions and alerts
5. Analyze historical and pattern data through visualizations

## Deployment

- The application can be deployed to any cloud platform supporting Python (Heroku, Linux VPS, etc.)
- For production, use Gunicorn or another WSGI server
- Set environment variables for security and API keys
- Use a reverse proxy (e.g., Nginx) for HTTPS and static file serving

## Troubleshooting & Support
- Ensure your OpenWeatherMap API key is valid and has not exceeded its quota
- For database issues, delete `heat_index_data.db` to reset (data will be lost)
- For UI or analytics issues, check browser console and Flask logs
- For further support, contact the project maintainer 