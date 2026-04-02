"""
Mushroom Forager
A field tool for mushroom identification, foraging calendars, and edibility safety.

Usage:
  python mushroom_forager.py identify --cap-color yellow --habitat oak --spore-print white
  python mushroom_forager.py calendar --region pacific-northwest --month 10
  python mushroom_forager.py safety chanterelle
  python mushroom_forager.py list
"""

import json
import argparse
from pathlib import Path


EDIBILITY_ORDER = {
    "deadly": 0,
    "toxic": 1,
    "unknown": 2,
    "edible": 3,
    "choice": 4,
}

EDIBILITY_LABEL = {
    "choice":  "CHOICE EDIBLE",
    "edible":  "EDIBLE",
    "unknown": "UNKNOWN — do not eat",
    "toxic":   "TOXIC",
    "deadly":  "DEADLY",
}

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

VALID_REGIONS = [
    "north-america", "europe", "pacific-northwest", "northeast-us",
    "southeast-us", "midwest-us", "uk", "central-europe",
]


def load_database(path=None):
    if path is None:
        path = Path(__file__).parent / "data" / "mushrooms.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["species"]


# ---------------------------------------------------------------------------
# Identify
# ---------------------------------------------------------------------------

TRAIT_KEYS = [
    "cap_color", "cap_shape", "gill_type", "gill_color",
    "stem_color", "spore_print", "habitat", "smell", "flesh_color",
]


def score_species(species, query_traits):
    """
    Score a species against the provided traits.
    Returns (score, total_provided) where score counts matching traits.
    """
    traits = species["traits"]
    matches = 0
    provided = 0

    for key, value in query_traits.items():
        if value is None:
            continue
        provided += 1
        candidates = [c.lower() for c in traits.get(key, [])]
        query_val = value.lower()
        if any(query_val in c or c in query_val for c in candidates):
            matches += 1

    return matches, provided


def cmd_identify(args, species_list):
    query = {
        "cap_color":   args.cap_color,
        "cap_shape":   args.cap_shape,
        "gill_type":   args.gill_type,
        "gill_color":  args.gill_color,
        "stem_color":  args.stem_color,
        "spore_print": args.spore_print,
        "habitat":     args.habitat,
        "smell":       args.smell,
        "flesh_color": args.flesh_color,
    }

    provided = sum(1 for v in query.values() if v is not None)
    if provided == 0:
        print("Please provide at least one trait. Run with --help for options.")
        return

    results = []
    for sp in species_list:
        matches, _ = score_species(sp, query)
        if matches > 0:
            pct = round(matches / provided * 100)
            results.append((pct, matches, sp))

    results.sort(key=lambda x: (-x[0], x[2]["common_name"]))

    if not results:
        print("\nNo matches found. Try fewer or different traits.")
        return

    print(f"\n=== Identification Results ({provided} trait(s) provided) ===\n")
    for pct, matches, sp in results[:args.top]:
        edibility = sp["edibility"]
        label = EDIBILITY_LABEL[edibility]
        bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
        print(f"  [{bar}] {pct:3d}%  {sp['common_name']}")
        print(f"          {sp['latin_name']}")
        print(f"          Status: {label}")
        if edibility in ("deadly", "toxic"):
            print(f"          !! WARNING: {sp['warning']}")
        elif sp.get("look_alikes"):
            look_alikes = ", ".join(sp["look_alikes"])
            print(f"          Look-alikes: {look_alikes}")
        print()

    deadly_in_results = [sp for _, _, sp in results[:args.top] if sp["edibility"] == "deadly"]
    if deadly_in_results:
        print("  *** SAFETY NOTICE: Deadly species appear in your results.")
        print("  *** Never eat a mushroom based solely on this tool. Verify with")
        print("  *** multiple field guides and an expert before consuming anything.\n")


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

def cmd_calendar(args, species_list):
    month = args.month
    region = args.region.lower()

    if region not in VALID_REGIONS:
        print(f"Unknown region '{region}'. Valid regions: {', '.join(VALID_REGIONS)}")
        return

    in_season = [
        sp for sp in species_list
        if month in sp["season"] and region in sp["regions"]
    ]

    if not in_season:
        print(f"\nNo species found for {MONTH_NAMES[month]} in {region}.")
        return

    # Sort: deadly/toxic first (as warnings), then choice, then edible
    in_season.sort(key=lambda sp: (EDIBILITY_ORDER[sp["edibility"]], sp["common_name"]))

    print(f"\n=== Foraging Calendar: {MONTH_NAMES[month]} in {region} ===\n")

    edible = [sp for sp in in_season if sp["edibility"] in ("choice", "edible")]
    caution = [sp for sp in in_season if sp["edibility"] in ("unknown",)]
    danger = [sp for sp in in_season if sp["edibility"] in ("toxic", "deadly")]

    if edible:
        print(f"  --- Edible species ({len(edible)}) ---")
        for sp in edible:
            label = EDIBILITY_LABEL[sp["edibility"]]
            season_str = ", ".join(MONTH_NAMES[m] for m in sp["season"])
            print(f"  * {sp['common_name']} ({sp['latin_name']})")
            print(f"    Status: {label}")
            print(f"    Season: {season_str}")
            if sp.get("look_alikes"):
                print(f"    Watch out for: {', '.join(sp['look_alikes'])}")
            print()

    if caution:
        print(f"  --- Unknown edibility ({len(caution)}) ---")
        for sp in caution:
            print(f"  ? {sp['common_name']} ({sp['latin_name']}) — do not eat")
        print()

    if danger:
        print(f"  --- DANGEROUS species also fruiting ({len(danger)}) ---")
        print("  ! Be aware of these when foraging this month:\n")
        for sp in danger:
            label = EDIBILITY_LABEL[sp["edibility"]]
            print(f"  ! {sp['common_name']} ({sp['latin_name']})  [{label}]")
            print(f"    {sp['warning']}")
            print()


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

