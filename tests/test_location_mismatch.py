import random
from functools import lru_cache

from generator.chains import plant_chains
from generator.clean import build_clean_dataset
from generator.collisions import fix_collisions
from generator.config import load_config
from generator.inject import Injector
from generator.location_mismatch import plant_document_mismatches, plant_high_risk_locations
from generator.ownership import chain_companies, links_by_owned_from_table
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
    plant_high_risk_locations(injector, tables, cfg, random.Random(seed + 5))
    plant_document_mismatches(injector, tables, cfg, random.Random(seed + 6))
    _, key = injector.results()
    return cfg, tables, key


_cached = lru_cache(maxsize=None)(_build)


def test_exact_counts_are_planted():
    cfg, tables, key = _cached(1)
    n_clients = int(tables["companies"]["is_client"].sum())
    for flag in ("high_risk_location", "document_mismatch"):
        expected = round(cfg["rates"][flag] * n_clients)
        assert (key["flag_type"] == flag).sum() == expected


def test_high_risk_matches_the_definition():
    cfg, tables, key = _cached(1)
    links = links_by_owned_from_table(tables["ownership_links"])
    companies = tables["companies"]
    country = dict(zip(companies["company_id"], companies["country_of_registration"]))
    high = set(cfg["high_risk_countries"])
    clients = companies[companies["is_client"]]["company_id"]

    found = {cid for cid in clients
             if any(country[c] in high for c in chain_companies(links, cid))}
    planted = set(key[key["flag_type"] == "high_risk_location"]["company_id"])
    assert found == planted


def test_documents_disagree_only_where_planted():
    _, tables, key = _cached(1)
    disagree = set()
    for cid, group in tables["documents"].groupby("company_id"):
        if group["registration_number"].nunique() > 1 or group["address"].nunique() > 1:
            disagree.add(cid)
    planted = set(key[key["flag_type"] == "document_mismatch"]["company_id"])
    assert disagree == planted


def test_documents_match_company_record_when_not_planted():
    _, tables, key = _cached(1)
    planted = set(key[key["flag_type"] == "document_mismatch"]["company_id"])
    companies = tables["companies"]
    reg = dict(zip(companies["company_id"], companies["registration_number"]))
    for row in tables["documents"].itertuples():
        if row.company_id not in planted:
            assert row.registration_number == reg[row.company_id]


def test_same_seed_same_answer_key():
    a = _build(5)[2]
    b = _build(5)[2]
    assert a.equals(b)