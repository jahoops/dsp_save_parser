import json
import dsp_save_parser as s

SAVE_PATH = r"C:\Users\J\Documents\Dyson Sphere Program\Save\save this one.dsv"

with open(SAVE_PATH, "rb") as f:
    data = s.GameSave.parse(f)

inventory = []
for slot, cell in enumerate(data.game_data.main_player.package.grids):
    if cell.item_id:
        inventory.append({"slot": slot, "item_id": cell.item_id, "count": cell.count})

print(json.dumps(inventory, indent=2))