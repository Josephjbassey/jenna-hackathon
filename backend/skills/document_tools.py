"""Document & Data Analysis Skill for Jenna-Unified.

Enables Jenna to:
- Inspect and summarize CSV files
- Parse and query JSON datasets
- Summarize documentation files
"""
import csv
import json
from pathlib import Path
from langchain_core.tools import tool

_ROOT = Path(__file__).resolve().parent.parent


@tool
def summarize_csv_data(filepath: str, max_rows: int = 8) -> str:
    """Read a CSV file and output header columns, total row count, and first few rows as a Markdown table.
    
    Args:
        filepath: Path to the CSV file (relative to workspace or absolute)
        max_rows: Number of preview rows to format (default: 8)
    """
    path = Path(filepath)
    if not path.is_absolute():
        path = _ROOT / path

    if not path.exists():
        return f"CSV file not found at: {filepath}"

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return f"CSV file {path.name} is empty."

            rows = []
            count = 0
            for r in reader:
                count += 1
                if len(rows) < max_rows:
                    rows.append(r)

        # Build markdown table
        md = [f"### CSV Analysis: `{path.name}` ({count} rows total)\n"]
        md.append("| " + " | ".join(header) + " |")
        md.append("| " + " | ".join(["---"] * len(header)) + " |")
        for r in rows:
            # Pad row if fewer items than header
            padded = r + [""] * (len(header) - len(r))
            md.append("| " + " | ".join(padded[:len(header)]) + " |")

        return "\n".join(md)
    except Exception as e:
        return f"Error reading CSV {filepath}: {e}"


@tool
def inspect_json_structure(filepath: str) -> str:
    """Inspect a JSON file, showing top-level keys, item counts, data types, and sample entries.
    
    Args:
        filepath: Path to the JSON file
    """
    path = Path(filepath)
    if not path.is_absolute():
        path = _ROOT / path

    if not path.exists():
        return f"JSON file not found at: {filepath}"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            keys_info = {k: type(v).__name__ for k, v in list(data.items())[:20]}
            return (
                f"### JSON Object `{path.name}`\n"
                f"- **Total Keys:** {len(data)}\n"
                f"- **Top-Level Schema:** {json.dumps(keys_info, indent=2)}"
            )
        elif isinstance(data, list):
            sample = data[0] if data else {}
            return (
                f"### JSON Array `{path.name}`\n"
                f"- **Total Items:** {len(data)}\n"
                f"- **Sample Item Structure:** {json.dumps(sample, indent=2)[:800]}"
            )
        return f"JSON file contains primitive type: {type(data).__name__}"
    except Exception as e:
        return f"Error parsing JSON {filepath}: {e}"
