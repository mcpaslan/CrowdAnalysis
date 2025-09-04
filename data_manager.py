import sqlite3
from datetime import datetime
import os
from logger_config import logger


class DataManager:
    """
    SQLite veritabanı ile ilgili tüm işlemleri yöneten merkezi sınıf.
    Bağlantı kurma, tablo oluşturma, veri ekleme ve çekme işlemlerini yapar.
    """

    def __init__(self, db_folder='database', db_name='analysis_history.db'):
        """
        Veritabanı bağlantısını kurar ve gerekirse tabloları oluşturur.

        Args:
            db_folder (str): Veritabanı dosyasının bulunacağı klasör.
            db_name (str): Veritabanı dosyasının adı.
        """
        # Veritabanı klasörünün var olduğundan emin ol
        if not os.path.exists(db_folder):
            os.makedirs(db_folder)

        db_path = os.path.join(db_folder, db_name)

        try:
            # Veritabanına bağlan (eğer dosya yoksa oluşturulur)
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            print(f"Veritabanı bağlantısı başarılı: {db_path}")
            self._setup_tables()
        except sqlite3.Error as e:
            print(f"Veritabanı hatası: {e}")
            self.conn = None

    def _setup_tables(self):
        """
        Gerekli tabloları veritabanında oluşturur (eğer mevcut değillerse).
        - sessions: Her bir video analizini tekil bir oturum olarak kaydeder.
        - events: Her bir giriş/çıkış olayını kaydeder ve bir oturuma bağlar.
        """
        if not self.conn:
            return

        try:
            # Analiz oturumlarını tutan tablo
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS sessions
                                (
                                    session_id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    start_time
                                    TEXT
                                    NOT
                                    NULL,
                                    video_name
                                    TEXT,
                                    total_entries
                                    INTEGER
                                    DEFAULT
                                    0,
                                    total_exits
                                    INTEGER
                                    DEFAULT
                                    0
                                )
                                ''')

            # Her bir giriş/çıkış olayını tutan tablo
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS events
                                (
                                    event_id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    session_id
                                    INTEGER
                                    NOT
                                    NULL,
                                    timestamp
                                    TEXT
                                    NOT
                                    NULL,
                                    event_type
                                    TEXT
                                    NOT
                                    NULL,
                                    FOREIGN
                                    KEY
                                (
                                    session_id
                                ) REFERENCES sessions
                                (
                                    session_id
                                )
                                    )
                                ''')
            self.conn.commit()
            print("Tablolar başarıyla kuruldu veya zaten mevcut.")
        except sqlite3.Error as e:
            print(f"Tablo oluşturma hatası: {e}")

    def create_new_session(self, video_name='N/A'):
        """
        Yeni bir analiz oturumu başlatır ve veritabanına kaydeder.

        Returns:
            int: Oluşturulan yeni oturumun ID'si.
        """
        if not self.conn:
            return None

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute(
                "INSERT INTO sessions (start_time, video_name) VALUES (?, ?)",
                (start_time, video_name)
            )
            self.conn.commit()
            session_id = self.cursor.lastrowid
            print(f"Yeni oturum oluşturuldu: ID={session_id}")
            return session_id
        except sqlite3.Error as e:
            print(f"Oturum oluşturma hatası: {e}")
            return None

    def log_event(self, session_id, event_type):
        """
        Bir giriş veya çıkış olayını veritabanına kaydeder.
        """
        if not self.conn or session_id is None:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute(
                "INSERT INTO events (session_id, timestamp, event_type) VALUES (?, ?, ?)",
                (session_id, timestamp, event_type)
            )
            # İlgili oturumun toplam giriş/çıkış sayısını da güncelle
            if event_type == 'Giriş':
                self.cursor.execute("UPDATE sessions SET total_entries = total_entries + 1 WHERE session_id = ?",
                                    (session_id,))
            elif event_type == 'Çıkış':
                self.cursor.execute("UPDATE sessions SET total_exits = total_exits + 1 WHERE session_id = ?",
                                    (session_id,))

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Olay kaydetme hatası: {e}")

    def get_all_sessions(self):
        """
        Tüm geçmiş analiz oturumlarının özetini döndürür.
        """
        if not self.conn:
            return []
        try:
            self.cursor.execute(
                "SELECT session_id, start_time, video_name, total_entries, total_exits FROM sessions ORDER BY start_time DESC")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Oturumları getirme hatası: {e}")
            return []


    def get_events_by_session(self, session_id):
        """
        Belirli bir oturum ID'sine ait tüm giriş/çıkış olaylarını zaman sırasıyla döndürür.
        """
        if not self.conn or session_id is None:
            return []
        try:
            self.cursor.execute(
                "SELECT timestamp, event_type FROM events WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.exception(f"Oturum ID {session_id} için olaylar getirilirken hata oluştu.")
            return []

    def close_connection(self):
        """
        Veritabanı bağlantısını güvenli bir şekilde kapatır.
        """
        if self.conn:
            self.conn.close()
            logger.info("Veritabanı bağlantısı kapatıldı.")
