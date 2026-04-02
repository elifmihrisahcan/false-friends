"""
False Friends Finder
Compares two language dictionaries and finds words that look the same
but have different meanings.
"""

import json


def load_dictionary(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_false_friends(dict_a, dict_b):
    shared = set(dict_a) & set(dict_b)
    return {
        word: {"a": dict_a[word], "b": dict_b[word]}
        for word in shared
        if dict_a[word].lower() != dict_b[word].lower()
    }


def print_results(false_friends, lang_a, lang_b):
    print(f"\n=== False Friends: {lang_a} vs {lang_b} ===\n")
    if not false_friends:
        print("No false friends found.")
        return
    for word, meanings in sorted(false_friends.items()):
        print(f"  {word}")
        print(f"    {lang_a}: {meanings['a']}")
        print(f"    {lang_b}: {meanings['b']}")


if __name__ == "__main__":
    lang_a = input("Language A name: ").strip()
    path_a = input(f"Path to {lang_a} dictionary: ").strip()
    lang_b = input("Language B name: ").strip()
    path_b = input(f"Path to {lang_b} dictionary: ").strip()

    dict_a = load_dictionary(path_a)
    dict_b = load_dictionary(path_b)

    false_friends = find_false_friends(dict_a, dict_b)
    print_results(false_friends, lang_a, lang_b)
