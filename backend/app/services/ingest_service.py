import json
from pathlib import Path

def load_emails():

    current_file = Path(__file__)

    project_root = current_file.parent.parent.parent.parent

    json_path = project_root / "data" / "email-data-advanced.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data