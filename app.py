import streamlit as st
import cv2
import tempfile
import pandas as pd

# Mevcut modüllerimizi import ediyoruz
from video_stream_manager import VideoStreamManager
from person_detect_and_tracking_engine import PersonTrackingEngine
from density_map_generator import DensityMapGenerator
from entry_exit_counter import EntryExitCounter

st.set_page_config(layout="wide", page_title="Gerçek Zamanlı Alan Analizi")

st.title("Gerçek Zamanlı Alan Kullanım ve Yoğunluk Takibi")
st.write("Analiz etmek istediğiniz videoyu yükleyin ve 'Analizi Başlat' butonuna tıklayın.")

# --- SIDEBAR: KONTROL PANELİ ---
with st.sidebar:
    st.header("Kontroller")
    uploaded_file = st.file_uploader("Video Dosyası Seçin", type=["mp4", "avi", "mov"])

    # Giriş/Çıkış çizgisi ve harita ayarları için sliderlar
    line_y_position = st.slider("Giriş/Çıkış Çizgisi Konumu (Y-Ekseni)", 0, 1080, 350)
    heatmap_blur = st.slider("Isı Haritası Bulanıklık Değeri", 1, 101, 61, step=2)
    heatmap_percentile = st.slider("Isı Haritası Kontrast Yüzdesi (%)", 90, 100, 98)

    start_button = st.button("Analizi Başlat")

# --- ANA EKRAN ---
if uploaded_file is not None and start_button:
    # Yüklenen videoyu geçici bir dosyaya kaydet
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    video_source = tfile.name

    # Analiz motorlarını başlat
    stream_manager = VideoStreamManager(video_source)
    tracking_engine = PersonTrackingEngine()

    stream_manager.start_stream()
    ret, first_frame = stream_manager.get_frame()

    if not ret:
        st.error("Video okunamadı. Lütfen farklı bir dosya deneyin.")
    else:
        # Sınıfları sidebar'dan gelen değerlerle başlat
        density_generator = DensityMapGenerator(first_frame.shape, heatmap_blur, heatmap_percentile)
        counter = EntryExitCounter(line_y_position)
        stream_manager.stop_stream()  # Başa al
        stream_manager.start_stream()

        # Video akışı için bir yer tutucu oluştur
        stframe = st.empty()
        progress_bar = st.progress(0)

        # Toplam kare sayısını al (OpenCV 7+)
        total_frames = int(stream_manager.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0

        while True:
            ret, frame = stream_manager.get_frame()
            if not ret:
                break

            frame_count += 1
            annotated_frame, person_count, tracked_objects = tracking_engine.process_frame(frame)

            points = [obj['center'] for obj in tracked_objects if 'center' in obj]
            density_generator.add_points(points)
            counter.update(tracked_objects)

            # Çizgi ve sayaçları ekle
            cv2.line(annotated_frame, (0, line_y_position), (frame.shape[1], line_y_position), (0, 255, 255), 2)
            cv2.putText(annotated_frame, f"Giris: {counter.entries}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                        (0, 255, 0), 3)
            cv2.putText(annotated_frame, f"Cikis: {counter.exits}", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                        (0, 0, 255), 3)

            # Streamlit için kareyi BGR'dan RGB'ye çevir
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            stframe.image(frame_rgb, channels="RGB")

            # İlerleme çubuğunu güncelle
            if total_frames > 0:
                progress_bar.progress(frame_count / total_frames)

        progress_bar.progress(1.0)
        st.success("Video analizi başarıyla tamamlandı!")
        stream_manager.stop_stream()

        # --- SONUÇ SEKMELERİ ---
        st.header("Analiz Sonuçları")
        tab1, tab2, tab3 = st.tabs(["📊 Rapor", "📜 Loglar", "🔥 Isı Haritası"])

        with tab1:
            st.subheader("Genel Rapor")
            col1, col2 = st.columns(2)
            col1.metric("Toplam Giriş Yapan Kişi Sayısı", counter.entries)
            col2.metric("Toplam Çıkış Yapan Kişi Sayısı", counter.exits)

        with tab2:
            st.subheader("Giriş ve Çıkış Kayıtları")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Giriş Logları")
                if counter.entry_logs:
                    df_entry = pd.DataFrame(counter.entry_logs)
                    st.dataframe(df_entry)
                else:
                    st.info("Giriş yapan kimse tespit edilmedi.")
            with col2:
                st.write("Çıkış Logları")
                if counter.exit_logs:
                    df_exit = pd.DataFrame(counter.exit_logs)
                    st.dataframe(df_exit)
                else:
                    st.info("Çıkış yapan kimse tespit edilmedi.")

        with tab3:
            st.subheader("Genel Yoğunluk Haritası")
            with st.spinner('Isı haritası oluşturuluyor...'):
                final_heatmap = density_generator.generate_heatmap_image()
                final_result = cv2.addWeighted(first_frame, 0.2, final_heatmap, 0.8, 0)
                final_result_rgb = cv2.cvtColor(final_result, cv2.COLOR_BGR2RGB)
                st.image(final_result_rgb, caption="En yoğun bölgeler kırmızı renkle gösterilmiştir.")
