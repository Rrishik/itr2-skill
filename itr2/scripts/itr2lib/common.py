from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Iterable

QUARTERS = (
    "Q1 (<=15-Jun)",
    "Q2 (16-Jun..15-Sep)",
    "Q3 (16-Sep..15-Dec)",
    "Q4 (16-Dec..15-Mar)",
    "Q5 (16-Mar..31-Mar)",
)


class InputError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise InputError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise InputError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError("The input JSON root must be an object.")
    return value


def obj(value: Any, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InputError(f"{field} must be an object.")
    return value


def array(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise InputError(f"{field} must be an array.")
    return value


def number(value: Any, field: str = "value", default: Decimal = Decimal(0)) -> Decimal:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise InputError(f"{field} must be numeric.")
    try:
        result = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError, ValueError) as exc:
        raise InputError(f"{field} must be numeric.") from exc
    if not result.is_finite():
        raise InputError(f"{field} must be finite.")
    return result


def money(value: Any) -> int:
    return int(number(value).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def decimal_json(value: Decimal, places: int = 2) -> int | float:
    unit = Decimal(1).scaleb(-places)
    rounded = value.quantize(unit, rounding=ROUND_HALF_EVEN)
    if rounded == rounded.to_integral_value():
        return int(rounded)
    return float(rounded)


def parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{field} must be a date.")
    raw = value.strip()
    formats = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y")
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    raise InputError(f"{field} must use YYYY-MM-DD or an unambiguous supported date format.")


def quarter_for_date(value: date) -> str:
    month_day = value.month * 100 + value.day
    if value.month >= 4:
        if month_day <= 615:
            return QUARTERS[0]
        if month_day <= 915:
            return QUARTERS[1]
        if month_day <= 1215:
            return QUARTERS[2]
        return QUARTERS[3]
    if month_day <= 315:
        return QUARTERS[3]
    return QUARTERS[4]


def resolve_path(value: str | Path, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return decimal_json(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    return value


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_json(path: Path, value: Any) -> None:
    payload = (
        json.dumps(json_ready(value), ensure_ascii=False, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    atomic_write_bytes(path, payload)


def write_text(path: Path, value: str) -> None:
    atomic_write_bytes(path, value.encode("utf-8"))


def sum_numbers(values: Iterable[Any]) -> Decimal:
    return sum((number(value) for value in values), Decimal(0))
