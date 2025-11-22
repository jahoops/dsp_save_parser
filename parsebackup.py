from dsp_save_parser.generated import GameSave
import os
from io import BytesIO

class DebugStream(BytesIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_read = 0

    def read(self, n=-1):
        data = super().read(n)
        self.total_read += len(data)
        if self.total_read % 1024 * 1024 < len(data):  # every ~1MB
            print(f"Read so far: {self.total_read / 1024 / 1024:.2f} MB")
        return data

save_path = r'C:\Users\J\Documents\Dyson Sphere Program\Save\backups\last_exit.dsv'
save_path = os.path.expanduser(save_path)

with open(save_path, 'rb') as f:
    print("File opened... parsing now")
    save_bytes = f.read()
    stream = DebugStream(save_bytes)
    data = GameSave.parse(stream)
    print("parsed!")

print("🎉 Parsed save file successfully!")
print("Header:", data.header)
print("Build Game Version:", data.header.build_game_version)
print("Save Tick:", data.header.save_tick)
