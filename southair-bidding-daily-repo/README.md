# 南航采购招标网每日公告简报

这个 MVP 每天抓取南航采购招标网两个栏目中“发布时间为当天”的公告，合并去重后生成 Markdown 和 HTML 邮件简报，并通过 SMTP 发送。

已分析页面数据来源：两个栏目列表都由页面脚本 `typeTellApart.js` 调用接口加载，MVP 直接使用 `requests` 调用：

```text
POST https://csbidding.csair.cn/cms/api/dynamicData/queryContentPage
```

栏目配置：

| 栏目 | categoryId |
| --- | --- |
| 招标公告 | `964895061131132928` |
| 采购公告 | `964893593951010816` |

## 功能

- 抓取字段：栏目名称、标题名称、地区、预算价格、采购方式、发布时间、截止时间、原文链接
- 只保留北京时间当天发布的公告
- 两个栏目合并后去重，优先按原文链接去重，其次按“标题名称 + 发布时间”去重
- 同时生成 Markdown 和 HTML 邮件内容
- 当天没有新增公告时，也发送“今日无新增公告”邮件
- 支持本地手动运行和 GitHub Actions 每天北京时间 19:00 自动运行
- SMTP 账号、授权码、收件人等敏感信息全部从环境变量读取

## 本地运行

进入项目目录：

```bash
cd southair-bidding-daily
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

先本地预览，不发送邮件：

```bash
python src/main.py --dry-run --output-dir reports
```

指定日期预览：

```bash
python src/main.py --dry-run --date 2026-07-16 --output-dir reports
```

发送邮件前配置环境变量：

```bash
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="465"
export SMTP_USER="your-email@example.com"
export SMTP_PASSWORD="your-smtp-auth-code"
export SMTP_FROM="your-email@example.com"
export SMTP_TO="receiver@example.com"
export SMTP_USE_SSL="true"
export SMTP_USE_STARTTLS="false"
```

发送：

```bash
python src/main.py
```

如果你的邮箱服务商使用 587 端口和 STARTTLS，可以这样配置：

```bash
export SMTP_PORT="587"
export SMTP_USE_SSL="false"
export SMTP_USE_STARTTLS="true"
```

## GitHub Actions 部署

1. 把 `southair-bidding-daily` 目录提交到 GitHub 仓库根目录。
2. 在仓库的 `Settings -> Secrets and variables -> Actions` 中添加这些 Secrets：

| Secret | 说明 |
| --- | --- |
| `SMTP_HOST` | SMTP 服务器地址 |
| `SMTP_PORT` | SMTP 端口，常见为 `465` 或 `587` |
| `SMTP_USER` | 邮箱账号 |
| `SMTP_PASSWORD` | SMTP 授权码或应用专用密码 |
| `SMTP_FROM` | 发件人邮箱，可与账号相同 |
| `SMTP_TO` | 收件人邮箱，多个邮箱用英文逗号分隔 |
| `SMTP_USE_SSL` | 常见填 `true` |
| `SMTP_USE_STARTTLS` | 使用 587/STARTTLS 时填 `true`，SSL 模式填 `false` |

3. 工作流文件位于 `.github/workflows/daily.yml`，定时配置为：

```yaml
cron: "0 11 * * *"
```

GitHub Actions 使用 UTC 时间，`11:00 UTC` 对应北京时间 `19:00`。

也可以在 GitHub Actions 页面手动点击 `Run workflow` 立即运行一次。

## 配置说明

主要配置在 `config.yaml`：

- `site.page_size`：接口每页抓取数量
- `site.max_pages`：每个栏目最多抓取页数
- `columns`：栏目名称、栏目 ID 和来源页面
- `report.timezone`：默认 `Asia/Shanghai`
- `mail.*_env`：读取 SMTP 配置的环境变量名

## 项目结构

```text
southair-bidding-daily/
  README.md
  requirements.txt
  config.yaml
  .github/workflows/daily.yml
  src/
    main.py
    crawler.py
    parser.py
    report.py
    mailer.py
    storage.py
  data/
    seen.json
```

`data/seen.json` 目前用于记录最近一次抓取到的公告去重键，MVP 的“新增”口径仍以“发布时间为当天”为准，避免本地重复预览影响当天邮件内容。
