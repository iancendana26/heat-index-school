import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import joblib
from apscheduler.schedulers.background import BackgroundScheduler

class LSTMModel:
    def __init__(self):
        self.model = self._build_model()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.sequence_length = 24  # 24 hours of data for sequence
    
    def _build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, input_shape=(self.sequence_length, 2)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def preprocess_data(self, data):
        features = data[['temperature', 'humidity']].values
        if not self.is_trained:
            features = self.scaler.fit_transform(features)
        else:
            features = self.scaler.transform(features)
            
        # Create sequences
        X = []
        y = []
        for i in range(len(features) - self.sequence_length):
            X.append(features[i:(i + self.sequence_length)])
            y.append(data['heat_index'].values[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train(self, data, epochs=50, batch_size=32):
        X, y = self.preprocess_data(data)
        
        if len(X) == 0:
            return {
                'mse': None,
                'rmse': None,
                'r2': None
            }
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=0
        )
        
        self.is_trained = True
        
        # Calculate training metrics
        predictions = self.model.predict(X)
        mse = np.mean((y - predictions.flatten()) ** 2)
        rmse = np.sqrt(mse)
        
        # Calculate R2 score
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        ss_res = np.sum((y - predictions.flatten()) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        
        return {
            'mse': mse,
            'rmse': rmse,
            'r2': r2
        }
    
    def predict(self, data):
        if not self.is_trained:
            # For demonstration, return dummy predictions
            return np.zeros(len(data))
        
        X, _ = self.preprocess_data(data)
        if len(X) == 0:
            return np.zeros(len(data))
        
        predictions = self.model.predict(X)
        
        # Pad the beginning with zeros since we can't predict without enough history
        padded_predictions = np.zeros(len(data))
        padded_predictions[self.sequence_length:] = predictions.flatten()
        
        return padded_predictions
    
    def save_model(self, path):
        # Save Keras model
        self.model.save(f"{path}_keras")
        
        # Save other attributes
        model_data = {
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, f"{path}_data")
    
    def load_model(self, path):
        # Load Keras model
        self.model = tf.keras.models.load_model(f"{path}_keras")
        
        # Load other attributes
        model_data = joblib.load(f"{path}_data")
        self.scaler = model_data['scaler']
        self.is_trained = model_data['is_trained'] 

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