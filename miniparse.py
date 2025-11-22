from construct import Struct, Int32ul, PascalString, Bytes
from construct import GreedyBytes
import os
from io import BytesIO

MiniGameSave = Struct(
    "file_length" / Int32ul,
    "major_game_version" / Int32ul,
    "minor_game_version" / Int32ul,
    "release_game_version" / Int32ul,
    "build_game_version" / Int32ul,
    "save_tick" / Int32ul,
    "header_screenshot_size" / Int32ul,
    "screenshot_data" / Bytes(lambda this: this.header_screenshot_size),
    # You could stop here, or...
    # "objectConnCount" / Int32ul  <-- (if you can find the offset!)
)

save_path = r'C:\Users\J\Documents\Dyson Sphere Program\Save\backups\notasold.dsv'
save_path = os.path.expanduser(save_path)
with open(save_path, 'rb') as f:
    print("Reading file...")
    save_bytes = f.read()
    result = MiniGameSave.parse(save_bytes)  # <-- THIS is the correct form

print("Parsed header!")
print(result)
