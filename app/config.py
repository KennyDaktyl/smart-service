from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int(name: str, default: int, min_value: int = 0) -> int:
    raw = os.getenv(name, str(default)).strip()
    value = int(raw)
    if value < min_value:
        raise ValueError(f"{name} must be >= {min_value}, got {value}")
    return value


def _get_float(name: str, default: float, min_value: float = 0.0) -> float:
    raw = os.getenv(name, str(default)).strip()
    value = float(raw)
    if value < min_value:
        raise ValueError(f"{name} must be >= {min_value}, got {value}")
    return value


def _get_str(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class Settings:
    check_interval_seconds: int
    max_outage_seconds: int
    socket_host: str
    socket_port: int
    socket_timeout_seconds: float
    http_url: str
    http_timeout_seconds: float
    reboot_command: str


def load_settings() -> Settings:
    return Settings(
        check_interval_seconds=_get_int("CHECK_INTERVAL_SECONDS", 30, min_value=1),
        max_outage_seconds=_get_int("MAX_OUTAGE_SECONDS", 600, min_value=30),
        socket_host=_get_str("SOCKET_HOST", "1.1.1.1"),
        socket_port=_get_int("SOCKET_PORT", 53, min_value=1),
        socket_timeout_seconds=_get_float("SOCKET_TIMEOUT_SECONDS", 3.0, min_value=0.1),
        http_url=_get_str("HTTP_URL", "https://clients3.google.com/generate_204"),
        http_timeout_seconds=_get_float("HTTP_TIMEOUT_SECONDS", 5.0, min_value=0.1),
        reboot_command=_get_str(
            "REBOOT_COMMAND",
            "nsenter --target 1 --mount --uts --ipc --net --pid /sbin/reboot",
        ),
    )
