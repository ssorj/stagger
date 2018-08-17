import json as _json
import os as _os
import threading as _threading
import traceback as _traceback

class Data:
    def __init__(self, file_path):
        self.file_path = file_path

        self.tags = dict()

        self.lock = _threading.Lock()
        self.modified = _threading.Event()

    def load(self):
        if not _os.path.exists(self.file_path):
            return
        
        with open(self.file_path, "r") as f:
            data = _json.load(f)
            self.tags = data.get("tags")
        
            print(f"Loaded data from disk: {data}")

    def save(self):
        with self.lock:
            temp = f"{self.file_path}.temp"
            data = {
                "tags": self.tags,
            }

            print(f"Saving data to disk: {data}")

            with open(temp, "w") as f:
                _json.dump(data, f, indent="  ")

            _os.rename(temp, self.file_path)

class SaveThread(_threading.Thread):
    def __init__(self, data):
        super().__init__()

        self.data = data
        self.daemon = True

    def run(self):
        while self.data.modified.wait():
            try:
                self.data.save()
            except KeyboardInterrupt:
                raise
            except Exception:
                _traceback.print_exc()
            finally:
                self.data.modified.clear()
