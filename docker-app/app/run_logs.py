from __future__ import annotations

import logging
from datetime import datetime, timedelta
from .time_utils import now_local
from pathlib import Path
from typing import Iterator

from .config import DATA_DIR


APP_LOGGER = logging.getLogger("yahaha_cover_studio")
if not APP_LOGGER.handlers:
    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    APP_LOGGER.addHandler(stream)
    APP_LOGGER.setLevel(logging.INFO)


class RunLog:
    def __init__(self, trigger: str) -> None:
        now = now_local()
        self.started_at = now
        self.trigger = trigger or "manual"
        self.task_id = now.strftime("%Y%m%d_%H%M%S_%f")
        self.path = DATA_DIR / "logs" / now.strftime("%Y-%m-%d") / f"{self.task_id}_{self.trigger}.log"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handler = logging.FileHandler(self.path, encoding="utf-8")
        self._handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        # A generation is single-flight. Attach the run file to the shared app
        # logger so download, render and upload failures emitted by services are
        # captured in this task's file as well as Docker stdout.
        self.logger = APP_LOGGER
        self.logger.addHandler(self._handler)

    def info(self, message: str, *args: object) -> None:
        self.logger.info(message, *args)

    def warning(self, message: str, *args: object) -> None:
        self.logger.warning(message, *args)

    def exception(self, message: str, *args: object) -> None:
        self.logger.exception(message, *args)

    def close(self) -> None:
        self.logger.removeHandler(self._handler)
        self._handler.close()


def clean_expired_logs(retention_days: int) -> int:
    logs_dir = DATA_DIR / "logs"
    cutoff = now_local() - timedelta(days=max(1, retention_days))
    removed = 0
    if not logs_dir.exists():
        return removed
    for path in logs_dir.rglob("*.log"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime, tz=cutoff.tzinfo) < cutoff:
                path.unlink()
                removed += 1
        except OSError as error:
            APP_LOGGER.warning("清理日志失败 %s: %s", path, error)
    for directory in sorted((path for path in logs_dir.rglob("*") if path.is_dir()), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass
    return removed


def iter_logs() -> Iterator[Path]:
    logs_dir = DATA_DIR / "logs"
    if not logs_dir.exists():
        return iter(())
    return iter(sorted((path for path in logs_dir.rglob("*.log") if path.is_file()), key=lambda path: path.stat().st_mtime, reverse=True))


def safe_log_path(name: str) -> Path | None:
    candidate = (DATA_DIR / "logs" / str(name or "")).resolve()
    root = (DATA_DIR / "logs").resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_file() and candidate.suffix == ".log" else None
