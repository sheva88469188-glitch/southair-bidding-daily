from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urljoin


@dataclass(frozen=True)
class Announcement:
    column_name: str
    title: str
    area: str
    budget_price: str
    purchase_method: str
    publish_time: str
    deadline: str
    source_url: str

    @property
    def dedupe_key(self) -> str:
        if self.source_url:
            return f"url:{self.source_url}"
        return f"title-date:{self.title}|{self.publish_time}"


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def format_datetime(value: str | None, with_time: bool = True) -> str:
    dt = parse_datetime(value)
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M" if with_time else "%Y-%m-%d")


def format_price(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)
    if amount == amount.to_integral_value():
        return f"{amount:,.0f}"
    return f"{amount:,.2f}"


def normalize_area(row: dict[str, Any]) -> str:
    province = (row.get("provinceName") or row.get("province") or "").strip()
    city = (row.get("cityName") or row.get("city") or "").strip()
    if not province and not city:
        return "全国"
    if province and city and province == city:
        return province
    return " ".join(part for part in (province, city) if part)


def get_deadline(row: dict[str, Any]) -> str:
    return (
        row.get("tenderFileSaleEndTime")
        or row.get("quoteEndTime")
        or row.get("expiryDate")
        or row.get("quoteBeginTime")
        or ""
    )


def row_is_on_date(row: dict[str, Any], target_date: date) -> bool:
    publish_dt = parse_datetime(row.get("publishDate"))
    return bool(publish_dt and publish_dt.date() == target_date)


def parse_announcement(
    row: dict[str, Any],
    column_name: str,
    webfile_base: str,
) -> Announcement:
    relative_url = row.get("url") or ""
    source_url = urljoin(webfile_base.rstrip("/") + "/", relative_url.lstrip("/"))
    return Announcement(
        column_name=column_name,
        title=(row.get("title") or "").strip(),
        area=normalize_area(row),
        budget_price=format_price(row.get("estimateTotalPrice")),
        purchase_method=(row.get("purchaseModeName") or "").strip(),
        publish_time=format_datetime(row.get("publishDate")),
        deadline=format_datetime(get_deadline(row)),
        source_url=source_url,
    )


def dedupe_announcements(items: list[Announcement]) -> list[Announcement]:
    seen: set[str] = set()
    result: list[Announcement] = []
    for item in items:
        key = item.dedupe_key
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
