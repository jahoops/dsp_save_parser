import dsp_save_parser as s

SOURCE_SAVE = r"C:\Users\J\Documents\Dyson Sphere Program\Save\save this one.dsv"
OUTPUT_SAVE = r"C:\Users\J\Documents\Dyson Sphere Program\Save\load this one.dsv"

with open(SOURCE_SAVE, "rb") as f:
    data = s.GameSave.parse(f)

updated_slots = 0
for slot, cell in enumerate(data.game_data.main_player.package.grids):
    if slot == 0:
        cell.item_id = 2213 # 2213	Geothermal power station
        cell.stack_size = 50
        cell.count = 50
    if slot == 1:
        cell.item_id = 2212 # 2212	Satellite substation
        cell.stack_size = 50
        cell.count = 50 
    if cell.item_id not in (6006, 6005, 6004, 6003, 6002, 6001):  # Copper Ore, Coal, Stone, Iron Ore
        continue
    if cell.item_id == 6006:
        cell.item_id = 1608 # 1608	Antimatter capsule
        cell.stack_size = 100
        cell.count = 100
    elif cell.item_id == 6005:
        cell.item_id = 1611 # 1611	Gravity missile set
        cell.stack_size = 100
        cell.count = 100
    elif cell.item_id == 6004:
        cell.item_id = 5204 # 5204	Negentropy singularity
        cell.stack_size = 50
        cell.count = 50
    elif cell.item_id == 6003:
        cell.item_id = 1804 # 1804	Strange annihilation fuel rod
        cell.stack_size = 50
        cell.count = 50
    elif cell.item_id == 6002:
        cell.item_id = 1122 # 1122	Antimatter
        cell.stack_size = 20
        cell.count = 20
    elif cell.item_id == 6001:
        cell.item_id = 1803 # 1803	Antimatter fuel rod
        cell.stack_size = 30
        cell.count = 30
with open(OUTPUT_SAVE, "wb") as f:
    data.save(f)
    
print(f"Updated slot(s). Saved to {OUTPUT_SAVE}")