from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Tuple

from modules_utils.config_loader import ConfigLoader


@dataclass
class HealthReport:
    ok: bool
    details: Dict[str, str]

    def to_json(self) -> str:
        return json.dumps({"ok": self.ok, "details": self.details}, ensure_ascii=False)


def _check_dir_exists(p: Path, name: str, details: Dict[str, str]) -> bool:
    if p.exists() and p.is_dir():
        details[name] = "OK"
        return True
    details[name] = f"FAIL: missing directory {p.as_posix()}"
    return False


def _check_file_exists(p: Path, name: str, details: Dict[str, str]) -> bool:
    if p.exists() and p.is_file():
        details[name] = "OK"
        return True
    details[name] = f"FAIL: missing file {p.as_posix()}"
    return False


def _check_writable_dir(p: Path, name: str, details: Dict[str, str]) -> bool:
    try:
        p.mkdir(parents=True, exist_ok=True)
        test_file = p / ".health_write_test"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        test_file.unlink(missing_ok=True)
        details[name] = "OK"
        return True
    except Exception as e:
        details[name] = f"FAIL: write error in {p.as_posix()}: {e}"
        return False


def _check_disk_space(p: Path, name: str, details: Dict[str, str], min_free_mb: int = 200) -> bool:
    try:
        total, used, free = 0, 0, 0
        if hasattr(os, "statvfs"):  # POSIX
            st = os.statvfs(p.as_posix())
            free = (st.f_bavail * st.f_frsize) // (1024 * 1024)
            total = (st.f_blocks * st.f_frsize) // (1024 * 1024)
            used = total - free
        else:
            # Windows fallback
            import shutil
            total_b, used_b, free_b = shutil.disk_usage(p)
            total, used, free = total_b // (1024 * 1024), used_b // (1024 * 1024), free_b // (1024 * 1024)
        if free >= min_free_mb:
            details[name] = f"OK: {free} MB free"
            return True
        details[name] = f"FAIL: low disk space ({free} MB free < {min_free_mb} MB)"
        return False
    except Exception as e:
        details[name] = f"FAIL: disk check error: {e}"
        return False


def _check_log_size(log_file: Path, name: str, details: Dict[str, str], max_mb: int = 10) -> bool:
    try:
        if not log_file.exists():
            details[name] = "WARN: log file not created yet"
            return True
        size_mb = log_file.stat().st_size / (1024 * 1024)
        if size_mb <= max_mb:
            details[name] = f"OK: {size_mb:.2f} MB"
            return True
        details[name] = f"WARN: large log ({size_mb:.2f} MB > {max_mb} MB)"
        return True
    except Exception as e:
        details[name] = f"FAIL: log size check error: {e}"
        return False


def run_health_checks(project_root: Path = Path(".")) -> HealthReport:
    details: Dict[str, str] = {}
    ok = True

    # Dossiers clés
    config_dir = project_root / "config"
    logs_dir = project_root / "logs"

    ok &= _check_dir_exists(config_dir, "config_dir", details)
    ok &= _check_dir_exists(logs_dir, "logs_dir", details)
    ok &= _check_writable_dir(logs_dir, "logs_writable", details)

    # Fichiers config
    ok &= _check_file_exists(config_dir / "risk.yml", "risk.yml", details)
    ok &= _check_file_exists(config_dir / "system.yml", "system.yml", details)
    ok &= _check_file_exists(config_dir / "api_limits.yml", "api_limits.yml", details)

    # Validation via ConfigLoader (Pydantic)
    try:
        loader = ConfigLoader(config_dir)
        _ = loader.load_risk()
        _ = loader.load_system()
        _ = loader.load_api_limits()
        details["config_validation"] = "OK"
    except Exception as e:
        ok = False
        details["config_validation"] = f"FAIL: {e}"

    # Disque et logs
    ok &= _check_disk_space(project_root, "disk_space", details, min_free_mb=200)
    _ = _check_log_size(logs_dir / "system.log", "log_size", details, max_mb=10)

    return HealthReport(ok=bool(ok), details=details)


def _main_cli():
    report = run_health_checks(Path("."))
    print(report.to_json())
    # code 0 si ok, 1 sinon
    raise SystemExit(0 if report.ok else 1)


if __name__ == "__main__":
    _main_cli()
