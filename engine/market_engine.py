"""
Market Engine - 3M Model (Mover → Market → Movement)
Provides market data, opportunity calculations, and financial scenarios.
"""

import random
import time
from typing import Dict, List, Optional
from datetime import datetime

# Simulated market instruments
MARKET_DATA = {
    "XAUUSD": {
        "name_ar": "الذهب",
        "name_en": "Gold",
        "symbol": "XAUUSD",
        "icon": "🥇",
        "category": "commodities",
        "price": 2345.50,
        "change_pct": 0.85,
        "spread": 0.25,
        "pip_value": 1.0,
        "contract_size": 100,
        "popular": True
    },
    "XAGUSD": {
        "name_ar": "الفضة",
        "name_en": "Silver",
        "symbol": "XAGUSD",
        "icon": "🥈",
        "category": "commodities",
        "price": 28.75,
        "change_pct": 1.20,
        "spread": 0.03,
        "pip_value": 0.01,
        "contract_size": 5000,
        "popular": False
    },
    "USOIL": {
        "name_ar": "النفط الأمريكي",
        "name_en": "US Oil (WTI)",
        "symbol": "USOIL",
        "icon": "🛢️",
        "category": "commodities",
        "price": 78.30,
        "change_pct": -0.45,
        "spread": 0.03,
        "pip_value": 0.01,
        "contract_size": 1000,
        "popular": True
    },
    "EURUSD": {
        "name_ar": "يورو / دولار",
        "name_en": "EUR/USD",
        "symbol": "EURUSD",
        "icon": "💶",
        "category": "forex",
        "price": 1.0892,
        "change_pct": 0.15,
        "spread": 0.0001,
        "pip_value": 0.0001,
        "contract_size": 100000,
        "popular": True
    },
    "GBPUSD": {
        "name_ar": "جنيه إسترليني / دولار",
        "name_en": "GBP/USD",
        "symbol": "GBPUSD",
        "icon": "💷",
        "category": "forex",
        "price": 1.2715,
        "change_pct": -0.22,
        "spread": 0.0002,
        "pip_value": 0.0001,
        "contract_size": 100000,
        "popular": False
    },
    "NAS100": {
        "name_ar": "مؤشر ناسداك",
        "name_en": "NASDAQ 100",
        "symbol": "NAS100",
        "icon": "📈",
        "category": "indices",
        "price": 18450.00,
        "change_pct": 1.10,
        "spread": 1.0,
        "pip_value": 1.0,
        "contract_size": 1,
        "popular": True
    },
    "SP500": {
        "name_ar": "مؤشر S&P 500",
        "name_en": "S&P 500",
        "symbol": "SP500",
        "icon": "📊",
        "category": "indices",
        "price": 5280.00,
        "change_pct": 0.65,
        "spread": 0.5,
        "pip_value": 1.0,
        "contract_size": 1,
        "popular": False
    },
    "ARAMCO": {
        "name_ar": "أرامكو السعودية",
        "name_en": "Saudi Aramco",
        "symbol": "ARAMCO",
        "icon": "🏢",
        "category": "stocks",
        "price": 29.50,
        "change_pct": 0.34,
        "spread": 0.01,
        "pip_value": 0.01,
        "contract_size": 1,
        "popular": True
    },
    "BTCUSD": {
        "name_ar": "بيتكوين",
        "name_en": "Bitcoin",
        "symbol": "BTCUSD",
        "icon": "₿",
        "category": "crypto",
        "price": 98500.00,
        "change_pct": 2.30,
        "spread": 50.0,
        "pip_value": 1.0,
        "contract_size": 1,
        "popular": True
    }
}

# Economic events that move markets (3M: Movers)
MARKET_MOVERS = [
    {
        "event_ar": "تقرير الوظائف غير الزراعية (NFP)",
        "event_en": "Non-Farm Payrolls (NFP)",
        "impact": "high",
        "affected_markets": ["XAUUSD", "EURUSD", "NAS100", "SP500"],
        "icon": "📋",
        "scenario": {
            "positive": "إذا جاءت الأرقام أفضل من المتوقع: الدولار يرتفع → الذهب ينخفض → الأسهم ترتفع",
            "negative": "إذا جاءت الأرقام أسوأ من المتوقع: الدولار ينخفض → الذهب يرتفع → الأسهم تنخفض"
        },
        "historical_movement": {"XAUUSD": 30, "EURUSD": 80, "NAS100": 200}
    },
    {
        "event_ar": "قرار الفائدة الفيدرالي",
        "event_en": "Federal Reserve Interest Rate Decision",
        "impact": "critical",
        "affected_markets": ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "BTCUSD"],
        "icon": "🏦",
        "scenario": {
            "positive": "خفض الفائدة: الذهب يرتفع بقوة → الدولار ينخفض → الأسهم ترتفع",
            "negative": "رفع الفائدة: الذهب ينخفض → الدولار يرتفع → الأسهم تنخفض"
        },
        "historical_movement": {"XAUUSD": 50, "EURUSD": 120, "NAS100": 350}
    },
    {
        "event_ar": "مخزونات النفط الأمريكية",
        "event_en": "US Crude Oil Inventories",
        "impact": "medium",
        "affected_markets": ["USOIL"],
        "icon": "🛢️",
        "scenario": {
            "positive": "انخفاض المخزونات: النفط يرتفع (طلب أكبر)",
            "negative": "ارتفاع المخزونات: النفط ينخفض (فائض المعروض)"
        },
        "historical_movement": {"USOIL": 3}
    },
    {
        "event_ar": "بيانات التضخم (CPI)",
        "event_en": "Consumer Price Index (CPI)",
        "impact": "high",
        "affected_markets": ["XAUUSD", "EURUSD", "NAS100"],
        "icon": "📈",
        "scenario": {
            "positive": "تضخم أقل من المتوقع: الذهب يرتفع → الأسهم ترتفع (توقعات خفض الفائدة)",
            "negative": "تضخم أعلى من المتوقع: الذهب ينخفض → الأسهم تنخفض (توقعات رفع الفائدة)"
        },
        "historical_movement": {"XAUUSD": 25, "EURUSD": 60, "NAS100": 180}
    }
]


