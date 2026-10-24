"""Builds ../index.html (French booster pack tracker) from template.html + src/.

src/pp_boosters.json   Poképédia booster image files (Booster_<Série>_<Extension>_<Pokémon>.png), via its API
src/fr_sets_full.json  TCGdex French sets (names, dates, abbreviations, series)
src/en_sets.json       TCGdex English set names, used to find the Cardmarket booster product
src/extra.json         manual corrections: skipped files, sets TCGdex lacks, McDonald's / Play! packs, extra artworks
src/icon.png           home-screen icon
Downloaded on each run (not committed): src/ns.json and src/pg.json, Cardmarket sealed product list and price guide.

    python build.py             refresh Poképédia list + Cardmarket prices, then build
    python build.py --offline   rebuild from the files already in src/
"""
import json, os, re, sys, unicodedata, urllib.request, urllib.parse, base64
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OFFLINE = "--offline" in sys.argv
def jload(n):
    with open(os.path.join(SRC, n), encoding="utf-8") as f: return json.load(f)
def jsave(n, d):
    with open(os.path.join(SRC, n), "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=0)

def fetch_poked():
    out, cont = [], {}
    while True:
        q = {"action": "query", "list": "allimages", "aiprefix": "Booster", "ailimit": "500", "aiprop": "url|size", "format": "json", **cont}
        req = urllib.request.Request("https://www.pokepedia.fr/api.php?" + urllib.parse.urlencode(q), headers={"User-Agent": "boosters-fr/1.0"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        out += d["query"]["allimages"]
        if "continue" not in d: return out
        cont = d["continue"]

if not OFFLINE:
    print("Poképédia…"); jsave("pp_boosters.json", fetch_poked())
for url, name in (("https://downloads.s3.cardmarket.com/productCatalog/productList/products_nonsingles_6.json", "ns.json"),
                  ("https://downloads.s3.cardmarket.com/productCatalog/priceGuide/price_guide_6.json", "pg.json")):
    if not OFFLINE or not os.path.exists(os.path.join(SRC, name)):
        print("Cardmarket", name, "…"); urllib.request.urlretrieve(url, os.path.join(SRC, name))

FILES = jload("pp_boosters.json")
FR_SETS = [s for s in jload("fr_sets_full.json") if "_err" not in s]
EN_NAME = {s["id"]: s["name"] for s in jload("en_sets.json")}
EXTRA = jload("extra.json")
NS = [p for p in jload("ns.json")["products"] if p["categoryName"] == "Pokémon Booster"]
PG = {p["idProduct"]: p for p in jload("pg.json")["priceGuides"]}
CM_BY_NAME = {}
for p in NS: CM_BY_NAME.setdefault(p["name"].lower(), p["idProduct"])

def norm(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode())

# Sets that sell boosters: TCGdex French sets minus TCG Pocket, promos, kits, McDonald's (handled in extra.json), sub-sets
NOT_BOOSTER = re.compile(r"^(A\d|B\d|P-|wp|np|.*p$|tk-|\d{4}|jumbo|xya|sve|mee|cel25cc|30th-c|sma|swsh4\.5sv|.*tg$|swsh12\.5gg|exu|rc|mfb)")
SKIP_SETS = set(EXTRA["skip_sets"])
SETS = {}
for s in FR_SETS:
    if NOT_BOOSTER.match(s["id"]) or s["id"] in SKIP_SETS: continue
    SETS[s["id"]] = {"id": s["id"], "name": s["name"], "serie": (s.get("serie") or {}).get("name") or "", "date": s.get("releaseDate") or "",
                     "abbr": (s.get("abbreviation") or {}).get("official"), "loc": (s.get("abbreviation") or {}).get("localized")}
for s in EXTRA["sets"]:
    SETS[s["id"]] = {**{"abbr": None, "loc": None}, **s}
for sid, d in EXTRA.get("fr_dates", {}).items():  # French release dates (TCGdex has US dates for older sets)
    if sid in SETS: SETS[sid]["date"] = d

# Poképédia file name -> set: longest "<série> <extension>" prefix, accents and punctuation ignored
PREFIX = ["", "ecarlateetviolet", "epeeetbouclier", "soleiletlune", "xy", "noirblanc", "hs", "platine", "diamantperle", "megaevolution", "ex"]
KEYS = {}
for sid, s in SETS.items():
    for p in PREFIX: KEYS[p + norm(s["name"])] = sid
KEYS.update({"heartgoldsoulsilver": "hgss1", "hstriomphe": "hgss4", "lappeldeslegendes": "col1", "diamantperleduelsausommet": "dp4",
             "noirblancdragonsexaltes": "bw6", "noirblanctempeteplasma": "bw8", "diamantperletempete": "dp7",
             "platinevainqueurssupremes": "pl3", "platinerivauxemergeants": "pl2", "ecarlateetviolet151": "sv03.5",
             "xyevolutions": "xy12", "megaevolutionherostranscendants": "me02.5"})
SKIP_FILE = re.compile("|".join(EXTRA["skip_files"]), re.I)

def variant_of(art):
    if re.search(r"Échantillon", art): return "", "Booster échantillon"
    if re.search(r"Avant-première", art): return "", "Booster avant-première"
    m = re.search(r"\s*-\s*Édition 1$", art)
    if m: return art[:m.start()], "1re édition"
    return art, ""

PACKS = []
for f in FILES:
    fn = f["name"]
    if SKIP_FILE.search(fn): continue
    if fn in EXTRA["file_map"]:
        sid, art = EXTRA["file_map"][fn]
    else:
        name = re.sub(r"^Booster_", "", fn.rsplit(".", 1)[0])
        for pre, psid in EXTRA["prefix_map"].items():
            if name.startswith(pre): sid, art = psid, name[len(pre):].replace("_", " "); break
        else:
            toks, best = name.split("_"), None
            for i in range(1, len(toks) + 1):
                k = norm(" ".join(toks[:i]))
                if k in KEYS: best = (i, KEYS[k])
            if not best: continue  # Japanese, TCG Pocket or English-only product
            sid, art = best[1], " ".join(toks[best[0]:]).strip() or "(visuel unique)"
    if sid not in SETS: continue
    art, v = variant_of(art)
    if not v and EXTRA["samples"].get(sid) == art: v = "Booster échantillon"
    PACKS.append({"set": sid, "art": art or "(visuel unique)", "v": v, "img": f["url"], "w": f.get("width"), "h": f.get("height")})
for e in EXTRA["extra_packs"]:
    PACKS.append({k: val for k, val in e.items() if val is not None})

# French Wizards sets were printed in "1re édition" and "Illimitée": label each Poképédia image with its edition and add
# the other edition with the same illustration (or a dedicated image when one is known)
other = {"1re édition": "Illimitée", "Illimitée": "1re édition"}
for sid, eds in EXTRA["editions"].items():
    regular = [p for p in PACKS if p["set"] == sid and p["v"] in ("", "1re édition")]
    for p in regular:
        if not p["v"]: p["v"] = eds.get(p["art"]) or eds.get("*") or "Illimitée"
    for p in list(regular):
        ov = other[p["v"]]
        if any(q["set"] == sid and q["art"] == p["art"] and q["v"] == ov for q in PACKS): continue
        key = f"{sid}:{p['art']}:{ov}"
        img = EXTRA["edition_images"].get(key)
        q = {"set": sid, "art": p["art"], "v": ov, "img": img or p["img"]}
        if not img: q["note"] = f"Image de la version {p['v'].lower()} : même illustration."
        if f"{sid}:{p['art']}" in EXTRA["edition_uncertain"]: q["u"] = 1
        PACKS.append(q)
for p in PACKS:
    n = EXTRA["image_notes"].get(f"{p['set']}:{p['art']}")
    if n and not p.get("note") and p["v"] in ("", "Illimitée", "1re édition"): p["note"] = n
drop = {(d["set"], d["art"]) for d in EXTRA["drop_packs"]}
PACKS = [p for p in PACKS if (p["set"], p["art"]) not in drop]

VORDER = {"": 0, "1re édition": 0, "Illimitée": 0, "Booster avant-première": 2, "Booster échantillon": 3, "Pack Loisir (échantillon)": 4}
by_set = defaultdict(list)
for p in PACKS: by_set[p["set"]].append(p)
GROUPS, CARDS = [], []
for sid, ps in by_set.items():
    s = SETS[sid]
    ps.sort(key=lambda p: (VORDER.get(p["v"], 9), norm(p["art"]) if p["art"] != "(visuel unique)" else "", p["v"] != "1re édition"))
    cm_name = s.get("cm") or EXTRA["cm_names"].get(sid) or (f"{EN_NAME[sid]} Booster" if sid in EN_NAME else None)
    cm = CM_BY_NAME.get(cm_name.lower()) if cm_name else None
    if not cm and sid in EN_NAME:  # EX sets are listed as "EX <name> Booster" on Cardmarket
        cm = CM_BY_NAME.get(f"ex {EN_NAME[sid]} booster".lower())
    g = {"id": sid, "t": s["name"], "serie": s["serie"], "date": s["date"], "y": int((s["date"] or "0000")[:4]),
         "c": s.get("abbr"), "lc": s.get("loc")}
    if s.get("upcoming"): g["up"] = 1
    if cm in PG: g["cm"] = cm
    GROUPS.append(g)
    seen = {}
    for i, p in enumerate(ps):
        pid = f"{sid}:{norm(p['art']) or 'unique'}" + (f":{norm(p['v'])}" if p["v"] else "")
        if pid in seen: seen[pid] += 1; pid += f"-{seen[pid]}"
        else: seen[pid] = 0
        c = {"id": pid, "g": sid, "a": p["art"], "img": p["img"], "o": i}
        if p["v"]: c["v"] = p["v"]
        if p.get("u"): c["u"] = 1
        if p.get("note"): c["note"] = p["note"]
        CARDS.append(c)
GROUPS.sort(key=lambda g: (g["date"] or "9999", g["id"]))
for i, g in enumerate(GROUPS): g["o"] = i

PRICES = {g["cm"]: [PG[g["cm"]].get("avg"), PG[g["cm"]].get("trend"), PG[g["cm"]].get("low")] for g in GROUPS if "cm" in g}
data = ("const SNAP_DATE = " + json.dumps(jload("pg.json").get("createdAt", "")[:10]) + ";\n"
        "const GROUPS = " + json.dumps(GROUPS, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "const CARDS = " + json.dumps(CARDS, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "const PRICES = " + json.dumps(PRICES, separators=(",", ":")) + ";")
with open(os.path.join(HERE, "template.html"), encoding="utf-8") as f: tpl = f.read()
with open(os.path.join(SRC, "icon.png"), "rb") as f: icon = "data:image/png;base64," + base64.b64encode(f.read()).decode()
with open(os.path.join(HERE, "..", "index.html"), "w", encoding="utf-8") as f: f.write(tpl.replace("/*__DATA__*/", data).replace("__ICON__", icon))
print("sets", len(GROUPS), "boosters", len(CARDS), "priced sets", len(PRICES))
missing = sorted(s for s in SETS if s not in by_set)
if missing: print("sets without any booster artwork:", missing)
