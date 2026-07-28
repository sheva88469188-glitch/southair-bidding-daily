from __future__ import annotations

import time
from datetime import date
from typing import Any

import requests
from requests import RequestException

from parser import Announcement, dedupe_announcements, parse_announcement, row_is_on_date


class SouthairCrawler:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.site = config["site"]
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                ),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json; charset=utf-8",
                "Origin": self.site["base_url"],
            }
        )

    def fetch_today(self, target_date: date) -> list[Announcement]:
        all_items: list[Announcement] = []
        for column in self.config["columns"]:
            all_items.extend(self._fetch_column(column, target_date))
        return dedupe_announcements(all_items)

    def _fetch_column(self, column: dict[str, Any], target_date: date) -> list[Announcement]:
        rows: list[dict[str, Any]] = []
        page_no = 1
        max_pages = int(self.site.get("max_pages", 5))
        page_size = int(self.site.get("page_size", 50))

        while page_no <= max_pages:
            data = self._request_page(column, page_no, page_size)
            result = data.get("res") or {}
            page_rows = result.get("rows") or []
            rows.extend(page_rows)

            page_count = int(result.get("pageCount") or 0)
            if page_no >= page_count or not page_rows:
                break
            page_no += 1

        return [
            parse_announcement(row, column["name"], self.site["webfile_base"])
            for row in rows
            if row_is_on_date(row, target_date)
        ]

    def _request_page(
        self,
        column: dict[str, Any],
        page_no: int,
        page_size: int,
    ) -> dict[str, Any]:
        payload = {
            "pageNo": page_no,
            "pageSize": page_size,
            "dto": {
                "siteId": self.site["site_id"],
                "categoryId": column["category_id"],
                "agentCompanyName": "",
                "title": "",
                "province": "",
                "city": "",
                "publishDays": "1",
                "estimateTotalPriceBegin": "",
                "estimateTotalPriceEnd": "",
            },
        }
        retry_times = int(self.site.get("request_retry_times", 3))
        retry_delay_seconds = float(self.site.get("request_retry_delay_seconds", 5))
        last_error: Exception | None = None

        for attempt in range(1, retry_times + 1):
            try:
                response = self.session.post(
                    self.site["api_url"],
                    json=payload,
                    headers={"Referer": column["index_url"]},
                    timeout=int(self.site.get("request_timeout_seconds", 20)),
                )
                response.raise_for_status()
                data = response.json()
                if data.get("code") != 0:
                    raise RuntimeError(f"接口返回异常: {data}")
                return data
            except (RequestException, ValueError, RuntimeError) as exc:
                last_error = exc
                if attempt >= retry_times:
                    break
                print(
                    f"请求南航接口失败，准备重试 {attempt}/{retry_times}: "
                    f"{column['name']} 第 {page_no} 页，错误: {exc}"
                )
                time.sleep(retry_delay_seconds * attempt)

        raise RuntimeError(
            f"请求南航接口失败，已重试 {retry_times} 次: "
            f"{column['name']} 第 {page_no} 页"
        ) from last_error