def get_market_data() -> Dict:
    """Get current simulated market data with slight random variations."""
    result = {}
    for symbol, data in MARKET_DATA.items():
        instrument = data.copy()
        # Add slight random price variation for realism
        variation = random.uniform(-0.5, 0.5)
        instrument["price"] = round(data["price"] * (1 + variation / 100), 2)
        instrument["change_pct"] = round(data["change_pct"] + random.uniform(-0.3, 0.3), 2)
        instrument["last_update"] = datetime.now().isoformat()
        result[symbol] = instrument
    return result


def detect_asset_mention(text: str) -> List[Dict]:
    """Detect financial asset mentions in Arabic text."""
    asset_keywords = {
        "XAUUSD": ["ذهب", "الذهب", "gold", "أونصة", "أونصات"],
        "USOIL": ["نفط", "النفط", "بترول", "oil", "خام"],
        "EURUSD": ["يورو", "اليورو", "eur"],
        "GBPUSD": ["جنيه", "إسترليني", "باوند", "gbp"],
        "NAS100": ["ناسداك", "nasdaq", "التكنولوجيا"],
        "SP500": ["إس أند بي", "s&p"],
        "ARAMCO": ["أرامكو", "aramco", "السعودية"],
        "BTCUSD": ["بيتكوين", "bitcoin", "عملة رقمية", "كريبتو"],
        "XAGUSD": ["فضة", "الفضة", "silver"],
    }

    detected = []
    text_lower = text.lower()
    for symbol, keywords in asset_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                instrument = MARKET_DATA[symbol].copy()
                detected.append(instrument)
                break

    return detected


def calculate_3m_opportunity(symbol: str, investment_usd: float = 1000, leverage: int = 100) -> Optional[Dict]:
    """
    Calculate a 3M opportunity card:
    Mover → Market → Movement → Potential Profit/Loss
    """
    if symbol not in MARKET_DATA:
        return None

    instrument = MARKET_DATA[symbol]

    # Find relevant movers
    relevant_movers = [m for m in MARKET_MOVERS if symbol in m["affected_markets"]]
    if not relevant_movers:
        relevant_movers = [MARKET_MOVERS[0]]  # Default to NFP

    mover = relevant_movers[0]
    expected_movement = mover["historical_movement"].get(symbol, 10)

    # Calculate potential profit
    effective_capital = investment_usd * leverage
    if symbol == "XAUUSD":
        # Gold: movement in $ per ounce, 100 oz per lot
        lots = effective_capital / (instrument["price"] * 100)
        potential_profit = lots * expected_movement * 100
    elif symbol in ["EURUSD", "GBPUSD"]:
        # Forex: movement in pips
        lots = effective_capital / instrument["contract_size"]
        potential_profit = lots * expected_movement * 10
    elif symbol in ["NAS100", "SP500"]:
        # Indices: movement in points
        lots = effective_capital / (instrument["price"] * instrument["contract_size"])
        potential_profit = lots * expected_movement
    else:
        lots = effective_capital / (instrument["price"] * instrument["contract_size"])
        potential_profit = lots * expected_movement * instrument["contract_size"]

    return {
        "mover": {
            "event_ar": mover["event_ar"],
            "event_en": mover["event_en"],
            "impact": mover["impact"],
            "icon": mover["icon"]
        },
        "market": {
            "symbol": symbol,
            "name_ar": instrument["name_ar"],
            "name_en": instrument["name_en"],
            "current_price": instrument["price"],
            "icon": instrument["icon"]
        },
        "movement": {
            "expected_points": expected_movement,
            "scenario_positive": mover["scenario"]["positive"],
            "scenario_negative": mover["scenario"]["negative"]
        },
        "calculation": {
            "investment": investment_usd,
            "leverage": f"1:{leverage}",
            "effective_capital": effective_capital,
            "potential_profit": round(potential_profit, 2),
            "potential_loss": round(potential_profit * 0.5, 2),
            "risk_reward": "1:2"
        },
        "pitch_ar": f"إذا استثمرت {investment_usd}$ برافعة 1:{leverage} في {instrument['name_ar']}، وتحرّك السعر {expected_movement} نقطة كما حصل تاريخياً عند صدور {mover['event_ar']}، فإن ربحك المحتمل يصل إلى {round(potential_profit, 2)}$ 🎯"
    }


def get_trending_assets() -> List[Dict]:
    """Get currently trending assets sorted by absolute change."""
    data = get_market_data()
    sorted_assets = sorted(data.values(), key=lambda x: abs(x["change_pct"]), reverse=True)
    return sorted_assets[:5]
