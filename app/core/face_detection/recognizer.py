import pickle
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier

class FaceRecognizer:
    def __init__(self, model_type='adaboost'):
        self.model_type = model_type
        if model_type == 'knn':
            self.model = KNeighborsClassifier(n_neighbors=3)
        elif model_type == 'svm':
            self.model = SVC(kernel='rbf', probability=True)
        elif model_type == 'mlp':
            self.model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500)
        elif model_type == 'rf':
            self.model = RandomForestClassifier(n_estimators=100)
        elif model_type == 'adaboost':
            base_estimator = DecisionTreeClassifier(max_depth=1)
            self.model = AdaBoostClassifier(base_estimator=base_estimator, n_estimators=100, learning_rate=0.5)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        self.faces = None
        self.labels = None

    def load_data(self, face_path, label_path):
        with open(face_path, 'rb') as f:
            self.faces = pickle.load(f)
        with open(label_path, 'rb') as f:
            self.labels = pickle.load(f)
        print(f"[DEBUG] Loaded data: faces shape={self.faces.shape}, labels length={len(self.labels)}")

    def train(self):
        if self.faces is not None and self.labels is not None:
            print(f"[DEBUG] Training model with {len(self.labels)} samples")
            self.model.fit(self.faces, self.labels)

    def predict(self, face):
        return self.model.predict([face])[0]
    
    def predict_with_confidence(self, face):
        try:
            probas = self.model.predict_proba([face])[0]
            max_index = probas.argmax()
            confidence = probas[max_index]
            predicted_label = self.model.classes_[max_index]
            print(f"[DEBUG] Probabilities for each label: {dict(zip(self.model.classes_, probas))}")
            print(f"[DEBUG] Predicted label: {predicted_label}, confidence: {confidence}")
            return predicted_label, confidence
        except Exception as e:
            print(f"[ERROR] Error in predict_with_confidence: {e}")
            return None, 0.0