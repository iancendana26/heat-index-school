import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='heat_index_data.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize the database with required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create readings table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    heat_index REAL NOT NULL,
                    alert_level TEXT NOT NULL
                )
                ''')
                
                # Create forecasts table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    forecast_time DATETIME NOT NULL,
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL,
                    heat_index REAL NOT NULL
                )
                ''')
                
                # Create alerts table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    alert_level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def store_reading(self, temperature, humidity, heat_index, alert_level):
        """Store a new reading in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                INSERT INTO readings (timestamp, temperature, humidity, heat_index, alert_level)
                VALUES (?, ?, ?, ?, ?)
                ''', (current_time, temperature, humidity, heat_index, alert_level))
                conn.commit()
                logger.debug(f"Stored new reading: temp={temperature}, humidity={humidity}, heat_index={heat_index}")
        except Exception as e:
            logger.error(f"Error storing reading: {str(e)}")
            raise

    def store_forecast(self, forecast_time, temperature, humidity, heat_index):
        """Store a new forecast in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                forecast_time_str = forecast_time.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                INSERT INTO forecasts (timestamp, forecast_time, temperature, humidity, heat_index)
                VALUES (?, ?, ?, ?, ?)
                ''', (current_time, forecast_time_str, temperature, humidity, heat_index))
                conn.commit()
                logger.debug(f"Stored new forecast for {forecast_time_str}")
        except Exception as e:
            logger.error(f"Error storing forecast: {str(e)}")
            raise

    def store_alert(self, alert_level, message):
        """Store a new alert in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                INSERT INTO alerts (timestamp, alert_level, message)
                VALUES (?, ?, ?)
                ''', (current_time, alert_level, message))
                conn.commit()
                logger.debug(f"Stored new alert: {alert_level} - {message}")
        except Exception as e:
            logger.error(f"Error storing alert: {str(e)}")
            raise

    def get_recent_readings(self, limit=10):
        """Get the most recent readings"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT timestamp, temperature, humidity, heat_index, alert_level
                FROM readings
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (limit,))
                # Reverse the results to get chronological order
                results = cursor.fetchall()
                return list(reversed(results))
        except Exception as e:
            logger.error(f"Error getting recent readings: {str(e)}")
            return []

    def get_daily_averages(self, days=7):
        """Get daily average readings for the specified number of days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT 
                    date(timestamp) as date,
                    AVG(temperature) as avg_temp,
                    AVG(humidity) as avg_humidity,
                    AVG(heat_index) as avg_heat_index
                FROM readings
                WHERE timestamp >= datetime('now', ?)
                GROUP BY date(timestamp)
                ORDER BY date DESC
                ''', (f'-{days} days',))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting daily averages: {str(e)}")
            return []

    def get_alert_distribution(self, days=7):
        """Get distribution of alert levels for the specified number of days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT 
                    alert_level,
                    COUNT(*) as count
                FROM readings
                WHERE timestamp >= datetime('now', ?)
                GROUP BY alert_level
                ''', (f'-{days} days',))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting alert distribution: {str(e)}")
            return []

    def get_hottest_periods(self, limit=5):
        """Get the hottest periods based on heat index"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT timestamp, temperature, humidity, heat_index
                FROM readings
                ORDER BY heat_index DESC
                LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting hottest periods: {str(e)}")
            return []

    def get_forecast_accuracy(self, hours=24):
        """Calculate forecast accuracy by comparing forecasts with actual readings"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT 
                    f.forecast_time,
                    f.heat_index as forecast_heat_index,
                    r.heat_index as actual_heat_index
                FROM forecasts f
                LEFT JOIN readings r ON datetime(f.forecast_time) = datetime(r.timestamp)
                WHERE f.timestamp >= datetime('now', ?)
                ORDER BY f.forecast_time DESC
                ''', (f'-{hours} hours',))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting forecast accuracy: {str(e)}")
            return []

    def get_all_readings(self):
        """Get all readings from the database, ordered by timestamp ascending"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT timestamp, temperature, humidity, heat_index, alert_level
                FROM readings
                ORDER BY timestamp ASC
                ''')
                results = cursor.fetchall()
                return list(results)
        except Exception as e:
            logger.error(f"Error getting all readings: {str(e)}")
            return [] 