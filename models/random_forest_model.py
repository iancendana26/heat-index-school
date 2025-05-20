import numpy as np

class RandomForestModel:
    def __init__(self):
        pass

    def predict(self, data):
        """Simple prediction function that returns the input heat index values"""
        return data['heat_index'].values 