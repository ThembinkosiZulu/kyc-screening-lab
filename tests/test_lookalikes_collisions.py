import random

from rapidfuzz import fuzz, process, utils

from generator.config import load_config
from generator.clean import build_clean_dataset
from generator.sanctions import build_sanctions_list
from generator.lookalikes import make_lookalike
from generator.collisions import fix_collisions


def _setup():
    cfg = load_config()
    sanctions = build_sanctions_list(cfg, random.Random(1))
    return cfg, sanctions


def test_lookalike_is_a_different_person():
    cfg, sanctions = _setup()
    names = set(sanctions["full_name"])
    rng = random.Random(2)
    for entry in sanctions.to_dict("records"):
        la = make_lookalike(entry, cfg, rng, names)
        assert la["full_name"] != entry["full_name"]
        assert la["full_name"] not in names
        assert abs((la["date_of_birth"] - entry["date_of_birth"]).days) > 365
        assert la["lookalike_of"] == entry["sanction_id"]


def test_collision_fix_leaves_no_close_names():
    cfg, sanctions = _setup()
    persons = build_clean_dataset(cfg, random.Random(3))["persons"]
    fixed, _ = fix_collisions(persons, sanctions, cfg, random.Random(4))
    names = sanctions["full_name"].tolist()
    for name in fixed["full_name"]:
        score = process.extractOne(
            name, names, scorer=fuzz.token_sort_ratio, processor=utils.default_process
        )[1]
        assert score < cfg["collision_max_similarity"]