from tracker import load_applied

SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_applications",
        "description": "Return the full list of jobs already applied to, with their current status.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def run() -> list[dict]:
    return load_applied()
