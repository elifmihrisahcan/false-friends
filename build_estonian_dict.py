"""
Builds an Estonian dictionary JSON from English Wiktionary.
Output format: { "word": "first meaning (in English)", ... }
"""

import json
import time
import re
import urllib.request
import urllib.parse

CATEGORY_URL = (
    "https://en.wiktionary.org/w/api.php"
    "?action=query&list=categorymembers"
    "&cmtitle=Category:Estonian_lemmas"
    "&cmlimit=500&format=json&cmcontinue={}"
)
DEFINITION_URL = "https://en.wiktionary.org/api/rest_v1/page/definition/{}"
OUTPUT_FILE = "dictionaries/estonian_full.json"
DELAY = 0.5


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()


def get_all_words():
    words = []
    cmcontinue = ""
    while True:
        data = fetch_json(CATEGORY_URL.format(urllib.parse.quote(cmcontinue)))
        words += [e["title"] for e in data["query"]["categorymembers"]]
        if "continue" not in data:
            break
        cmcontinue = data["continue"]["cmcontinue"]
        time.sleep(0.2)
    return words


def get_meaning(word):
    url = DEFINITION_URL.format(urllib.parse.quote(word))
    try:
        data = fetch_json(url)
    except Exception:
        return None
    et_entries = data.get("et", [])
    if not et_entries:
        return None
    definitions = et_entries[0].get("definitions", [])
    if not definitions:
        return None
    return strip_html(definitions[0]["definition"])


def main():
    print("Fetching Estonian word list from Wiktionary...")
    words = get_all_words()
    print(f"Found {len(words)} words. Building dictionary...")

    dictionary = {}
    for i, word in enumerate(words, 1):
        meaning = get_meaning(word)
        if meaning:
            dictionary[word] = meaning
        if i % 100 == 0:
            print(f"  {i}/{len(words)} — last: {word!r}")
        time.sleep(DELAY)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(dictionary)} entries saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
