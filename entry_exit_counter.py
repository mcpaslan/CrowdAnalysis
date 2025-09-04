import collections
from datetime import datetime


class EntryExitCounter:
    def __init__(self, line_y_position):
        self.line_y = line_y_position
        self.entries = 0
        self.exits = 0
        self.track_history = collections.defaultdict(lambda: collections.deque(maxlen=2))
        self.counted_ids = set()

        # --- YENİ EKLENEN KISIM: LOG LİSTELERİ ---
        self.entry_logs = []
        self.exit_logs = []

    def update(self, tracked_objects):
        current_ids = {obj['id'] for obj in tracked_objects}

        for obj in tracked_objects:
            obj_id = obj['id']
            center_y = obj['center'][1]
            self.track_history[obj_id].append(center_y)

            if len(self.track_history[obj_id]) == 2 and obj_id not in self.counted_ids:
                prev_y = self.track_history[obj_id][0]

                # Zaman damgasını al
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

                if prev_y < self.line_y and center_y >= self.line_y:
                    self.entries += 1
                    self.counted_ids.add(obj_id)
                    # --- YENİ: GİRİŞ LOGU EKLE ---
                    self.entry_logs.append({"Zaman": timestamp, "Olay": f"ID-{obj_id} giriş yaptı"})

                elif prev_y > self.line_y and center_y <= self.line_y:
                    self.exits += 1
                    self.counted_ids.add(obj_id)
                    # --- YENİ: ÇIKIŞ LOGU EKLE ---
                    self.exit_logs.append({"Zaman": timestamp, "Olay": f"ID-{obj_id} çıkış yaptı"})

        lost_ids = set(self.track_history.keys()) - current_ids
        for lost_id in lost_ids:
            self.counted_ids.discard(lost_id)
            del self.track_history[lost_id]
