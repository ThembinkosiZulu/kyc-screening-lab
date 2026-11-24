from generator.clean import _random_dob
from generator.names import make_name
from generator.variants import _has


def _compose(culture, p):
    """Put name parts together the way each culture writes them."""
    given, family = p["given_name"], p["family_name"]
    second = p.get("second_surname")
    prefix = p["name_prefix"] if _has(p, "name_prefix") else None

    if culture == "chinese":
        return f"{family} {given}"
    if culture == "spanish":
        return f"{given} {family} {second}"
    if culture == "arabic":
        return f"{given} {prefix}{family}" if prefix else f"{given} {family}"
    # german and south_african
    return f"{given} {prefix} {family}" if prefix else f"{given} {family}"


def make_lookalike(entry, cfg, rng, sanction_names):
    """An innocent person with a name similar to a sanctioned person,
    but a different name, a different date of birth, and no real link."""
    culture = entry["culture"]

    for _ in range(200):
        other = make_name(culture, rng)
        parts = {
            "given_name": entry["given_name"],
            "family_name": entry["family_name"],
            "second_surname": entry["second_surname"] if _has(entry, "second_surname") else None,
            "name_prefix": entry["name_prefix"] if _has(entry, "name_prefix") else None,
        }

        if rng.random() < 0.5:
            parts["given_name"] = other["given_name"]
            kind = "same_family_new_given"
        else:
            for key in ("family_name", "second_surname", "name_prefix"):
                parts[key] = other[key]
            kind = "same_given_new_family"

        full = _compose(culture, parts)
        if full == entry["full_name"] or full in sanction_names:
            continue

        dob = _random_dob(rng)
        while abs((dob - entry["date_of_birth"]).days) <= 365:
            dob = _random_dob(rng)

        return {
            **parts,
            "full_name": full,
            "culture": culture,
            "date_of_birth": dob,
            "country": rng.choice(cfg["low_risk_countries"]),
            "lookalike_of": entry["sanction_id"],
            "lookalike_kind": kind,
        }

    raise RuntimeError("Could not build a look-alike name")