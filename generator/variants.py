import re
import unicodedata

SIMILAR_LETTER = {
    "a": "e", "e": "a", "i": "y", "y": "i", "o": "u", "u": "o",
    "c": "k", "k": "c", "s": "z", "z": "s", "d": "t", "t": "d",
    "b": "p", "p": "b", "g": "j", "j": "g", "m": "n", "n": "m",
    "l": "r", "r": "l", "v": "w", "w": "v",
}

CHINESE_ROMANISATION = {
    "Zhang": "Chang", "Li": "Lee", "Wang": "Wong", "Chen": "Chan",
    "Liu": "Lau", "Yang": "Yeung", "Huang": "Hwang", "Zhao": "Chao",
    "Wu": "Ng", "Zhou": "Chow", "Xu": "Hsu", "Sun": "Suen",
}

ARABIC_ALTERNATIVES = {
    "Mohammed": ["Muhammad", "Mohamed", "Mohammad"], "Ahmed": ["Ahmad"],
    "Omar": ["Umar"], "Hassan": ["Hasan"], "Khalid": ["Khaled"],
    "Yusuf": ["Yousef", "Yousuf"], "Ibrahim": ["Ebrahim"],
    "Layla": ["Leila", "Laila"], "Fatima": ["Fatma"], "Samira": ["Sameera"],
    "Amira": ["Ameera"], "Noor": ["Nour"], "Rahman": ["Rehman"],
    "Saleh": ["Salih"], "Nasser": ["Nasir"], "Haddad": ["Hadad"],
    "Mansour": ["Mansur"], "Karim": ["Kareem"], "Farouk": ["Farook"],
    "Aziz": ["Azeez"], "Khoury": ["Khouri"],
}

LEVELS = {"exact": 0, "one_change": 1, "two_changes": 2}


def _has(entry, key):
    value = entry.get(key)
    return isinstance(value, str) and value != ""


def _edit_spots(name):
    """Positions we may edit: inside words of 4+ letters, never the first letter."""
    spots = []
    for m in re.finditer(r"[^\W\d_]{4,}", name):
        spots.extend(range(m.start() + 1, m.end()))
    return spots


# ---------- generic rules (any culture) ----------

def _drop_letter(name, entry, rng):
    spots = _edit_spots(name)
    if not spots:
        return None
    i = rng.choice(spots)
    return name[:i] + name[i + 1:]


def _double_letter(name, entry, rng):
    spots = _edit_spots(name)
    if not spots:
        return None
    i = rng.choice(spots)
    return name[:i] + name[i] + name[i:]


def _swap_letters(name, entry, rng):
    spots = _edit_spots(name)
    pairs = [i for i in spots if i + 1 in spots and name[i] != name[i + 1]]
    if not pairs:
        return None
    i = rng.choice(pairs)
    return name[:i] + name[i + 1] + name[i] + name[i + 2:]


def _change_letter(name, entry, rng):
    spots = [i for i in _edit_spots(name) if name[i].lower() in SIMILAR_LETTER]
    if not spots:
        return None
    i = rng.choice(spots)
    new = SIMILAR_LETTER[name[i].lower()]
    if name[i].isupper():
        new = new.upper()
    return name[:i] + new + name[i + 1:]


def _initials(name, entry, rng):
    given = entry["given_name"]
    return name.replace(given, given[0] + ".", 1)


def _swap_order(name, entry, rng):
    tokens = name.split()
    if len(tokens) < 2:
        return None
    return " ".join(tokens[1:] + tokens[:1])


# ---------- culture rules ----------

def _romanisation(name, entry, rng):
    alt = CHINESE_ROMANISATION.get(entry["family_name"])
    if not alt:
        return None
    return name.replace(entry["family_name"], alt, 1)


def _strip_accents(name, entry, rng):
    new = "".join(c for c in unicodedata.normalize("NFKD", name)
                  if not unicodedata.combining(c))
    return new if new != name else None


def _drop_second_surname(name, entry, rng):
    if not _has(entry, "second_surname"):
        return None
    new = name.replace(" " + entry["second_surname"], "", 1)
    return new if new != name else None


def _umlaut(name, entry, rng):
    new = name
    for a, b in [("ü", "ue"), ("ö", "oe"), ("ä", "ae"),
                 ("Ü", "Ue"), ("Ö", "Oe"), ("Ä", "Ae"), ("ß", "ss")]:
        new = new.replace(a, b)
    return new if new != name else None


def _drop_prefix(name, entry, rng):
    if not _has(entry, "name_prefix"):
        return None
    new = name.replace(entry["name_prefix"] + " ", "", 1)
    return new if new != name else None


def _transliteration(name, entry, rng):
    words = re.findall(r"[^\W\d_]+", name)
    options = [w for w in words if w in ARABIC_ALTERNATIVES]
    if not options:
        return None
    word = rng.choice(options)
    new_word = rng.choice(ARABIC_ALTERNATIVES[word])
    return re.sub(rf"\b{word}\b", new_word, name, count=1)


def _al_prefix(name, entry, rng):
    if "Al-" not in name:
        return None
    return name.replace("Al-", rng.choice(["Al ", "El-"]), 1)


def _prefix_style(name, entry, rng):
    if not _has(entry, "name_prefix"):
        return None
    prefix, family = entry["name_prefix"], entry["family_name"]
    old = f"{prefix} {family}"
    if old not in name:
        return None
    if rng.random() < 0.5:
        new = f"{prefix.title()} {family}"
    else:
        new = prefix.replace(" ", "") + family
    return name.replace(old, new, 1)


RULES = {
    "drop_letter": _drop_letter, "double_letter": _double_letter,
    "swap_letters": _swap_letters, "change_letter": _change_letter,
    "initials": _initials, "swap_order": _swap_order,
    "romanisation": _romanisation, "strip_accents": _strip_accents,
    "drop_second_surname": _drop_second_surname, "umlaut": _umlaut,
    "drop_prefix": _drop_prefix, "transliteration": _transliteration,
    "al_prefix": _al_prefix, "prefix_style": _prefix_style,
}

GENERIC_RULES = ["drop_letter", "double_letter", "swap_letters",
                 "change_letter", "initials", "swap_order"]

CULTURE_RULES = {
    "chinese": ["romanisation"],
    "spanish": ["strip_accents", "drop_second_surname"],
    "german": ["umlaut", "strip_accents", "drop_prefix"],
    "arabic": ["transliteration", "al_prefix"],
    "south_african": ["prefix_style"],
}


def pick_variant_level(cfg, rng):
    """Roll the die: 0 = exact copy, 1 = one change, 2 = two changes."""
    names = list(cfg["variant_level_mix"].keys())
    weights = list(cfg["variant_level_mix"].values())
    return LEVELS[rng.choices(names, weights=weights, k=1)[0]]


def make_variant(entry, level, rng):
    """Return a spelling variant of a sanctioned person's name.
    level 0 = exact, 1 = one change, 2 = two changes."""
    original = entry["full_name"]
    if level == 0:
        return {"name": original, "changes": []}

    # culture rules are listed twice so they are picked more often
    pool = GENERIC_RULES + CULTURE_RULES[entry["culture"]] * 2
    name, changes = original, []
    for _ in range(60):
        if len(changes) == level:
            break
        rule = rng.choice(pool)
        if rule in changes:
            continue
        new = RULES[rule](name, entry, rng)
        if new and new != name and new != original:
            name = new
            changes.append(rule)

    if not changes:   # safety net: swapping the order always works
        swapped = _swap_order(original, entry, rng)
        if swapped:
            name, changes = swapped, ["swap_order"]
    return {"name": name, "changes": changes}
    