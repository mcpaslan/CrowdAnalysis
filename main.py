# main.py (Tüm Özellikleri İçeren Tam Kod)

import cv2
from video_stream_manager import VideoStreamManager
from person_detect_and_tracking_engine import PersonTrackingEngine
from density_map_generator import DensityMapGenerator
from entry_exit_counter import EntryExitCounter

def main():
    # --- PROJE AYARLARI: Buradaki değerleri kendi videonuza göre değiştirin ---

    # 1. Video Kaynağı
    # Web kamerası için: 0, 1, ...
    # Video dosyası için: "video/dosya_adi.mp4"
    video_source = "video/giris_cikis.mp4"

    # 2. Giriş/Çıkış Sayacı Ayarları
    # Videonuzdaki sayım çizgisinin Y-eksenindeki piksel konumu.
    # Bu çizgiyi videonuzun en uygun yerine (örn: kapı eşiği) yerleştirin.
    GIRIS_CIKIS_CIZGISI_Y = 450

    # 3. Yoğunluk Haritası Ayarları
    # Isının ne kadar geniş bir alana yayılacağını belirler. Daha büyük değerler daha yayvan alanlar oluşturur. (Tek sayı olmalı)
    HEATMAP_BLUR_KERNEL = 61
    # Haritanın kontrastını ayarlar. Düşük değerler daha fazla alanı 'sıcak' gösterir. (%90-99 arası idealdir)
    HEATMAP_CLIPPING_PERCENTILE = 98

    # --- AYARLARIN SONU ---


    # Gerekli modüllerden nesneleri oluşturma
    stream_manager = VideoStreamManager(source=video_source)
    if not stream_manager.start_stream():
        return

    # Hız için 'yolov8n.pt' veya 'yolov8s.pt' modelini kullanmanızı tavsiye ederim.
    # Bu ayarı person_detect_and_tracking_engine.py dosyasından yapabilirsiniz.
    tracking_engine = PersonTrackingEngine()

    ret, first_frame = stream_manager.get_frame()
    if not ret:
        print("Video başlatılamadı veya ilk kare okunamadı.")
        stream_manager.stop_stream()
        return

    # Sınıfları ilgili parametrelerle başlat
    density_generator = DensityMapGenerator(
        frame_shape=first_frame.shape,
        blur_kernel_size=HEATMAP_BLUR_KERNEL,
        clipping_percentile=HEATMAP_CLIPPING_PERCENTILE
    )
    counter = EntryExitCounter(line_y_position=GIRIS_CIKIS_CIZGISI_Y)

    # Analize başlamak için video akışını başa al
    stream_manager.stop_stream()
    stream_manager.start_stream()

    print("Video işleniyor... (Durdurmak için 'q' tuşuna basın)")

    # Ana video işleme döngüsü
    while True:
        ret, frame = stream_manager.get_frame()
        if not ret:
            print("Video işleme tamamlandı.")
            break

        # 1. Kareyi işle: İnsanları takip et, kutuları ve ID'leri çiz
        annotated_frame, person_count, tracked_objects = tracking_engine.process_frame(frame.copy())

        # 2. Yoğunluk haritası verilerini güncelle
        # 'center' anahtarı olmayan nesneleri filtrele (nadiren de olsa olabilir)
        points = [obj['center'] for obj in tracked_objects if 'center' in obj]
        density_generator.add_points(points)

        # 3. Giriş/Çıkış sayacını güncelle
        counter.update(tracked_objects)

        # 4. Anlık sonuçları ekrana çizdir
        # Sanal sayım çizgisi
        cv2.line(annotated_frame, (0, GIRIS_CIKIS_CIZGISI_Y), (frame.shape[1], GIRIS_CIKIS_CIZGISI_Y), (0, 255, 255), 2)
        # Sayaçlar
        cv2.putText(annotated_frame, f"Giris: {counter.entries}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        cv2.putText(annotated_frame, f"Cikis: {counter.exits}", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        # Anlık işlenmiş görüntüyü göster
        cv2.imshow("Canli Analiz", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("İşlem kullanıcı tarafından durduruldu.")
            break

    # --- Video bittikten sonraki işlemler ---

    print("Nihai yoğunluk haritası oluşturuluyor...")
    final_heatmap_image = density_generator.generate_heatmap_image()

    # Arka planı daha az belirgin, ısı haritasını daha baskın yap
    final_result_image = cv2.addWeighted(first_frame, 0.2, final_heatmap_image, 0.8, 0)

    cv2.putText(final_result_image, "Genel Yogunluk Haritasi (Sonuc)", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow("Genel Yogunluk Haritasi (Sonuc)", final_result_image)
    print("Sonuç haritası 'heatmap_result.png' olarak kaydedildi.")

    print(f"\n--- Analiz Sonucu ---")
    print(f"Toplam Giris Yapan Sayisi: {counter.entries}")
    print(f"Toplam Cikis Yapan Sayisi: {counter.exits}")
    print("--------------------")

    # Sonuç penceresinin kapanmaması için bir tuşa basılmasını bekle
    cv2.waitKey(0)

    # Tüm kaynakları serbest bırak
    stream_manager.stop_stream()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()