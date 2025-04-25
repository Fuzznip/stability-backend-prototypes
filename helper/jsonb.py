import json

def load_jsonb(data: str) -> dict:
    return json.loads(data)

def save_jsonb(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=4)