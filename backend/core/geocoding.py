"""
Ghana City/Region Geocoding Lookup
====================================
Approximate lat/lng centroids for cities and regions in Ghana.
Used by the preprocessing pipeline when no coordinates exist in the CSV.
"""

# Major Ghana cities with approximate coordinates
# Sources: OpenStreetMap, Google Maps, Wikipedia
GHANA_CITY_COORDS = {
    # ── Greater Accra ──
    "accra": (5.6037, -0.1870),
    "accra central": (5.5500, -0.2100),
    "accra newtown": (5.5600, -0.2150),
    "tema": (5.6698, -0.0166),
    "tema community 22": (5.6500, -0.0100),
    "ashaiman": (5.6931, -0.0424),
    "madina": (5.6730, -0.1670),
    "nungua": (5.5935, -0.0780),
    "labadi": (5.5610, -0.1488),
    "cantonments": (5.5768, -0.1721),
    "osu": (5.5571, -0.1818),
    "east legon": (5.6344, -0.1567),
    "adenta": (5.7144, -0.1612),
    "adenta municipality": (5.7144, -0.1612),
    "adenta-fafraha": (5.7250, -0.1550),
    "adentan": (5.7144, -0.1612),
    "achimota": (5.6300, -0.2300),
    "dome": (5.6500, -0.2200),
    "haatso": (5.6600, -0.2100),
    "agbogba": (5.6700, -0.2000),
    "lapaz": (5.6100, -0.2400),
    "dansoman": (5.5600, -0.2509),
    "north kaneshie": (5.5800, -0.2400),
    "kwashieman": (5.5900, -0.2500),
    "odorkor": (5.5800, -0.2600),
    "teshie": (5.5800, -0.1050),
    "nima": (5.5800, -0.1900),
    "maamobi": (5.5750, -0.1960),
    "james town": (5.5347, -0.2119),
    "mataheko": (5.5438, -0.2150),
    "ridge": (5.5680, -0.1980),
    "tesano": (5.5950, -0.2300),
    "dzorwulu": (5.6060, -0.1980),
    "north legon": (5.6700, -0.1850),
    "legon": (5.6500, -0.1860),
    "abelenkpe, accra": (5.5900, -0.1920),
    "kasoa": (5.5350, -0.4163),
    "amasaman": (5.6900, -0.3100),
    "weija": (5.5580, -0.3340),
    "new weija": (5.5600, -0.3400),
    "dodowa": (5.8700, -0.0950),
    "pokoase": (5.7000, -0.2800),
    "new ashongman": (5.7050, -0.1700),
    "ashale-botwe": (5.6900, -0.1400),
    "oyarifa": (5.7100, -0.1300),
    "klagon": (5.6850, -0.0350),
    "agbogbloshie": (5.5480, -0.2250),
    "kordiabe": (5.8600, -0.0700),
    "darkuman-nyamekye": (5.5700, -0.2450),
    "simpa": (5.5300, -0.3500),
    "somanya": (6.1000, -0.0150),
    "mempeasem": (5.6500, -0.1550),
    "gomaa buduburam": (5.5100, -0.4100),
    "greater accra": (5.6037, -0.1870),

    # ── Ashanti Region ──
    "kumasi": (6.6885, -1.6244),
    "obuasi": (6.2060, -1.6630),
    "ejisu": (6.7310, -1.4680),
    "ejura": (7.3870, -1.3640),
    "agogo": (6.8000, -1.0800),
    "bekwai": (6.4581, -1.5740),
    "juaben": (6.7200, -1.4500),
    "mampong": (7.0660, -1.4000),
    "kokofu": (6.5500, -1.4800),
    "konongo": (6.6150, -1.2130),
    "kwadaso": (6.7000, -1.6600),
    "atonsu kumasi": (6.6500, -1.6400),
    "tanoso": (6.7300, -1.6800),
    "santasi": (6.6700, -1.6500),
    "offinso": (7.0700, -1.6600),
    "kuntanase": (6.5200, -1.5000),
    "jamasi": (6.8600, -1.4700),
    "tepa": (7.0200, -2.0000),
    "mankranso": (6.8300, -1.7200),
    "agona ashanti": (6.5900, -1.5800),
    "kumawu": (6.8800, -1.2500),
    "juaso": (6.5400, -1.1200),
    "asokore": (6.7100, -1.5900),
    "asokore mampong": (6.7100, -1.5900),
    "tikrom": (6.7400, -1.5700),
    "ahodwo": (6.6700, -1.6400),
    "pramso": (6.5000, -1.5500),
    "pramiso": (6.5000, -1.5500),
    "nsuta": (6.8200, -1.5000),
    "dompoase": (6.5800, -1.6000),
    "donyina": (6.8000, -1.3500),
    "sekyere": (7.0000, -1.4000),
    "apaaso": (6.7800, -1.5600),
    "wamasi": (6.9000, -1.5000),
    "apinkra": (6.7500, -1.2000),
    "drobonso": (7.3000, -1.2000),
    "nyinamponase": (6.7000, -1.6000),
    "jacobu": (6.4700, -1.5000),
    "boamadumasi": (6.8500, -1.5500),
    "oseikojokrom": (6.7100, -1.6400),
    "kronum": (6.7400, -1.5900),
    "buokrom": (6.7000, -1.6100),
    "wiamoase": (6.8000, -1.4200),
    "akrofrom": (6.6900, -1.6300),
    "akwatialine": (6.6900, -1.6200),
    "nkenkaso": (6.8500, -1.7000),
    "yabraso": (6.7500, -1.5800),
    "kasei (via ejura)": (7.3500, -1.3000),
    "ahimakrom": (6.7200, -1.6000),
    "asamang": (6.7300, -1.5200),
    "kwabeng": (6.5200, -0.9800),
    "anyinasuso": (6.7500, -1.6000),
    "anyinasusu": (6.7500, -1.6000),
    "kumasi metropolitan": (6.6885, -1.6244),

    # ── Western Region ──
    "takoradi": (4.8981, -1.7450),
    "sekondi": (4.9340, -1.7130),
    "tarkwa": (5.3009, -1.9940),
    "axim": (4.8700, -2.2400),
    "bogoso": (5.5400, -2.0000),
    "bibiani": (6.4600, -2.3200),
    "eikwe": (4.8800, -2.2700),
    "nkwanta": (8.2600, -0.5000),
    "enchi": (5.8200, -2.8400),
    "sefwi wiawso": (6.2200, -2.4900),
    "sefwi bekwai": (6.2000, -2.3500),
    "sefwi asawinso": (6.2100, -2.5200),
    "sefwi boadi": (6.2300, -2.4500),
    "sefwi boinzan": (6.2000, -2.5000),
    "sefwi essam": (6.1800, -2.4000),
    "sefwi": (6.2100, -2.4900),
    "sefwi-asafo": (6.2200, -2.5000),
    "kojokrom/sekondi": (4.9400, -1.7100),
    "daboase": (5.2500, -1.7500),
    "apowa": (4.9000, -2.2000),
    "apremdo": (4.9000, -1.7600),
    "aboadze": (4.9700, -1.6200),
    "new takoradi": (4.9100, -1.7500),
    "kwesimintsim": (4.9200, -1.7600),
    "dixcove": (4.8000, -1.9700),
    "dompim": (5.4500, -2.0500),
    "kamgbunli": (4.8500, -2.2500),
    "manso amenfi": (5.8500, -2.2000),
    "benso": (5.2500, -1.8500),
    "dominase": (5.0500, -1.4500),
    "ayanfuri": (5.7500, -1.7000),
    "asankrangua": (5.7800, -2.3400),
    "brebre": (5.6000, -2.1000),

    # ── Central Region ──
    "cape coast": (5.1036, -1.2466),
    "winneba": (5.3508, -0.6257),
    "mankessim": (5.2700, -1.0400),
    "apam": (5.2800, -0.7300),
    "agona swedru": (5.5400, -0.7300),
    "agona swfru": (5.5400, -0.7300),
    "breman asikuma": (5.5700, -1.2000),
    "ankaful": (5.1200, -1.2700),
    "ajumako": (5.3200, -1.1300),
    "cabo corso": (5.1036, -1.2466),
    "agona nkwanta": (5.5000, -0.7000),
    "dunkwa-on-offin": (5.9600, -1.7800),
    "swedru": (5.5400, -0.7300),
    "asin": (5.3500, -1.1500),

    # ── Eastern Region ──
    "koforidua": (6.0936, -0.2572),
    "nkawkaw": (6.5500, -0.7800),
    "akosombo": (6.2900, 0.0500),
    "asamankese": (5.8640, -0.6600),
    "akuapem mampong": (5.9200, -0.0700),
    "akuapim-mampong": (5.9200, -0.0700),
    "mampong-akwapim": (5.9200, -0.0700),
    "suhum": (6.0400, -0.4500),
    "nsawam": (5.8100, -0.3500),
    "akwatia": (6.1300, -0.8300),
    "new abirim": (6.1800, -0.8800),
    "mangoase": (5.8500, -0.1500),
    "obosomase": (5.9500, -0.1000),
    "odonkawkrom": (6.5000, -0.8000),
    "adoagyiri-adeiso": (5.8000, -0.5000),
    "enyinabrim": (6.2000, -0.8500),
    "abuakwa": (6.1500, -0.2300),
    "akaporiso": (5.9000, -0.2000),

    # ── Northern Region ──
    "tamale": (9.4034, -0.8393),
    "yendi": (9.4450, -0.0100),
    "damongo": (9.0800, -1.8200),
    "bimbilla": (8.8500, -0.0600),
    "bimbila": (8.8500, -0.0600),
    "tolon": (9.4300, -1.0500),
    "karaga": (9.8000, -0.1800),
    "kparigu": (9.5000, -0.4000),
    "yabologu": (9.3500, -0.7500),
    "tatale": (9.1700, 0.5000),
    "zabzugu tatale": (9.2500, 0.3500),

    # ── Upper East ──
    "bolgatanga": (10.7863, -0.8522),
    "bawku": (11.0600, -0.2400),
    "navrongo": (10.8900, -1.0900),
    "sandema": (10.6300, -1.0700),
    "nogsenia": (10.8000, -0.8500),
    "wiaga": (10.5500, -1.0700),

    # ── Upper West ──
    "wa": (10.0601, -2.5099),
    "nadawli": (10.0700, -2.6600),
    "daffiama": (10.0300, -2.6000),
    "wechiau": (9.9000, -2.8500),
    "lamboya": (10.0100, -2.5300),

    # ── Volta Region ──
    "ho": (6.6000, 0.4680),
    "hohoe": (7.1500, 0.4730),
    "keta": (5.9200, 0.9900),
    "aflao": (6.1200, 1.1900),
    "kpando": (6.9800, 0.2900),
    "peki": (6.8600, 0.3100),
    "sogakope": (6.0000, 0.6300),
    "anfoega": (7.0000, 0.3500),
    "adidome": (6.1000, 0.5000),
    "dzodze": (6.2700, 0.9800),
    "akatsi": (6.1200, 0.8000),
    "worawora": (7.5300, 0.3700),
    "anloga": (5.7900, 0.8900),
    "anolga": (5.7900, 0.8900),
    "battor": (6.0800, 0.4500),
    "weme - abor": (6.0500, 0.5500),
    "nkonya": (7.2000, 0.2000),
    "nope": (6.0500, 0.5000),

    # ── Bono / Brong-Ahafo Region ──
    "sunyani": (7.3349, -2.3286),
    "berekum": (7.4530, -2.5830),
    "techiman": (7.5833, -1.9308),
    "goaso": (6.8000, -2.5200),
    "wenchi": (7.7400, -2.1000),
    "duayaw nkwanta": (7.1800, -2.5900),
    "dormaa ahenkro": (7.3600, -2.9600),
    "bechem": (7.0900, -2.0300),
    "acherensua": (6.8500, -2.5000),
    "nsawura": (7.2000, -2.4000),
    "abesim": (7.3500, -2.3100),
    "abesim - sunyani": (7.3400, -2.3200),
    "atebubu": (7.7500, -0.9800),
    "kintampo": (8.0500, -1.7300),
    "yeji": (8.2200, -0.6600),
    "banda": (8.0000, -2.2000),
    "twabidi": (7.1000, -2.1000),
    "mpatuom": (7.3200, -2.3400),

    # ── Savannah ──
    "salaga": (8.5500, -0.5200),
    "bole": (9.0300, -2.4800),
    "chinderi": (8.6000, -0.3000),

    # ── North East ──
    "nalerigu": (10.5200, -0.3700),
    "walewale": (10.3500, -0.7700),

    # ── Oti Region ──
    "kpandai": (8.4700, -0.0100),

    # ── Ahafo ──
    "afamaso": (6.9000, -2.5500),
    "asuofia": (6.9500, -2.4000),

    # ── Western North ──
    "juaboso": (6.3000, -2.7800),
    "adumkrom": (6.2000, -2.5000),

    # ── Misc/aliases ──
    "ghana": (7.9465, -1.0232),
    "western": (5.3000, -2.0000),
    "osu \u2013 accra east": (5.5571, -0.1818),
    "bakanta": (9.5000, -0.7000),
    "kabiase gonja": (9.3000, -1.2000),
    "apenkro": (6.0000, -2.5000),
    "ateiku": (6.6000, -1.6000),
    "sromani": (6.5000, -2.5000),
    "kawkawti": (9.3000, -0.5000),
    "mepom": (10.7000, -0.8000),
    "agroyesum": (6.6000, -1.5000),
    "abura": (5.1300, -1.2100),
    "adum banso": (5.8000, -2.0000),
    "afransi": (6.4000, -1.6000),
}

