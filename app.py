import streamlit as st
import cv2
import tempfile
import pandas as pd
import json
from video_stream_manager import VideoStreamManager
from person_detect_and_tracking_engine import PersonTrackingEngine
from density_map_generator import DensityMapGenerator
from entry_exit_counter import EntryExitCounter
from report_generator import ReportGenerator
from data_manager import DataManager

st.set_page_config(layout="wide", page_title="Gerçek Zamanlı Alan Analizi")

st.title("Gerçek Zamanlı Alan Analizi ve Yoğunluk Takibi")
st.write("""
Bu uygulama, yüklenen bir videodaki insan akışını ve yoğunluğunu analiz eder. 
Analiz sonuçlarını canlı olarak takip edebilir, geçmiş verileri görüntüleyebilir ve detaylı raporlar alabilirsiniz.
""")

# --- Veritabanı Yöneticisini Başlatma ---
db_manager = DataManager()

# --- AYARLAR BÖLÜMÜ (KENAR ÇUBUĞU) ---
st.sidebar.header("Uygulama Durumu ve Ayarlar")

# YENİ: Veritabanı bağlantı durumunu arayüzde göster
if db_manager.conn:
    st.sidebar.success("Veritabanı bağlantısı aktif.")
else:
    st.sidebar.error("Veritabanı bağlantısı kurulamadı.")

uploaded_file = st.sidebar.file_uploader("Analiz için bir video dosyası seçin", type=['mp4', 'avi', 'mov'])

st.sidebar.subheader("Sayaç Ayarları")
line_position_percentage = st.sidebar.slider(
    "Giriş/Çıkış Çizgisi Konumu (Y-ekseni %)",
    min_value=0, max_value=100, value=50,
    help="Çizginin videonun dikey eksenindeki konumunu yüzde olarak ayarlayın."
)

st.sidebar.subheader("Yoğunluk Haritası Ayarları")
blur_kernel_size = st.sidebar.slider(
    "Bulanıklık Değeri (Kernel Boyutu)",
    min_value=1, max_value=101, value=61, step=2,
    help="Isının ne kadar geniş bir alana yayılacağını belirler. Yüksek değerler daha yumuşak geçişler sağlar."
)
clipping_percentile = st.sidebar.slider(
    "Kontrast Yüzdesi (%)",
    min_value=90, max_value=100, value=98,
    help="Haritanın kontrastını ayarlar. Düşük değerler daha fazla alanı 'sıcak' (kırmızı) gösterir."
)

# --- Geçmiş Analizler Bölümü ---
st.header("Geçmiş Analiz Oturumları")
try:
    all_sessions = db_manager.get_all_sessions()
    if all_sessions:
        df_sessions = pd.DataFrame(all_sessions, columns=['Oturum ID', 'Başlangıç Zamanı', 'Video Adı', 'Toplam Giriş',
                                                          'Toplam Çıkış'])
        st.dataframe(df_sessions, use_container_width=True)
    else:
        st.info("Henüz kaydedilmiş bir analiz oturumu bulunmuyor.")
except Exception as e:
    st.error(f"Geçmiş analizler yüklenirken bir hata oluştu: {e}")

