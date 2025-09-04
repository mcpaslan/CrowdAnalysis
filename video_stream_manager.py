import cv2
from logger_config import logger  # YENİ: Merkezi logger'ı import ediyoruz


class VideoStreamManager:
    """
    Video kaynağından (dosya veya kamera) görüntü akışını yöneten sınıf.
    """

    def __init__(self, source):
        self.source = source
        self.cap = None
        self.is_running = False

    def start_stream(self):
        """
        Video akışını başlatır ve bağlantıyı kontrol eder.
        """
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            logger.error(f"Hata: Video kaynağı açılamadı -> {self.source}")  # DEĞİŞTİ
            self.is_running = False
            return False

        self.is_running = True
        logger.info(f"Video akışı başarıyla başlatıldı: {self.source}")  # DEĞİŞTİ
        return True

    def get_frame(self):
        """
        Akıştan bir sonraki kareyi (frame) okur.
        """
        if not self.is_running or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        return ret, frame

    def stop_stream(self):
        """
        Video akışını durdurur ve kaynakları serbest bırakır.
        """
        if self.cap is not None:
            self.cap.release()
        self.is_running = False
        logger.info("Video akışı durduruldu.")  # DEĞİŞTİ
