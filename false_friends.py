"""
False Friends Finder
Compares two language dictionaries and finds words that look the same
but have different meanings.
"""

import json
import argparse
from pathlib import Path
from difflib import SequenceMatcher


def load_dictionary(path):
    """Load a JSON dictionary file: { "word": "meaning", ... }"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_exact_false_friends(dict_a, dict_b):
    """Words spelled identically but with different meanings."""
    shared = set(dict_a) & set(dict_b)
    return {
        word: {"a": dict_a[word], "b": dict_b[word]}
        for word in shared
        if dict_a[word].lower() != dict_b[word].lower()
    }


def find_fuzzy_false_friends(dict_a, dict_b, threshold=0.85):
    """Words with similar (but not identical) spelling and different meanings."""
    results = []
    for word_a, meaning_a in dict_a.items():
        for word_b, meaning_b in dict_b.items():
            if word_a == word_b:
                continue
            score = SequenceMatcher(None, word_a.lower(), word_b.lower()).ratio()
            if score >= threshold and meaning_a.lower() != meaning_b.lower():
                results.append({
                    "word_a": word_a,
                    "word_b": word_b,
                    "similarity": round(score, 3),
                    "meaning_a": meaning_a,
                    "meaning_b": meaning_b,
                })
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results


def print_results(exact, fuzzy, lang_a, lang_b):
    print(f"\n=== False Friends: {lang_a} vs {lang_b} ===\n")

    if exact:
        print(f"--- Exact matches ({len(exact)}) ---")
        for word, meanings in sorted(exact.items()):
            print(f"  {word!r}")
            print(f"    {lang_a}: {meanings['a']}")
            print(f"    {lang_b}: {meanings['b']}")
    else:
        print("No exact false friends found.")

    if fuzzy:
        print(f"\n--- Near matches ({len(fuzzy)}) ---")
        for item in fuzzy:
            print(f"  {item['word_a']!r} / {item['word_b']!r}  (similarity: {item['similarity']})")
            print(f"    {lang_a}: {item['meaning_a']}")
            print(f"    {lang_b}: {item['meaning_b']}")


def main():
    parser = argparse.ArgumentParser(description="Find false friends between two language dictionaries.")
    parser.add_argument("dict_a", help="Path to first dictionary JSON file")
    parser.add_argument("dict_b", help="Path to second dictionary JSON file")
    parser.add_argument("--lang-a", default="Language A", help="Name of first language")
    parser.add_argument("--lang-b", default="Language B", help="Name of second language")
    parser.add_argument("--fuzzy", action="store_true", help="Also find near-similar words")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="Similarity threshold for fuzzy matching (0-1, default: 0.85)")
    parser.add_argument("--output", help="Save results to a JSON file")
    args = parser.parse_args()

    dict_a = load_dictionary(args.dict_a)
    dict_b = load_dictionary(args.dict_b)

    exact = find_exact_false_friends(dict_a, dict_b)
    fuzzy = find_fuzzy_false_friends(dict_a, dict_b, args.threshold) if args.fuzzy else []

    print_results(exact, fuzzy, args.lang_a, args.lang_b)

    if args.output:
        result = {"exact": exact, "fuzzy": fuzzy}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
