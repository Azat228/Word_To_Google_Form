import json
from pathlib import Path
from typing import Any


TEST_CONFIGS_DIR = Path(__file__).resolve().parent.parent / "test_configs"


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_test_config_files() -> list[Path]:
    if not TEST_CONFIGS_DIR.exists():
        return []

    return sorted(TEST_CONFIGS_DIR.glob("*.json"))


def load_test_configs() -> list[dict[str, Any]]:
    configs = []

    for path in get_test_config_files():
        config = load_json(path)
        config["_path"] = str(path)
        configs.append(config)

    return configs


def get_config_display_names() -> list[str]:
    configs = load_test_configs()

    return [
        config.get("name", config.get("id", "Unnamed test"))
        for config in configs
    ]


def find_config_by_name(name: str) -> dict[str, Any] | None:
    configs = load_test_configs()

    for config in configs:
        if config.get("name") == name:
            return config

    return None


def find_config_by_id(config_id: str) -> dict[str, Any] | None:
    configs = load_test_configs()

    for config in configs:
        if config.get("id") == config_id:
            return config

    return None