import config


def filter_items(app_id: int, items: dict):
    _items = []

    if app_id == config.APP_IDS.get('CSGO'):

        for item in items:
            market_name = item.get("market_name")
            if 'medal' in market_name.lower():
                _items.append(item)

    else:
        _items.extend(items)

    return _items
