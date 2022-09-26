from pathlib import Path

APP_IDS = {
    'DOTA': 570,
    'CSGO': 730,
    'RUST': 252490
}

LINK_MARKET = 'https://steamcommunity.com/market/priceoverview/?appid={app_id}&currency=1&market_hash_name={market_hash_name}'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
}

PATH_MAIN = str(Path(__file__).parent)

SYSTEM = 'LINUX'
