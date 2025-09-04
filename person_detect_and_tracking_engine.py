from ultralytics import YOLO
import cv2
import numpy as np


class PersonTrackingEngine:
    def __init__(self, model_path="Model/yolov8m.pt"):
        self.model = YOLO(model_path)

    def process_frame(self, frame):
        """
        Bir kareyi işler, insanları takip eder ve her bir nesne için
        ID, kutu ve merkez bilgilerini içeren bir SÖZLÜK LİSTESİ döndürür.
        """
        results = self.model.track(frame, persist=True, classes=0, verbose=False)

        annotated_frame = results[0].plot()

        tracked_objects = []
        # Takip ID'leri mevcutsa işlemleri yap
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = box
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)

                # --- ANA DÜZELTME BURADA ---
                # Veriyi demet (tuple) yerine sözlük (dictionary) olarak ekliyoruz.
                # Bu sayede diğer modüller bu veriye obj['id'] ve obj['center'] gibi
                # anahtarlarla sorunsuzca erişebilir.
                tracked_objects.append({
                    'id': track_id,
                    'box': (x1, y1, x2, y2),
                    'center': (center_x, center_y)
                })

        person_count = len(tracked_objects)

        return annotated_frame, person_count, tracked_objects