def cmd_safety(args, species_list):
    query = args.name.lower().replace(" ", "-").replace("_", "-")

    matches = [
        sp for sp in species_list
        if query in sp["id"]
        or query in sp["common_name"].lower()
        or query in sp["latin_name"].lower()
    ]

    if not matches:
        print(f"\nNo species found matching '{args.name}'.")
        print("Try: python mushroom_forager.py list")
        return

    for sp in matches:
        edibility = sp["edibility"]
        label = EDIBILITY_LABEL[edibility]
        season_str = ", ".join(MONTH_NAMES[m] for m in sp["season"])
        regions_str = ", ".join(sp["regions"])

        print(f"\n{'=' * 60}")
        print(f"  {sp['common_name']}")
        print(f"  {sp['latin_name']}")
        print(f"{'=' * 60}")
        print(f"\n  Edibility : {label}")
        print(f"  Season    : {season_str}")
        print(f"  Regions   : {regions_str}")

        print(f"\n  Key Traits:")
        for key, values in sp["traits"].items():
            label_key = key.replace("_", " ").capitalize()
            print(f"    {label_key:14s}: {', '.join(values)}")

        if sp.get("look_alikes"):
            print(f"\n  Look-alikes: {', '.join(sp['look_alikes'])}")

        if sp.get("warning"):
            print(f"\n  !! WARNING:")
            # Wrap warning text at 60 chars
            words = sp["warning"].split()
            line = "     "
            for word in words:
                if len(line) + len(word) + 1 > 62:
                    print(line)
                    line = "     " + word
                else:
                    line += (" " if line.strip() else "") + word
            if line.strip():
                print(line)

        if sp.get("notes"):
            print(f"\n  Notes: {sp['notes']}")

        print()


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def cmd_list(args, species_list):
    sorted_species = sorted(species_list, key=lambda sp: (EDIBILITY_ORDER[sp["edibility"]], sp["common_name"]))
    print("\n=== Species in Database ===\n")
    for sp in sorted_species:
        label = EDIBILITY_LABEL[sp["edibility"]]
        print(f"  {sp['id']:30s}  {sp['common_name']:30s}  [{label}]")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Mushroom Forager — identify by traits, browse foraging calendars, check edibility safety.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python mushroom_forager.py identify --cap-color yellow --habitat oak --spore-print white
  python mushroom_forager.py identify --cap-color orange --gill-type "true gills" --habitat "dead wood"
  python mushroom_forager.py calendar --region pacific-northwest --month 10
  python mushroom_forager.py calendar --region europe --month 5
  python mushroom_forager.py safety chanterelle
  python mushroom_forager.py safety "death cap"
  python mushroom_forager.py list

regions:
  north-america, europe, pacific-northwest, northeast-us,
  southeast-us, midwest-us, uk, central-europe
        """
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # identify
    id_p = sub.add_parser("identify", help="Identify a mushroom by its traits")
    id_p.add_argument("--cap-color",   help="Cap color (e.g. yellow, red, brown, white)")
    id_p.add_argument("--cap-shape",   help="Cap shape (e.g. convex, flat, funnel-shaped, shelf)")
    id_p.add_argument("--gill-type",   help="Gill type (e.g. 'true gills', 'false gills', 'pores', 'ridges', 'spines')")
    id_p.add_argument("--gill-color",  help="Gill color (e.g. white, pink, orange)")
    id_p.add_argument("--stem-color",  help="Stem color or features (e.g. white, ring, hollow)")
    id_p.add_argument("--spore-print", help="Spore print color (e.g. white, brown, black, pale yellow)")
    id_p.add_argument("--habitat",     help="Growing habitat (e.g. oak, dead wood, grassland, pine)")
    id_p.add_argument("--smell",       help="Smell (e.g. fruity, earthy, unpleasant, anise)")
    id_p.add_argument("--flesh-color", help="Flesh color when cut (e.g. white, yellow, blues)")
    id_p.add_argument("--top",         type=int, default=5, help="Show top N matches (default: 5)")

    # calendar
    cal_p = sub.add_parser("calendar", help="Show what's fruiting by region and month")
    cal_p.add_argument("--region", required=True, help=f"Region ({', '.join(VALID_REGIONS)})")
    cal_p.add_argument("--month",  required=True, type=int, choices=range(1, 13),
                       metavar="MONTH", help="Month number (1-12)")

    # safety
    saf_p = sub.add_parser("safety", help="Full safety profile for a named species")
    saf_p.add_argument("name", help="Common or latin name (e.g. chanterelle, 'death cap')")

    # list
    sub.add_parser("list", help="List all species in the database")

    args = parser.parse_args()

    try:
        species_list = load_database()
    except FileNotFoundError:
        print("Error: data/mushrooms.json not found. Make sure you run from the project directory.")
        return

    if args.command == "identify":
        cmd_identify(args, species_list)
    elif args.command == "calendar":
        cmd_calendar(args, species_list)
    elif args.command == "safety":
        cmd_safety(args, species_list)
    elif args.command == "list":
        cmd_list(args, species_list)


if __name__ == "__main__":
    main()
