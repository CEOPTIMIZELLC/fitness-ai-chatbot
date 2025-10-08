def longest_string_size_for_key(items, key):
    if len(items) == 0:
        return 0
    return len(max(items, key=lambda d:len(d[key]))[key])