from rapidfuzz import fuzz, process, utils

from generator.names import make_name


def _worst_score(name, sanction_names):
    """Highest similarity between this name and any sanctions name."""
    match = process.extractOne(
        name, sanction_names,
        scorer=fuzz.token_sort_ratio, processor=utils.default_process,
    )
    return match[1] if match else 0


def fix_collisions(persons, sanctions, cfg, rng):
    """Re-roll any clean person whose name is too close to a sanctions name.
    Returns the fixed table and how many people were changed."""
    limit = cfg["collision_max_similarity"]
    sanction_names = sanctions["full_name"].tolist()
    persons = persons.copy()
    changed = 0

    for idx in persons.index:
        if _worst_score(persons.at[idx, "full_name"], sanction_names) < limit:
            continue

        culture = persons.at[idx, "culture"]
        for _ in range(500):
            parts = make_name(culture, rng)
            if _worst_score(parts["full_name"], sanction_names) < limit:
                for key, value in parts.items():
                    persons.at[idx, key] = value
                changed += 1
                break
        else:
            raise RuntimeError("Could not find a name that avoids the sanctions list")

    return persons, changed