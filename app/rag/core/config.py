import os

from dotenv import load_dotenv
"""RAG source URL configuration constants."""

_ = load_dotenv()

NASDAQ_RARE_EARTH_BATTLEFIELD_2026 = (
    "https://www.nasdaq.com/press-release/why-rare-earth-magnets-are-real-battlefield-"
    "between-us-and-china-2026-02-27"
)
NASDAQ_ROUNDHILL_WEEKLYPAY_ETFS_2025 = (
    "https://www.nasdaq.com/press-release/roundhill-investments-launches-five-additional-"
    "weeklypaytm-etfs-2025-07-24"
)
NASDAQ_SMART_HEALTHCARE_2025 = (
    "https://www.nasdaq.com/press-release/smart-healthcare-taking-over-heres-where-moneys-"
    "headed-2025-06-10"
)
NASDAQ_QUANTUM_THREATS_2025 = (
    "https://www.nasdaq.com/press-release/quantum-threats-are-accelerating-these-companies-"
    "are-preparing-shift-2025-03-18"
)
NASDAQ_GOOGLE_WIZ_2025 = (
    "https://www.nasdaq.com/press-release/google-announces-agreement-acquire-wiz-2025-03-18"
)
NASDAQ_ARTMARKET_Q3_2024 = (
    "https://www.nasdaq.com/press-release/artmarketcom-q3-2024-revenue-13-study-ai-search-"
    "engines-shows-artprice-has-worlds"
)
NASDAQ_CULTUREAMP_GOOGLE_CLOUD = (
    "https://www.nasdaq.com/press-release/culture-amp-selects-google-cloud-to-drive-"
    "generative-ai-innovation-and-governance"
)
NASDAQ_GOOGLE_FASTLY_PRIVACY_SANDBOX = (
    "https://www.nasdaq.com/press-release/google-selects-fastly-oblivious-http-relay-for-"
    "privacy-sandbox-initiative-to-enhance"
)
NASDAQ_GOOGLE_CLOUD_AI_RETAIL_2023 = (
    "https://www.nasdaq.com/press-release/google-cloud-unveils-new-ai-tools-for-retailers-"
    "2023-01-13"
)
NASDAQ_SOUTH_FLORIDA_GOOGLE_PUBLIC_SECTOR = (
    "https://www.nasdaq.com/press-release/south-florida-agency-turns-to-google-public-sector-"
    "to-help-manage-critical-water"
)

SOURCE_URLS = {
    "nasdaq_rare_earth_2026": NASDAQ_RARE_EARTH_BATTLEFIELD_2026,
    "nasdaq_roundhill_weeklypay_etfs_2025": NASDAQ_ROUNDHILL_WEEKLYPAY_ETFS_2025,
    "nasdaq_smart_healthcare_2025": NASDAQ_SMART_HEALTHCARE_2025,
    "nasdaq_quantum_threats_2025": NASDAQ_QUANTUM_THREATS_2025,
    "nasdaq_google_wiz_2025": NASDAQ_GOOGLE_WIZ_2025,
    "nasdaq_artmarket_q3_2024": NASDAQ_ARTMARKET_Q3_2024,
    "nasdaq_cultureamp_google_cloud": NASDAQ_CULTUREAMP_GOOGLE_CLOUD,
    "nasdaq_google_fastly_privacy_sandbox": NASDAQ_GOOGLE_FASTLY_PRIVACY_SANDBOX,
    "nasdaq_google_cloud_ai_retail_2023": NASDAQ_GOOGLE_CLOUD_AI_RETAIL_2023,
    "nasdaq_south_florida_google_public_sector": NASDAQ_SOUTH_FLORIDA_GOOGLE_PUBLIC_SECTOR,
}

PROCESSED_JSONL_PATH = "app/rag/data/processed/processed_docs.jsonl"
PDF_SOURCE_PATHS = ["app/rag/data/raw/google", "app/rag/data/raw/nvidia"]
PLAYWRIGHT_STATE_FILE = "app/rag/data/raw/google/google_storage_state.json"
MIN_DOC_CHARS = 300
QDRANT_COLLECTION = "company_docs"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 160

RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() == "true"
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "10"))
RERANK_MODEL_NAME = os.getenv("RERANK_MODEL_NAME", "BAAI/bge-reranker-base")