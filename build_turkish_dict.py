"""
Builds a Turkish dictionary JSON from sozluk.gov.tr (TDK).
Output format: { "word": "first meaning", ... }
"""

import json
import time
import urllib.request
import urllib.parse

AUTOCOMPLETE_URL = "https://sozluk.gov.tr/autocomplete.json"
LOOKUP_URL = "https://sozluk.gov.tr/gts?ara={}"
OUTPUT_FILE = "dictionaries/turkish_full.json"
DELAY = 0.3  # seconds between requests to be polite


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def get_all_words():
    data = fetch_json(AUTOCOMPLETE_URL)
    return [entry["madde"] for entry in data if "madde" in entry]


def get_meaning(word):
    url = LOOKUP_URL.format(urllib.parse.quote(word))
    data = fetch_json(url)
    if not data or not isinstance(data, list):
        return None
    entry = data[0]
    meanings = entry.get("anlamlarListe", [])
    if not meanings:
        return None
    return meanings[0].get("anlam")


def main():
    print("Fetching word list...")
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
