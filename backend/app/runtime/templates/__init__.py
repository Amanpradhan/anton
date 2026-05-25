from app.runtime.templates.competitive_intel import TEMPLATE as COMPETITIVE_INTEL
from app.runtime.templates.market_digest import TEMPLATE as MARKET_DIGEST

TEMPLATES: dict[str, dict] = {
    COMPETITIVE_INTEL["id"]: COMPETITIVE_INTEL,
    MARKET_DIGEST["id"]: MARKET_DIGEST,
}

__all__ = ["TEMPLATES"]