# Region-level fallback coordinates (approximate centroids)
GHANA_REGION_COORDS = {
    "greater accra": (5.6037, -0.1870),
    "greater accra region": (5.6037, -0.1870),
    "ashanti": (6.7470, -1.5209),
    "ashanti region": (6.7470, -1.5209),
    "western": (5.3000, -2.0000),
    "western region": (5.3000, -2.0000),
    "western north": (6.3000, -2.5000),
    "western north region": (6.3000, -2.5000),
    "central": (5.5000, -1.0000),
    "central region": (5.5000, -1.0000),
    "central ghana": (7.0000, -1.5000),
    "eastern": (6.2000, -0.5000),
    "eastern region": (6.2000, -0.5000),
    "northern": (9.5000, -1.0000),
    "northern region": (9.5000, -1.0000),
    "upper east": (10.7000, -0.8000),
    "upper east region": (10.7000, -0.8000),
    "upper west": (10.2500, -2.5000),
    "upper west region": (10.2500, -2.5000),
    "volta": (6.5000, 0.4000),
    "volta region": (6.5000, 0.4000),
    "bono": (7.5000, -2.3000),
    "bono region": (7.5000, -2.3000),
    "bono east": (7.7500, -1.2000),
    "bono east region": (7.7500, -1.2000),
    "brong ahafo": (7.5000, -1.8000),
    "brong ahafo region": (7.5000, -1.8000),
    "ahafo": (7.0000, -2.5000),
    "ahafo region": (7.0000, -2.5000),
    "oti": (7.8000, 0.3000),
    "oti region": (7.8000, 0.3000),
    "savannah": (9.0000, -1.8000),
    "savannah region": (9.0000, -1.8000),
    "north east": (10.2000, -0.3000),
    "north east region": (10.2000, -0.3000),
    "accra": (5.6037, -0.1870),
    "accra north": (5.6200, -0.2000),
    "accra east": (5.5571, -0.1818),
    "accra west": (5.5600, -0.2500),
    "takoradi": (4.8981, -1.7450),
    "asokwa-kumasi": (6.6600, -1.6300),
    "ga east municipality": (5.7000, -0.1700),
    "tema west municipal": (5.6600, -0.0200),
    "techiman municipal": (7.5833, -1.9308),
    "ejisu municipal": (6.7310, -1.4680),
    "shai osudoku district, greater accra region": (5.8700, -0.0400),
    "keea": (5.1500, -1.2500),
    "sissala west district": (10.3000, -2.5000),
    "sh": (7.5000, -1.5000),
    "central tongu district": (6.1000, 0.5500),
    "asutifi south": (6.7000, -2.4000),
    "dormaa east": (7.4000, -2.7000),
    "ledzokuku-krowor": (5.5800, -0.0700),
    "ahafo ano south-east": (6.7500, -1.7500),
}


