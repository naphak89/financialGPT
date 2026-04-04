"""
Legacy Finnhub smoke test — API key must come from the environment.

Set FINNHUB_API_KEY in your shell or IDE before running.
Do not commit real API keys to the repository.
"""

import json
import os

import finnhub

api_key = os.environ.get("FINNHUB_API_KEY")
if not api_key:
    raise SystemExit("Set FINNHUB_API_KEY in the environment.")

finnhub_client = finnhub.Client(api_key=api_key)

# Fetch latest company news
news_items = finnhub_client.company_news("AAPL", _from="2025-12-01", to="2026-01-09")

output_path = os.path.join(os.getcwd(), "company news")
with open(output_path, "w", encoding="utf-8") as fp:
    fp.write(json.dumps(news_items, ensure_ascii=False, indent=2))

news_items = finnhub_client.general_news("stock", min_id=0)

output_path = os.path.join(os.getcwd(), "market news")
with open(output_path, "w", encoding="utf-8") as fp:
    fp.write(json.dumps(news_items, ensure_ascii=False, indent=2))

print(f"Wrote {len(news_items)} items to {output_path}")
