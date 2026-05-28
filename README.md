# paper-tools

> **Centralized tool registry, execution engine, and schema validation for the Paper ecosystem.**

## Structure

```
paper-tools/
├── app/
│   ├── registry/       ← Tool registration + discovery + schema export
│   ├── execution/      ← Tool execution with timeout + batch support
│   ├── schemas/        ← JSON Schema validation for arguments
│   └── builtin/        ← Built-in tool implementations
│       ├── crm/        ← CRM contact lookup/update
│       ├── email/      ← Email sending
│       ├── scheduling/ ← Calendar booking/cancellation
│       └── search/     ← Web search
├── tests/
└── README.md
```

## Usage

```python
from app.registry import get_tool_registry
from app.execution import get_execution_engine

registry = get_tool_registry()
engine = get_execution_engine()

# List available tools
print(registry.list_tools())  # ['book_meeting', 'cancel_meeting', ...]

# Execute a tool
result = await engine.execute("book_meeting", {
    "title": "Demo Call",
    "date": "2026-06-01",
    "time": "14:00",
    "duration_min": 30,
})

# Get schemas for LLM function calling
schemas = registry.schemas()
```

## License

MIT
