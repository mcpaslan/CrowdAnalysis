# density_map_generator.py (Güncellenmiş Hali)

import numpy as np
import cv2


class DensityMapGenerator:
    def __init__(self, frame_shape, blur_kernel_size=51, clipping_percentile=99):
        """
        Sınıfın kurucu metodu. Artık ayarlanabilir parametreler alıyor.

        Args:
            frame_shape (tuple): Video karesinin şekli.
            blur_kernel_size (int): Isıyı yaymak için kullanılacak blur kernel boyutu. Tek sayı olmalı.
            clipping_percentile (int): Kontrast ayarı için kullanılacak yüzdelik dilim.
        """
        self.frame_height = frame_shape[0]
        self.frame_width = frame_shape[1]
        self.blur_kernel_size = (blur_kernel_size, blur_kernel_size)
        self.clipping_percentile = clipping_percentile

        self.heatmap_matrix = np.zeros((self.frame_height, self.frame_width), dtype=np.float32)

    def add_points(self, points, intensity=15):  # Intensity'yi varsayılan olarak biraz daha yüksek tutalım
        for x, y in points:
            if 0 <= x < self.frame_width and 0 <= y < self.frame_height:
                self.heatmap_matrix[y, x] += intensity

    def generate_heatmap_image(self):
        """
        Daha akıllı normalizasyon ile görsel bir ısı haritası oluşturur.
        """
        # Isıyı daha geniş ve belirgin alanlara yay
        blurred_map = cv2.GaussianBlur(self.heatmap_matrix, self.blur_kernel_size, 0)

        # Eğer hiç ısı birikmediyse, boş bir harita döndür
        if np.max(blurred_map) == 0:
            return np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)

        # --- KONTRAST İÇİN EN ÖNEMLİ ADIM: AYKIRI DEĞERLERİ KIRPMA ---
        # Haritadaki tüm piksellerin %99'unun altında kaldığı değeri buluyoruz.
        # Bu, birkaç aşırı parlak noktanın tüm renk skalasını bozmasını engeller.
        max_val_clipped = np.percentile(blurred_map[blurred_map > 0], self.clipping_percentile)

        # Eğer kırpma sonrası max değer 0 ise (çok nadir bir durum), yine boş harita dön.
        if max_val_clipped == 0:
            return np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)

        # Matristeki değerleri bu yeni maksimum değere göre kırp (clip)
        clipped_map = np.clip(blurred_map, 0, max_val_clipped)

        # Kırpılmış haritayı 0-255 arasına normalize et
        norm_map = cv2.normalize(clipped_map, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Renklendir
        heatmap_color_image = cv2.applyColorMap(norm_map, cv2.COLORMAP_JET)

        return heatmap_color_imageanerev