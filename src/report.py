from __future__ import annotations

from datetime import date
from html import escape

from parser import Announcement


HEADERS = ["栏目名称", "标题名称", "地区", "预算价格", "采购方式", "发布时间", "截止时间", "原文链接"]


def build_subject(prefix: str, target_date: date, count: int) -> str:
    return f"{prefix} - {target_date.isoformat()}（{count}条）"


def build_markdown(items: list[Announcement], target_date: date) -> str:
    title = f"# 南航采购招标网今日新增公告（{target_date.isoformat()}）"
    if not items:
        return f"{title}\n\n今日无新增公告。\n"

    lines = [title, "", f"共发现 {len(items)} 条发布时间为当天的公告。", ""]
    lines.append("| " + " | ".join(HEADERS) + " |")
    lines.append("| " + " | ".join(["---"] * len(HEADERS)) + " |")
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(item.column_name),
                    _md_cell(item.title),
                    _md_cell(item.area),
                    _md_cell(item.budget_price),
                    _md_cell(item.purchase_method),
                    _md_cell(item.publish_time),
                    _md_cell(item.deadline),
                    f"[查看原文]({item.source_url})",
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def build_html(items: list[Announcement], target_date: date) -> str:
    title = f"南航采购招标网今日新增公告（{target_date.isoformat()}）"
    style = """
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #1f2937; }
    table { border-collapse: collapse; width: 100%; font-size: 14px; }
    th, td { border: 1px solid #d1d5db; padding: 8px 10px; vertical-align: top; }
    th { background: #f3f4f6; text-align: left; }
    a { color: #0b66c3; }
    """
    if not items:
        body = "<p>今日无新增公告。</p>"
    else:
        rows = []
        for item in items:
            rows.append(
                "<tr>"
                f"<td>{escape(item.column_name)}</td>"
                f"<td>{escape(item.title)}</td>"
                f"<td>{escape(item.area)}</td>"
                f"<td>{escape(item.budget_price)}</td>"
                f"<td>{escape(item.purchase_method)}</td>"
                f"<td>{escape(item.publish_time)}</td>"
                f"<td>{escape(item.deadline)}</td>"
                f'<td><a href="{escape(item.source_url)}">查看原文</a></td>'
                "</tr>"
            )
        body = (
            f"<p>共发现 {len(items)} 条发布时间为当天的公告。</p>"
            "<table><thead><tr>"
            + "".join(f"<th>{escape(header)}</th>" for header in HEADERS)
            + "</tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    return f"<!doctype html><html><head><meta charset=\"utf-8\"><style>{style}</style></head><body><h2>{escape(title)}</h2>{body}</body></html>"


def _md_cell(value: str) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ").strip()
