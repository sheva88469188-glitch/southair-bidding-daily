from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from crawler import SouthairCrawler
from mailer import send_email
from report import build_html, build_markdown, build_subject
from storage import save_seen


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    timezone = ZoneInfo(config["report"].get("timezone", "Asia/Shanghai"))
    target_date = args.date or datetime.now(timezone).date()

    crawler = SouthairCrawler(config)
    items = crawler.fetch_today(target_date)

    subject = build_subject(config["report"]["subject_prefix"], target_date, len(items))
    markdown_body = build_markdown(items, target_date)
    html_body = build_html(items, target_date)

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir.joinpath(f"southair-bidding-{target_date}.md").write_text(markdown_body, encoding="utf-8")
        output_dir.joinpath(f"southair-bidding-{target_date}.html").write_text(html_body, encoding="utf-8")

    if args.dry_run:
        print(subject)
        print()
        print(markdown_body)
    else:
        send_email(config, subject, markdown_body, html_body)
        save_seen(ROOT / "data" / "seen.json", items)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="南航采购招标网今日新增公告邮件简报")
    parser.add_argument("--config", default=str(ROOT / "config.yaml"), help="配置文件路径")
    parser.add_argument("--date", type=date.fromisoformat, help="指定抓取日期，格式 YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="只打印简报，不发送邮件")
    parser.add_argument("--output-dir", help="同时输出 Markdown 和 HTML 简报到指定目录")
    return parser.parse_args()


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


if __name__ == "__main__":
    main()
