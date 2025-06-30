from typing import Any

import pytest


@pytest.fixture
def simple_decl() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "test_tool",
        "description": {"en": "Test tool description.", "ru": "Тестовое описание."},
        "func": "lib.tools.test_func",
    }


@pytest.fixture
def decl_with_triggers() -> dict[str, Any]:
    return {
        "kind": "ToolNode",
        "name": "weather",
        "description": {"en": "Weather tool.", "ru": "Погода."},
        "func": "lib.tools.weather",
        "arguments": [
            {
                "name": "city",
                "type": "str",
                "description": {"en": "City name", "ru": "Город"},
            },
        ],
        "triggers": [
            {"en": "What's the weather?", "ru": "Какая погода?"},
            {"en": "Weather in Moscow", "ru": "Погода в Москве"},
            "Forecast",
        ],
        "tool_prompt_template": "{name}: {description}\n\n\n{triggers}",
    }
