import random

from generator.config import load_config
from generator.sanctions import build_sanctions_list
from generator.variants import make_variant


def _sanctions():
    cfg = load_config()
    return cfg, build_sanctions_list(cfg, random.Random(1))


def test_sanctions_list_size_and_unique_names():
    cfg, s = _sanctions()
    assert len(s) == cfg["n_sanctions_entries"]
    assert s["full_name"].is_unique
    assert s["sanction_id"].is_unique


def test_exact_variant_is_unchanged():
    _, s = _sanctions()
    entry = s.iloc[0].to_dict()
    assert make_variant(entry, 0, random.Random(2))["name"] == entry["full_name"]


def test_variants_change_the_name():
    _, s = _sanctions()
    rng = random.Random(3)
    for entry in s.to_dict("records"):
        for level in (1, 2):
            v = make_variant(entry, level, rng)
            assert v["name"] != entry["full_name"]
            assert len(v["changes"]) >= 1


def test_same_seed_same_variant():
    _, s = _sanctions()
    entry = s.iloc[5].to_dict()
    a = make_variant(entry, 2, random.Random(9))
    b = make_variant(entry, 2, random.Random(9))
    assert a == b
    