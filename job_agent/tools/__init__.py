from tools import search, score, fetch, applications, generate, log

TOOLS = [search, score, fetch, applications, generate, log]
SCHEMAS = [t.SCHEMA for t in TOOLS]
REGISTRY = {t.SCHEMA["function"]["name"]: t.run for t in TOOLS}
