import pickle
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier

class FaceRecognizer:
    def __init__(self, model_type="svm"):
        """Khởi tạo lớp FaceRecognizer với loại mô hình được chỉ định."""
        self.model_type = model_type
        if model_type == "knn":
            self.model = KNeighborsClassifier(n_neighbors=3)
        elif model_type == "svm":
            self.model = SVC(kernel="rbf", probability=True)
        elif model_type == "mlp":
            self.model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500)
        elif model_type == "rf":
            self.model = RandomForestClassifier(n_estimators=100)
        elif model_type == "adaboost":
            base_estimator = DecisionTreeClassifier(max_depth=1)
            self.model = AdaBoostClassifier(
                base_estimator=base_estimator, n_estimators=100, learning_rate=0.5
            )
        else:
            raise ValueError(f"Loại mô hình không được hỗ trợ: {model_type}")

        self.faces = None
        self.labels = None
        self.classes_ = None  # Lưu danh sách lớp sau khi huấn luyện

    def load_data(self, face_path, label_path):
        """Tải dữ liệu khuôn mặt và nhãn từ file."""
        with open(face_path, "rb") as f:
            self.faces = pickle.load(f)
        with open(label_path, "rb") as f:
            self.labels = pickle.load(f)
        print(f"[GỠ LỖI] Đã tải dữ liệu: hình dạng khuôn mặt={self.faces.shape}, độ dài nhãn={len(self.labels)}")

    def train(self):
        """Huấn luyện mô hình với dữ liệu khuôn mặt và nhãn."""
        if self.faces is None or self.labels is None:
            raise ValueError("Dữ liệu khuôn mặt hoặc nhãn chưa được tải. Hãy gọi load_data trước.")
        print(f"[GỠ LỖI] Huấn luyện mô hình với {len(self.labels)} mẫu")
        self.model.fit(self.faces, self.labels)
        # Gán self.classes_ sau khi huấn luyện
        if hasattr(self.model, 'classes_'):
            self.classes_ = self.model.classes_
        else:
            self.classes_ = np.unique(self.labels)
        print(f"[GỠ LỖI] Classes sau huấn luyện: {self.classes_}")

    def predict(self, face):
        """Dự đoán nhãn cho một khuôn mặt."""
        face = np.array(face).reshape(1, -1)  # Đảm bảo định dạng đúng
        return self.model.predict(face)[0]

    def predict_with_confidence(self, face):
        """Dự đoán nhãn với độ tin cậy."""
        try:
            # Kiểm tra xem self.classes_ đã được khởi tạo chưa
            if self.classes_ is None:
                raise ValueError("self.classes_ chưa được khởi tạo. Hãy huấn luyện hoặc tải mô hình trước.")
            
            face = np.array(face).reshape(1, -1)  # Đảm bảo định dạng đúng
            probas = self.model.predict_proba(face)[0]  # Lấy xác suất dự đoán
            max_index = probas.argmax()  # Chỉ số của xác suất cao nhất
            confidence = probas[max_index]  # Độ tin cậy
            predicted_label = self.classes_[max_index]  # Nhãn dự đoán
            
            # In thông tin gỡ lỗi
            print(f"[GỠ LỖI] Xác suất cho mỗi nhãn: {dict(zip(self.classes_, probas))}")
            print(f"[GỠ LỖI] Nhãn dự đoán: {predicted_label}, độ tin cậy: {confidence}")
            
            return predicted_label, float(confidence)
        except Exception as e:
            print(f"[LỖI] Lỗi trong predict_with_confidence: {e}")
            return None, 0.0

    def save(self, path):
        """Lưu mô hình học máy và classes_ vào file."""
        try:
            if self.classes_ is None:
                raise ValueError("self.classes_ chưa được khởi tạo. Không thể lưu mô hình.")
            with open(path, "wb") as f:
                pickle.dump({'model': self.model, 'classes_': self.classes_}, f)  # Lưu từ điển
            print(f"[THÀNH CÔNG] Mô hình đã được lưu vào {path}")
        except Exception as e:
            print(f"[LỖI] Lỗi khi lưu mô hình: {e}")
            raise

    @staticmethod
    def load(path, model_type="svm"):
        """Tạo đối tượng FaceRecognizer mới và tải mô hình học máy từ file."""
        try:
            recognizer = FaceRecognizer(model_type=model_type)
            with open(path, "rb") as f:
                data = pickle.load(f)
                if not isinstance(data, dict) or 'model' not in data or 'classes_' not in data:
                    raise ValueError("Tệp mô hình không đúng định dạng: cần chứa 'model' và 'classes_'")
                recognizer.model = data['model']
                recognizer.classes_ = data['classes_']
            print(f"[THÀNH CÔNG] Mô hình đã được tải từ {path}")
            print(f"[GỠ LỖI] Đã tải classes: {recognizer.classes_}")
            return recognizer
        except Exception as e:
            print(f"[LỖI] Lỗi khi tải mô hình: {e}")
            raise