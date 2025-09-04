import cv2


class VideoStreamManager:
    """
    Video kaynağından (dosya veya kamera) görüntü akışını yöneten sınıf.
    """

    def __init__(self, source):
        """
        Sınıfın kurucu metodu.

        Args:
            source (str or int): Video dosyasının yolu (örn: "video/magaza.mp4")
                                 veya kamera indeksi (örn: 0).
        """
        self.source = source
        self.cap = None  # VideoCapture nesnesini başlangıçta None olarak ayarlıyoruz.
        self.is_running = False

    def start_stream(self):
        """
        Video akışını başlatır ve bağlantıyı kontrol eder.
        """
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            # Eğer video kaynağı açılamazsa hata ver.
            print(f"Hata: Video kaynağı açılamadı -> {self.source}")
            self.is_running = False
            return False

        self.is_running = True
        print("Video akışı başarıyla başlatıldı.")
        return True

    def get_frame(self):
        """
        Akıştan bir sonraki kareyi (frame) okur.

        Returns:
            tuple: (ret, frame)
                   ret (bool): Kare başarıyla okunduysa True.
                   frame (numpy.ndarray): Okunan görüntü karesi.
        """
        if not self.is_running:
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
        print("Video akışı durduruldu.")