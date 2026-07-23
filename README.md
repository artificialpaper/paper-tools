# Paper Tools (`paper-tools`)

> Dynamic Tool Registry, JSON Schema Validator, and Execution Engine for the Paper AI Ecosystem.

`paper-tools` is the execution engine for custom tools and functions (CRM lookup, appointment scheduling, email dispatch, web search). It provides dynamic tool registration, parameter validation against JSON Schema, timeout enforcement, and schema exports for OpenAI Function Calling and Model Context Protocol (MCP).

---

## Role in the Ecosystem

```
Caller Services (paper-caller / paper-mcp)
                   |
                   | Tool Execution Request
                   v
              paper-tools
              ├── 1. Registry Lookup (`registry.py`)
              ├── 2. JSON Schema Validation (`schemas.py`)
              ├── 3. Async Timeout Execution (`engine.py`)
              └── 4. Built-in Tools (`builtin/`)
```

- **What it owns:** Tool registration decorators, schema definitions, timeout execution guards (`asyncio.wait_for`), exception handling, and reference tool modules (`crm`, `calendar`, `email`, `search`).
- **What it does NOT do:** `paper-tools` does not make direct LLM calls or manage network transport.

---

## Key Features

- **Decorator Registration:** Simple `@registry.register` decorator to expose Python functions to LLMs.
- **Strict JSON Schema Validation:** Validates incoming function arguments using Draft 7 JSON Schemas before execution.
- **Timeout Protection:** Configurable execution timeouts (default 5.0 seconds) to prevent frozen external API calls.
- **Multi-Format Export:** Exports tool definitions automatically as OpenAI Function Call schemas or MCP Tool arrays.
- **Built-in Reference Library:** Pre-built reference tool modules for common business workflows.

---

## Repository Structure

```
paper-tools/
├── app/
│   ├── registry.py              # In-memory ToolRegistry index
│   ├── engine.py                # Async ToolExecutionEngine with timeout guard
│   ├── schemas.py               # JSON Schema validation & format exporter
│   └── builtin/                 # Reference tool implementations
│       ├── crm.py               # Customer profile lookup tool
│       ├── calendar.py          # Appointment scheduling tool
│       ├── email.py             # Transactional email sender
│       └── search.py            # Web search integration tool
├── tests/                       # Unit tests
├── pyproject.toml               # Dependencies
└── README.md
```

---

## Quickstart & Setup

### Installation

```bash
# Clone repository
git clone https://github.com/artificialpaper/paper-tools.git
cd paper-tools

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

---

## Defining a Custom Tool

```python
from paper_tools.app.registry import registry

@registry.register(
    name="check_appointment_slots",
    description="Check available doctor appointment slots for a target date.",
    parameters={
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Target date in YYYY-MM-DD format"
            }
        },
        "required": ["date"]
    }
)
async def check_appointment_slots(date: str) -> list[str]:
    # Custom business logic
    return ["09:00 AM", "02:30 PM", "04:00 PM"]
```

---

## Executing a Tool safely

```python
from paper_tools.app.engine import engine

result = await engine.execute(
    tool_name="check_appointment_slots",
    arguments={"date": "2026-07-25"}
)

print(result)
# Output: ["09:00 AM", "02:30 PM", "04:00 PM"]
```

---

## Testing

```bash
# Run pytest test suite
pytest tests/
```

---

## Related Repositories

- [paper-caller](https://github.com/artificialpaper/paper-caller) - Real-Time Voice AI Agent Runtime
- [paper-mcp](https://github.com/artificialpaper/paper-mcp) - Model Context Protocol Bridge
- [paper-core](https://github.com/artificialpaper/paper-core) - Central LLM Inference Gateway
- [paper-docs](https://github.com/artificialpaper/paper-docs) - Official Ecosystem Documentation Portal

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
