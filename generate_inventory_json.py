import ast
import json
import re
from pathlib import Path
from typing import Any, Dict

SOURCE_DATA = Path("more_inventory_info.py")
OUTPUT_JSON = Path("inventory.json")


def _strip_lua_comments(source: str) -> str:
    result = []
    i = 0
    length = len(source)
    in_string = False
    string_char = ""

    while i < length:
        ch = source[i]
        if in_string:
            result.append(ch)
            if ch == "\\" and i + 1 < length:
                i += 1
                result.append(source[i])
            elif ch == string_char:
                in_string = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = True
            string_char = ch
            result.append(ch)
            i += 1
            continue

        if ch == "-" and i + 1 < length and source[i + 1] == "-":
            i += 2
            if i < length and source[i : i + 2] == "[[":
                i += 2
                while i + 1 < length and source[i : i + 2] != "]]":
                    i += 1
                i += 2
            else:
                while i < length and source[i] not in "\r\n":
                    i += 1
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def _extract_table_block(source: str, table_name: str) -> str:
    match = re.search(rf"\b{re.escape(table_name)}\b\s*=", source)
    if not match:
        raise ValueError(f"Unable to locate table '{table_name}' in {SOURCE_DATA}")

    start = source.find("{", match.end())
    if start == -1:
        raise ValueError(f"Table '{table_name}' does not contain an opening brace")

    depth = 0
    in_string = False
    string_char = ""
    i = start
    block_start = start

    while i < len(source):
        ch = source[i]
        if in_string:
            if ch == "\\" and i + 1 < len(source):
                i += 2
                continue
            if ch == string_char:
                in_string = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = True
            string_char = ch
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[block_start : i + 1]

        i += 1

    raise ValueError(f"Failed to find the end of table '{table_name}'")


def _is_identifier_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _has_word_boundary(text: str, start: int, end: int) -> bool:
    before_ok = start == 0 or not _is_identifier_char(text[start - 1])
    after_ok = end >= len(text) or not _is_identifier_char(text[end])
    return before_ok and after_ok


def _lua_table_to_python_literal(table_text: str) -> str:
    out = []
    i = 0
    length = len(table_text)

    while i < length:
        ch = table_text[i]

        if ch in ("'", '"'):
            start = i
            i += 1
            while i < length:
                current = table_text[i]
                if current == "\\" and i + 1 < length:
                    i += 2
                    continue
                if current == ch:
                    i += 1
                    break
                i += 1
            out.append(table_text[start:i])
            continue

        if table_text.startswith("true", i) and _has_word_boundary(table_text, i, i + 4):
            out.append("True")
            i += 4
            continue
        if table_text.startswith("false", i) and _has_word_boundary(table_text, i, i + 5):
            out.append("False")
            i += 5
            continue
        if table_text.startswith("nil", i) and _has_word_boundary(table_text, i, i + 3):
            out.append("None")
            i += 3
            continue

        if ch == "[":
            j = i + 1
            if j < length and table_text[j] == "-":
                j += 1
            digits_start = j
            while j < length and table_text[j].isdigit():
                j += 1
            if j > digits_start and j < length and table_text[j] == "]":
                k = j + 1
                while k < length and table_text[k].isspace():
                    k += 1
                if k < length and table_text[k] == "=":
                    out.append(table_text[i + 1 : j])
                    out.append(":")
                    i = k + 1
                    continue
            out.append(ch)
            i += 1
            continue

        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < length and (table_text[j].isalnum() or table_text[j] == "_"):
                j += 1
            token = table_text[i:j]
            k = j
            while k < length and table_text[k].isspace():
                k += 1
            if k < length and table_text[k] == "=":
                out.append(f"'{token}':")
                i = k + 1
                continue
            out.append(token)
            i = j
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _load_game_items() -> Dict[int, Dict[str, Any]]:
    source = SOURCE_DATA.read_text(encoding="utf-8")
    stripped = _strip_lua_comments(source)
    table_block = _extract_table_block(stripped, "game_items")
    python_literal = _lua_table_to_python_literal(table_block)
    parsed = ast.literal_eval(python_literal)
    if not isinstance(parsed, dict):
        raise TypeError("Parsed game_items data is not a dictionary")
    return parsed


def _normalize_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_for_json(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_normalize_for_json(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_for_json(item) for item in value]
    if isinstance(value, set):
        return sorted(_normalize_for_json(item) for item in value)
    return value


def main() -> None:
    items = _load_game_items()
    records = []
    for item_id in sorted(items):
        payload = _normalize_for_json(items[item_id])
        record = {"item_id": int(item_id)}
        record.update(payload)
        records.append(record)

    OUTPUT_JSON.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} entries to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
