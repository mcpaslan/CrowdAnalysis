import collections
from datetime import datetime


class EntryExitCounter:
    """
    Belirlenen bir sanal çizgiyi geçen nesnelerin yönüne göre
    giriş ve çıkışlarını sayan ve yeni olayları bildiren sınıf.
    """

    def __init__(self, line_y_position):
        self.line_y = line_y_position
        self.entries = 0
        self.exits = 0

        # Streamlit arayüzünde anlık logları göstermek için bu listeleri koruyoruz.
        self.entry_logs = []
        self.exit_logs = []

        self.track_history = collections.defaultdict(lambda: collections.deque(maxlen=2))
        self.counted_ids = set()

    def update(self, tracked_objects):
        """
        Takip edilen nesneleri günceller, çizgiyi geçenleri sayar ve
        yeni gerçekleşen olayların bir listesini döndürür.

        Args:
            tracked_objects (list of dicts): Her nesnenin 'id' ve 'center' bilgilerini içeren liste.

        Returns:
            list: O anki karede yeni gerçekleşen olayların listesi (örn: ['Giriş', 'Çıkış']).
        """
        # YENİ: Bu fonksiyonda gerçekleşen yeni olayları tutmak için boş bir liste
        new_events_this_frame = []

        current_ids = {obj['id'] for obj in tracked_objects}

        for obj in tracked_objects:
            obj_id = obj['id']
            center_y = obj['center'][1]

            self.track_history[obj_id].append(center_y)

            if len(self.track_history[obj_id]) == 2 and obj_id not in self.counted_ids:
                prev_y = self.track_history[obj_id][0]

                # YÖN KONTROLÜ
                if prev_y < self.line_y and center_y >= self.line_y:
                    # GİRİŞ olayı
                    self.entries += 1
                    self.counted_ids.add(obj_id)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.entry_logs.append(f"{timestamp}: ID {obj_id} giriş yaptı.")

                    # YENİ: Yeni olayı listeye ekle
                    new_events_this_frame.append('Giriş')

                elif prev_y > self.line_y and center_y <= self.line_y:
                    # ÇIKIŞ olayı
                    self.exits += 1
                    self.counted_ids.add(obj_id)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.exit_logs.append(f"{timestamp}: ID {obj_id} çıkış yaptı.")

                    # YENİ: Yeni olayı listeye ekle
                    new_events_this_frame.append('Çıkış')

        lost_ids = set(self.track_history.keys()) - current_ids
        for lost_id in lost_ids:
            self.counted_ids.discard(lost_id)
            del self.track_history[lost_id]

        # DEĞİŞTİ: Yeni olayların listesini döndür
        return new_events_this_frame

