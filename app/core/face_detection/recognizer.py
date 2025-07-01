import pickle
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier

class FaceRecognizer:
    def __init__(self, model_type='knn'):
        self.model_type = model_type
        if model_type == 'knn':
            self.model = KNeighborsClassifier(n_neighbors=3)
        elif model_type == 'svm':
            self.model = SVC(kernel='linear', probability=True)
        elif model_type == 'mlp':
            self.model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500)
        elif model_type == 'rf':
            self.model = RandomForestClassifier(n_estimators=100)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        self.faces = None
        self.labels = None

    def load_data(self, face_path, label_path):
        with open(face_path, 'rb') as f:
            self.faces = pickle.load(f)
        with open(label_path, 'rb') as f:
            self.labels = pickle.load(f)

    def train(self):
        if self.faces is not None and self.labels is not None:
            self.model.fit(self.faces, self.labels)

    def predict(self, face):
        return self.model.predict([face])[0]
    
    def predict_with_confidence(self, face):
        probas = self.model.predict_proba([face])[0]
        max_index = probas.argmax()
        confidence = probas[max_index]
        predicted_label = self.model.classes_[max_index]
        return predicted_label, confidence