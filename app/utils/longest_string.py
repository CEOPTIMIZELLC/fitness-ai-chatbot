def longest_string_size_for_key(items, key):
    return len(max(items, key=lambda d:len(d[key]))[key])