# --- Analiz Butonu ve İşlemleri ---
if uploaded_file is not None:
    if st.sidebar.button('Analizi Başlat', type="primary"):

        session_id = db_manager.create_new_session(video_name=uploaded_file.name)
        if session_id is None:
            st.error("Veritabanı oturumu oluşturulamadı! Lütfen konsol loglarını kontrol edin.")
            st.stop()

        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        video_source = tfile.name

        stream_manager = VideoStreamManager(source=video_source)
        stream_manager.start_stream()

        tracking_engine = PersonTrackingEngine()
        ret, first_frame = stream_manager.get_frame()

        if not ret:
            st.error("Video dosyasından ilk kare okunamadı. Dosya bozuk olabilir.")
            st.stop()

        line_y_pixel = int(first_frame.shape[0] * (line_position_percentage / 100))
        density_generator = DensityMapGenerator(frame_shape=first_frame.shape, blur_kernel_size=blur_kernel_size,
                                                clipping_percentile=clipping_percentile)
        counter = EntryExitCounter(line_y_position=line_y_pixel)

        stream_manager.stop_stream()
        stream_manager.start_stream()

        stframe = st.empty()
        st.sidebar.success("Analiz başladı. Sonuçlar aşağıda gösterilmektedir.")
        progress_bar = st.sidebar.progress(0, text="Video işleniyor...")
        total_frames = int(stream_manager.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_count = 0
        while ret:
            ret, frame = stream_manager.get_frame()
            if not ret:
                break

            frame_count += 1
            annotated_frame, person_count, tracked_objects = tracking_engine.process_frame(frame.copy())
            points = [obj['center'] for obj in tracked_objects if 'center' in obj]
            density_generator.add_points(points)

            new_events = counter.update(tracked_objects)
            for event in new_events:
                db_manager.log_event(session_id, event)

            line_y = counter.line_y
            cv2.line(annotated_frame, (0, line_y), (frame.shape[1], line_y), (0, 255, 255), 2)
            cv2.putText(annotated_frame, f"Giris: {counter.entries}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                        (0, 255, 0), 3)
            cv2.putText(annotated_frame, f"Cikis: {counter.exits}", (50, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                        (0, 0, 255), 3)

            # DÜZELTME: Deprecation uyarısını gidermek için 'use_container_width' kullanıldı.
            stframe.image(annotated_frame, channels="BGR", use_container_width=True)

            if total_frames > 0:
                progress_bar.progress(frame_count / total_frames,
                                      text=f"Video işleniyor... ({frame_count}/{total_frames})")

        progress_bar.success("Analiz tamamlandı!")
        stream_manager.stop_stream()

        final_heatmap_image = density_generator.generate_heatmap_image()
        final_result_image = cv2.addWeighted(first_frame, 0.2, final_heatmap_image, 0.8, 0)

        with st.spinner('Rapor dosyaları oluşturuluyor...'):
            report_gen = ReportGenerator()
            success = report_gen.generate_summary_report(
                total_entries=counter.entries, total_exits=counter.exits,
                entry_logs=counter.entry_logs, exit_logs=counter.exit_logs,
                heatmap_image=final_result_image
            )
            if success:
                st.sidebar.success("Raporlar 'reports' klasörüne kaydedildi!")
            else:
                st.sidebar.error("Rapor oluşturulurken bir hata oluştu.")

        st.header("Analiz Sonuçları")
        tab1, tab2, tab3 = st.tabs(["📊 Rapor", "📜 Loglar", "🔥 Isı Haritası"])

        with tab1:
            st.subheader("Oturum Özeti")
            col1, col2 = st.columns(2)
            col1.metric("Toplam Giriş Yapan Kişi Sayısı", counter.entries)
            col2.metric("Toplam Çıkış Yapan Kişi Sayısı", counter.exits)

            st.divider()

            # YENİ: Raporları arayüzden indirme bölümü
            st.subheader("Raporları İndir")

            # JSON verisini hazırla ve indirme butonu oluştur
            json_data = {
                "session_id": session_id,
                "summary": {"total_entries": counter.entries, "total_exits": counter.exits},
                "logs": {"entries": counter.entry_logs, "exits": counter.exit_logs}
            }
            json_string = json.dumps(json_data, indent=4, ensure_ascii=False)
            st.download_button(
                label="📥 JSON Raporu İndir",
                data=json_string,
                file_name=f"report_{session_id}.json",
                mime="application/json"
            )

            # CSV verisini hazırla ve indirme butonu oluştur
            all_logs_df = pd.concat([
                pd.DataFrame(counter.entry_logs, columns=["Log"]).assign(Tip="Giriş"),
                pd.DataFrame(counter.exit_logs, columns=["Log"]).assign(Tip="Çıkış")
            ])
            csv_string = all_logs_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 CSV Raporu İndir",
                data=csv_string,
                file_name=f"report_logs_{session_id}.csv",
                mime="text/csv"
            )

            # Isı haritası görüntüsünü hazırla ve indirme butonu oluştur
            _, buffer = cv2.imencode('.png', final_result_image)
            image_bytes = buffer.tobytes()
            st.download_button(
                label="📥 Isı Haritası İndir (PNG)",
                data=image_bytes,
                file_name=f"heatmap_{session_id}.png",
                mime="image/png"
            )

        with tab2:
            st.subheader("Olay Kayıtları")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Giriş Logları**")
                st.dataframe(pd.DataFrame(counter.entry_logs, columns=["Giriş Zamanı ve ID"]), use_container_width=True)
            with col2:
                st.write("**Çıkış Logları**")
                st.dataframe(pd.DataFrame(counter.exit_logs, columns=["Çıkış Zamanı ve ID"]), use_container_width=True)

        with tab3:
            st.subheader("Genel Yoğunluk Haritası")
            st.image(final_result_image, channels="BGR",
                     caption="Video boyunca en yoğun bölgeleri gösteren ısı haritası.")

