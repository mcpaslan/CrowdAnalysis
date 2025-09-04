import os
import json
from datetime import datetime
import pandas as pd
import cv2
import numpy as np


class ReportGenerator:
    """
    Analiz sonuçlarını (JSON, CSV, PNG) dosyalara kaydeden sınıf.
    """

    def __init__(self, report_folder='reports'):
        """
        Raporların kaydedileceği klasörü belirler ve mevcut değilse oluşturur.
        """
        self.report_folder = report_folder
        if not os.path.exists(self.report_folder):
            os.makedirs(self.report_folder)
            print(f"'{self.report_folder}' klasörü oluşturuldu.")

    def generate_summary_report(self, total_entries, total_exits, entry_logs, exit_logs, heatmap_image):
        """
        Tüm analiz verilerini alarak özet rapor dosyaları oluşturur.

        Args:
            total_entries (int): Toplam giriş sayısı.
            total_exits (int): Toplam çıkış sayısı.
            entry_logs (list): Giriş olaylarının log listesi.
            exit_logs (list): Çıkış olaylarının log listesi.
            heatmap_image (np.ndarray): Sonuç yoğunluk haritası görüntüsü.

        Returns:
            bool: Rapor oluşturma başarılı ise True, değilse False.
        """
        try:
            # Rapor dosyaları için benzersiz bir zaman damgası oluştur
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            base_filename = f"report_{timestamp}"

            # 1. JSON Raporu Oluşturma
            json_data = {
                "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "total_entries": total_entries,
                    "total_exits": total_exits
                },
                "logs": {
                    "entries": entry_logs,
                    "exits": exit_logs
                }
            }
            json_filepath = os.path.join(self.report_folder, f"{base_filename}.json")
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            # 2. CSV Raporu Oluşturma
            # Tüm logları tek bir DataFrame'de birleştirelim
            all_logs = []
            for log in entry_logs:
                # Örnek log: "2025-09-04 18:30:00: ID 1 giriş yaptı."
                parts = log.split(': ')
                time_str = parts[0]
                details = parts[1]
                all_logs.append({'Zaman Damgası': time_str, 'Olay': details, 'Tip': 'Giriş'})

            for log in exit_logs:
                parts = log.split(': ')
                time_str = parts[0]
                details = parts[1]
                all_logs.append({'Zaman Damgası': time_str, 'Olay': details, 'Tip': 'Çıkış'})

            if all_logs:
                df = pd.DataFrame(all_logs)
                csv_filepath = os.path.join(self.report_folder, f"{base_filename}.csv")
                df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')

            # 3. Yoğunluk Haritası Görüntüsünü Kaydetme
            image_filepath = os.path.join(self.report_folder, f"heatmap_{timestamp}.png")
            cv2.imwrite(image_filepath, heatmap_image)

            print(f"Raporlar başarıyla oluşturuldu: {self.report_folder}")
            return True

        except Exception as e:
            print(f"Rapor oluşturma sırasında bir hata oluştu: {e}")
            return False

