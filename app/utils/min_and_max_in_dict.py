def get_item_bounds(min_key, max_key, items):
    return {
            "min": min(item[min_key] for item in items),
            "max": max(item[max_key] for item in items)
        }