import json
import random
from functools import lru_cache

from generator.config import load_config
from generator.clean import build_clean_dataset
from generator.sanctions import build_sanctions_list
from generator.collisions import fix_collisions
from generator.inject import Injector


def _build(seed):
    cfg = load_config()
    tables = build_clean_dataset(cfg, random.Random(seed))
    sanctions = build_sanctions_list(cfg, random.Random(seed + 1))
    tables["persons"], _ = fix_collisions(
        tables["persons"], sanctions, cfg, random.Random(seed + 2))
    injector = Injector(tables, sanctions, cfg, random.Random(seed + 3))
    injector.plant_sanctions_matches()
    injector.plant_lookalikes()
    persons, key = injector.results()
    return cfg, tables, sanctions, persons, key


_cached = lru_cache(maxsize=None)(_build)   # builds once, reused by the tests below


def test_exact_counts_are_planted():
    cfg, tables, _, _, key = _cached(1)
    n = len(tables["companies"])
    for flag in ("sanctions_match", "look_alike"):
        expected = round(cfg["rates"][flag] * n)
        rows = key[key["flag_type"] == flag]
        assert len(rows) == expected
        assert rows["company_id"].nunique() == expected


def test_lookalikes_are_not_red_flags():
    _, _, _, _, key = _cached(1)
    assert not key[key["flag_type"] == "look_alike"]["is_red_flag"].any()
    assert key[key["flag_type"] == "sanctions_match"]["is_red_flag"].all()


def test_no_person_is_planted_twice():
    _, _, _, _, key = _cached(1)
    assert key["person_id"].is_unique


def test_matches_share_dob_and_lookalikes_do_not():
    _, _, sanctions, persons, key = _cached(1)
    sanction_dob = dict(zip(sanctions["sanction_id"], sanctions["date_of_birth"]))
    person_dob = dict(zip(persons["person_id"], persons["date_of_birth"]))
    for row in key.itertuples():
        details = json.loads(row.details)
        same_dob = person_dob[row.person_id] == sanction_dob[details["sanction_id"]]
        assert same_dob == row.is_red_flag


def test_same_seed_same_answer_key():
    a = _build(5)[4]
    b = _build(5)[4]
    assert a.equals(b)