def _normalize_place_name(name: str) -> str:
    """Normalize a place name for robust lookup (hyphens, abbreviations, whitespace)."""
    import re as _re
    n = name.strip().lower()
    n = _re.sub(r'[\s\-]+', ' ', n)          # collapse whitespace & hyphens
    n = n.replace('gt.', 'greater').replace('st.', 'saint')
    return n


def geocode_facility(city: str, region: str = None) -> tuple:
    """
    Return (latitude, longitude) for a facility based on city/region.
    Returns (None, None) if no match found.

    Uses a three-stage lookup:
      1. Exact match (city, then region)
      2. Word-boundary partial match — only accepts matches where the input
         appears as a whole word inside the key, sorted by key length so
         shorter (more specific) keys are preferred.  Avoids the old bug
         where "wa" matched "nkawkaw".
      3. Fuzzy Levenshtein fallback (>= 85 similarity) via rapidfuzz if
         available, catching common misspellings like Kumase -> Kumasi.
    """
    import re as _re

    # --- Stage 1: exact match -------------------------------------------------
    if city:
        city_lower = _normalize_place_name(city)
        if city_lower in GHANA_CITY_COORDS:
            return GHANA_CITY_COORDS[city_lower]

    if region:
        region_lower = _normalize_place_name(region)
        if region_lower in GHANA_REGION_COORDS:
            return GHANA_REGION_COORDS[region_lower]
        # Try matching with normalized keys
        for key, coords in GHANA_REGION_COORDS.items():
            if _normalize_place_name(key) == region_lower:
                return coords

    # --- Stage 2: word-boundary partial match (safe) --------------------------
    if city:
        city_lower = _normalize_place_name(city)
        # Sort candidates by key length (shorter = more specific match)
        candidates = sorted(GHANA_CITY_COORDS.items(), key=lambda x: len(x[0]))
        for key, coords in candidates:
            # Only accept if the query appears as a whole word in the key
            if _re.search(r'\b' + _re.escape(city_lower) + r'\b', key):
                return coords

    # --- Stage 3: fuzzy Levenshtein fallback -----------------------------------
    if city:
        try:
            from rapidfuzz import process as rfp
            match = rfp.extractOne(
                _normalize_place_name(city),
                GHANA_CITY_COORDS.keys(),
                score_cutoff=80,
            )
            if match:
                return GHANA_CITY_COORDS[match[0]]
        except ImportError:
            pass  # rapidfuzz not installed — skip fuzzy matching

    return None, None
