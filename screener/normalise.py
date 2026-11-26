import unicodedata

from rapidfuzz import utils

PREFIXES = {"al", "el", "von", "zu", "van", "der", "du", "le", "de"}
UMLAUTS = str.maketrans({"ü": "ue", "ö": "oe", "ä": "ae",
                         "Ü": "Ue", "Ö": "Oe", "Ä": "Ae", "ß": "ss"})


def normalise_baseline(name):
    """Lowercase and turn punctuation into spaces. Nothing else."""
    return utils.default_process(name)


def normalise_improved(name):
    """Baseline, plus umlaut spelling, accent removal and common name prefixes."""
    name = name.translate(UMLAUTS)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    tokens = utils.default_process(name).split()
    kept = [t for t in tokens if t not in PREFIXES]
    return " ".join(kept or tokens)