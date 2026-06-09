from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import shlex
import socket
import subprocess
import time
import urllib.request

from app.config import Settings, load_settings


logger = logging.getLogger("smart-service")


def configure_logging(settings: Settings) -> None:
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / settings.log_file

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        RotatingFileHandler(
            log_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
        ),
    ]

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    for handler in handlers:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    logger.info("logging to %s", log_path)


def has_socket_connectivity(settings: Settings) -> bool:
    try:
        with socket.create_connection(
            (settings.socket_host, settings.socket_port),
            timeout=settings.socket_timeout_seconds,
        ):
            return True
    except OSError as exc:
        logger.warning("socket connectivity check failed: %s", exc)
        return False


def has_http_connectivity(settings: Settings) -> bool:
    request = urllib.request.Request(settings.http_url, method="GET")
    try:
        with urllib.request.urlopen(
            request,
            timeout=settings.http_timeout_seconds,
        ) as response:
            return 200 <= response.status < 400
    except Exception as exc:  # noqa: BLE001
        logger.warning("http connectivity check failed: %s", exc)
        return False


def has_internet(settings: Settings) -> bool:
    if has_socket_connectivity(settings):
        return True
    return has_http_connectivity(settings)


def reboot_host(settings: Settings) -> None:
    command = shlex.split(settings.reboot_command)
    logger.error("outage threshold reached, rebooting host with command: %s", command)
    subprocess.run(command, check=True)


def run() -> None:
    settings = load_settings()
    configure_logging(settings)
    logger.info(
        "starting internet watchdog: interval=%ss max_outage=%ss socket=%s:%s http=%s",
        settings.check_interval_seconds,
        settings.max_outage_seconds,
        settings.socket_host,
        settings.socket_port,
        settings.http_url,
    )

    outage_started_at: float | None = None

    while True:
        if has_internet(settings):
            if outage_started_at is not None:
                outage_seconds = int(time.monotonic() - outage_started_at)
                logger.info("connectivity restored after %ss", outage_seconds)
                outage_started_at = None
            else:
                logger.info("connectivity ok")
        else:
            now = time.monotonic()
            if outage_started_at is None:
                outage_started_at = now
                logger.warning("connectivity lost, starting outage timer")

            outage_seconds = int(now - outage_started_at)
            remaining_seconds = max(settings.max_outage_seconds - outage_seconds, 0)
            logger.warning(
                "still offline for %ss, reboot in %ss if connectivity does not return",
                outage_seconds,
                remaining_seconds,
            )

            if outage_seconds >= settings.max_outage_seconds:
                reboot_host(settings)
                raise RuntimeError("reboot command returned unexpectedly")

        time.sleep(settings.check_interval_seconds)


if __name__ == "__main__":
    run()
