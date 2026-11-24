import json
import random
from functools import lru_cache

from generator.chains import plant_chains
from generator.clean import build_clean_dataset
from generator.collisions import fix_collisions
from generator.config import load_config
from generator.inject import Injector
from generator.ownership import (
    check_ownership, effective_stakes, links_by_owned_from_table)
from generator.sanctions import build_sanctions_list


def _build(seed):
    cfg = load_config()
    tables = build_clean_dataset(cfg, random.Random(seed))
    sanctions = build_sanctions_list(cfg, random.Random(seed + 1))
    tables["persons"], _ = fix_collisions(
        tables["persons"], sanctions, cfg, random.Random(seed + 2))
    injector = Injector(tables, sanctions, cfg, random.Random(seed + 3))
    injector.plant_sanctions_matches()
    injector.plant_lookalikes()
    plant_chains(injector, tables, cfg, random.Random(seed + 4))
    persons, key = injector.results()
    return cfg, tables, persons, key


_cached = lru_cache(maxsize=None)(_build)


def _direct_owners(tables):
    links = tables["ownership_links"]
    out = {}
    for row in links[links["owner_type"] == "person"].itertuples():
        out.setdefault(row.owned_company_id, set()).add(row.owner_id)
    return out


def test_exact_counts_are_planted():
    cfg, tables, _, key = _cached(1)
    n_clients = int(tables["companies"]["is_client"].sum())
    for rate_name, flag in [("hidden_owner", "hidden_owner"),
                            ("near_miss", "near_miss_chain")]:
        expected = round(cfg["rates"][rate_name] * n_clients)
        assert (key["flag_type"] == flag).sum() == expected


def test_ownership_adds_up_and_has_no_loops():
    _, tables, _, _ = _cached(1)
    check_ownership(tables)


def test_answer_key_matches_the_definition_of_hidden_owner():
    cfg, tables, _, key = _cached(1)
    links = links_by_owned_from_table(tables["ownership_links"])
    direct = _direct_owners(tables)
    companies = tables["companies"]
    clients = companies[companies["is_client"]]["company_id"]
    threshold = cfg["ownership_threshold_pct"]

    planted = {}
    for row in key[key["flag_type"] == "hidden_owner"].itertuples():
        planted.setdefault(row.company_id, set()).add(row.person_id)

    for cid in clients:
        stakes = effective_stakes(links, cid)
        found = {p for p, v in stakes.items()
                 if v >= threshold and p not in direct.get(cid, set())}
        assert found == planted.get(cid, set())


def test_near_misses_are_below_threshold_and_not_red_flags():
    cfg, tables, _, key = _cached(1)
    links = links_by_owned_from_table(tables["ownership_links"])
    rows = key[key["flag_type"] == "near_miss_chain"]
    assert not rows["is_red_flag"].any()
    for row in rows.itertuples():
        stake = effective_stakes(links, row.company_id)[row.person_id]
        assert stake < cfg["ownership_threshold_pct"]


def test_chain_depth_follows_the_evasion_period():
    cfg, tables, _, key = _cached(1)
    companies = tables["companies"]
    period_of = dict(zip(companies["company_id"], companies["period"]))
    chains = key[key["flag_type"].isin(["hidden_owner", "near_miss_chain"])]
    for row in chains.itertuples():
        depth = json.loads(row.details)["depth"]
        phase = ("after_evasion" if period_of[row.company_id] >= cfg["evasion_period"]
                 else "before_evasion")
        lo, hi = cfg["chain_depth"][phase]
        assert lo <= depth <= hi


def test_same_seed_same_answer_key():
    a = _build(5)[3]
    b = _build(5)[3]
    assert a.equals(b)