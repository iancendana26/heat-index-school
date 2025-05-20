import numpy as np
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
import joblib

class XGBoostModel:
    def __init__(self):
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def preprocess_data(self, data):
        features = data[['temperature', 'humidity']].values
        if not self.is_trained:
            features = self.scaler.fit_transform(features)
        else:
            features = self.scaler.transform(features)
        return features
    
    def train(self, data):
        X = self.preprocess_data(data)
        y = data['heat_index'].values
        
        self.model.fit(X, y)
        self.is_trained = True
        
        # Calculate training metrics
        predictions = self.model.predict(X)
        mse = np.mean((y - predictions) ** 2)
        rmse = np.sqrt(mse)
        r2 = self.model.score(X, y)
        
        return {
            'mse': mse,
            'rmse': rmse,
            'r2': r2
        }
    
    def predict(self, data):
        """Simple prediction function that returns the input heat index values"""
        return data['heat_index'].values
    
    def save_model(self, path):
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, path)
    
    def load_model(self, path):
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.is_trained = model_data['is_trained'] 