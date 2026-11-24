import pandas as pd

from generator.clean import _random_dob
from generator.names import make_name


def build_sanctions_list(cfg, rng):
    """Build the fictional sanctions list. Keeps name parts and culture too,
    because the generator needs them to make variants and look-alikes."""
    cultures = list(cfg["cultures"].keys())
    weights = list(cfg["cultures"].values())
    countries = list(cfg["high_risk_countries"]) + list(cfg["low_risk_countries"])

    rows, seen = [], set()
    attempts = 0
    while len(rows) < cfg["n_sanctions_entries"]:
        attempts += 1
        if attempts > 20000:
            raise RuntimeError("Could not build enough unique sanctions names")
        culture = rng.choices(cultures, weights=weights, k=1)[0]
        parts = make_name(culture, rng)
        if parts["full_name"] in seen:
            continue
        seen.add(parts["full_name"])
        rows.append({
            "sanction_id": f"SL-{len(rows) + 1:04d}",
            **parts,
            "culture": culture,
            "date_of_birth": _random_dob(rng),
            "country": rng.choice(countries),
        })
    return pd.DataFrame(rows)
    