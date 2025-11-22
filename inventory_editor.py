import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash, session

import dsp_save_parser as s

APP_SECRET = "dsp-slot-editor"
INVENTORY_JSON = Path("inventory.json")
SOURCE_SAVE = Path(r"C:\Users\J\Documents\Dyson Sphere Program\Save\save this one.dsv")
OUTPUT_SAVE = Path(r"C:\Users\J\Documents\Dyson Sphere Program\Save\load this one.dsv")

app = Flask(__name__)
app.secret_key = APP_SECRET


TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>DSP Inventory Editor</title>
  <style>
    :root {
      font-family: "Segoe UI", Tahoma, sans-serif;
      background: #0b0c10;
      color: #e4e7ec;
    }
    body {
      margin: 2rem auto;
      max-width: 1100px;
      padding: 0 1rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }
    th, td {
      border: 1px solid #1f2933;
      padding: 0.4rem 0.5rem;
      text-align: left;
    }
    th {
      background: #111827;
      position: sticky;
      top: 0;
    }
    select, input[type=number], input[type=text] {
      width: 100%;
      box-sizing: border-box;
      padding: 0.35rem;
      background: #111827;
      color: #e4e7ec;
      border: 1px solid #334155;
      border-radius: 4px;
    }
    select {
      appearance: none;
      background-image: linear-gradient(45deg, transparent 50%, #94a3b8 50%),
                        linear-gradient(135deg, #94a3b8 50%, transparent 50%);
      background-position: calc(100% - 20px) calc(1em + 2px), calc(100% - 15px) calc(1em + 2px);
      background-size: 5px 5px;
      background-repeat: no-repeat;
    }
    select option {
      background: #0b1120;
      color: #e2e8f0;
    }
    select:focus {
      outline: none;
      border-color: #60a5fa;
      box-shadow: 0 0 0 2px rgba(96,165,250,0.3);
    }
    .actions {
      margin-top: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }
    button {
      padding: 0.6rem 1.4rem;
      border: none;
      border-radius: 4px;
      font-size: 1rem;
      font-weight: 600;
      background: #2563eb;
      color: white;
      cursor: pointer;
    }
    button:hover {
      background: #1d4ed8;
    }
    .flash {
      list-style: none;
      padding: 0;
      margin: 1rem 0;
    }
    .flash li {
      background: #16a34a;
      color: white;
      padding: 0.6rem 0.8rem;
      border-radius: 4px;
    }
    .stack-cell {
      text-align: center;
      font-variant-numeric: tabular-nums;
    }
    .item-picker {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }
    .item-search {
      font-size: 0.85rem;
    }
    .item-description {
      font-size: 0.8rem;
      color: #a1aab8;
      min-height: 1.5em;
      white-space: pre-line;
    }
    .status-banner {
      margin-top: 0.75rem;
      padding: 0.6rem 0.8rem;
      border-radius: 4px;
      background: #0f3b24;
      color: #bbf7d0;
      border: 1px solid #22c55e77;
      font-size: 0.95rem;
    }
    .saving-overlay {
      position: fixed;
      inset: 0;
      background: rgba(7, 10, 18, 0.85);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #f8fafc;
      font-size: 1.2rem;
      letter-spacing: 0.02em;
      z-index: 1000;
      backdrop-filter: blur(1px);
    }
    .saving-overlay[hidden] {
      display: none;
    }
  </style>
</head>
<body>
  <h1>DSP Inventory Editor</h1>
  <p>Editing source: <code>{{ source_save }}</code><br />Writing to: <code>{{ output_save }}</code></p>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul class="flash" aria-live="polite">
        {% for msg in messages %}
          <li>{{ msg }}</li>
        {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  {% if last_saved %}
    <div class="status-banner" id="save-status">{{ last_saved }}</div>
  {% endif %}
  <form method="post" id="inventory-form">
    <div class="actions">
      <button type="submit">Save Inventory</button>
      <span>Changing a slot automatically snaps its count to the item's stack size. Adjust counts afterwards if needed.</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Slot</th>
          <th>Item</th>
          <th>Count</th>
          <th>Stack Size</th>
        </tr>
      </thead>
      <tbody>
        {% for slot in slots %}
        <tr>
          <td>{{ slot.slot }}</td>
          <td>
            <div class="item-picker">
              <input type="text" class="item-search" placeholder="Search..." data-select="slot-{{ slot.slot }}-item">
              <select id="slot-{{ slot.slot }}-item" name="slot-{{ slot.slot }}-item" class="item-select" data-slot="{{ slot.slot }}" title="{{ slot.description }}">
              <option value="0" data-description="" title="Empty" {% if not slot.item_id %}selected{% endif %}>-- Empty --</option>
              {% for option in item_options %}
                <option value="{{ option.item_id }}" data-description="{{ option.description|e }}" title="{{ option.description|e }}" {% if option.item_id == slot.item_id %}selected{% endif %}>
                  {{ option.label }}
                </option>
              {% endfor %}
              </select>
              <div class="item-description" id="slot-{{ slot.slot }}-description">{{ slot.description }}</div>
            </div>
          </td>
          <td>
            <input type="number" name="slot-{{ slot.slot }}-count" data-slot="{{ slot.slot }}" min="0" value="{{ slot.count }}" {% if slot.stack_size %}max="{{ slot.stack_size }}"{% endif %}>
          </td>
          <td id="slot-{{ slot.slot }}-stack" class="stack-cell">{% if slot.stack_size %}{{ slot.stack_size }}{% else %}-{% endif %}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <div class="actions">
      <button type="submit">Save Inventory</button>
      <span>Total slots: {{ slots|length }}</span>
    </div>
  </form>
  <div class="saving-overlay" id="saving-overlay" hidden>Saving changes… please wait</div>
  <script>
    const ITEM_DATA = {{ item_data | tojson }};
    function handleItemChange(event) {
      const select = event.target;
      const slot = select.dataset.slot;
      const itemId = select.value;
      const meta = ITEM_DATA[itemId] || {stack_size: 0, description: ""};
      const countInput = document.querySelector(`input[name='slot-${slot}-count']`);
      const stackLabel = document.getElementById(`slot-${slot}-stack`);
      const descTarget = document.getElementById(`slot-${slot}-description`);
      const stackSize = meta.stack_size || 0;
      select.title = meta.description || "";
      if (countInput) {
        countInput.value = stackSize;
        if (stackSize > 0) {
          countInput.max = stackSize;
        } else {
          countInput.removeAttribute('max');
        }
      }
      if (stackLabel) {
        stackLabel.textContent = stackSize ? stackSize : '-';
      }
      if (descTarget) {
        descTarget.textContent = meta.description || '';
      }
    }
    function handleItemSearch(event) {
      const selectId = event.target.dataset.select;
      const select = document.getElementById(selectId);
      if (!select) {
        return;
      }
      const needle = event.target.value.trim().toLowerCase();
      let firstVisible = null;
      select.querySelectorAll('option').forEach(option => {
        if (!needle) {
          option.hidden = false;
          return;
        }
        const haystack = `${option.textContent} ${option.value} ${(option.dataset.description || '')}`.toLowerCase();
        const matches = haystack.includes(needle);
        const keepVisible = matches || option.selected;
        option.hidden = !keepVisible;
        if (keepVisible && !option.hidden && !firstVisible && !option.selected) {
          firstVisible = option;
        }
      });
      if (needle && firstVisible) {
        select.value = firstVisible.value;
        select.dispatchEvent(new Event('change'));
      }
    }

    document.querySelectorAll('.item-select').forEach(select => {
      select.addEventListener('change', handleItemChange);
    });
    document.querySelectorAll('.item-search').forEach(input => {
      input.addEventListener('input', handleItemSearch);
    });
    const form = document.getElementById('inventory-form');
    const overlay = document.getElementById('saving-overlay');
    if (form) {
      form.addEventListener('submit', () => {
        document.querySelectorAll('button[type="submit"]').forEach(btn => {
          btn.disabled = true;
          btn.textContent = 'Saving…';
        });
        if (overlay) {
          overlay.removeAttribute('hidden');
        }
      });
    }
  </script>
</body>
</html>
"""


def _load_inventory() -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    data = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
    item_options: List[Dict[str, Any]] = []
    item_lookup: Dict[str, Dict[str, Any]] = {}
    for entry in data:
        option = {
            "item_id": entry["item_id"],
            "name": entry["name"],
        "stack_size": entry.get("stack_size", 0),
        "description": entry.get("description", ""),
        }
        option["label"] = f"{option['item_id']:>4} — {option['name']}"
        item_options.append(option)
        item_lookup[str(option["item_id"])] = option
    item_options.sort(key=lambda opt: opt["label"].lower())
    return item_options, item_lookup


def _read_slots() -> List[Dict[str, Any]]:
    with open(SOURCE_SAVE, "rb") as handle:
        data = s.GameSave.parse(handle)
    slots = []
    for idx, cell in enumerate(data.game_data.main_player.package.grids):
        slots.append(
            {
                "slot": idx,
                "item_id": int(cell.item_id or 0),
                "count": int(cell.count or 0),
                "stack_size": int(cell.stack_size or 0),
            }
        )
    return slots


def _write_slots(form_data, item_lookup: Dict[str, Dict[str, Any]]) -> int:
    with open(SOURCE_SAVE, "rb") as handle:
        data = s.GameSave.parse(handle)

    grids = data.game_data.main_player.package.grids
    updated = 0
    for idx, cell in enumerate(grids):
        item_field = form_data.get(f"slot-{idx}-item")
        count_field = form_data.get(f"slot-{idx}-count")
        if item_field is None and count_field is None:
            continue

        try:
            selected_id = int(item_field or 0)
        except (TypeError, ValueError):
            selected_id = 0

        try:
            desired_count = int(count_field or 0)
        except (TypeError, ValueError):
            desired_count = 0

        if selected_id <= 0:
            new_id = 0
            new_stack = 0
            new_count = 0
        else:
            meta = item_lookup.get(str(selected_id), {})
            stack_size = int(meta.get("stack_size") or 0)
            new_id = selected_id
            new_stack = stack_size if stack_size > 0 else cell.stack_size or stack_size
            max_allowed = new_stack if new_stack > 0 else desired_count
            if new_stack > 0:
                desired_count = min(desired_count or new_stack, new_stack)
            new_count = max(desired_count, 0)

        if (
            cell.item_id != new_id
            or int(cell.count or 0) != new_count
            or int(cell.stack_size or 0) != new_stack
        ):
            cell.item_id = new_id
            cell.stack_size = new_stack
            cell.count = new_count
            updated += 1

    with open(OUTPUT_SAVE, "wb") as handle:
        data.save(handle)

    return updated


@app.route("/", methods=["GET", "POST"])
def editor():
    item_options, item_lookup = _load_inventory()
    if request.method == "POST":
        updated = _write_slots(request.form, item_lookup)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Save complete at {timestamp}: updated {updated} slot(s) → {OUTPUT_SAVE}"
        flash(message)
        session["last_saved_message"] = message
        return redirect(url_for("editor"))

    slots = _read_slots()
    for slot in slots:
      slot["description"] = item_lookup.get(str(slot["item_id"]), {}).get("description", "")
      last_saved = session.pop("last_saved_message", None)
    return render_template_string(
        TEMPLATE,
        slots=slots,
        item_options=item_options,
        item_data=item_lookup,
        source_save=str(SOURCE_SAVE),
        output_save=str(OUTPUT_SAVE),
        last_saved=last_saved,
    )


if __name__ == "__main__":
    app.run(debug=True)
