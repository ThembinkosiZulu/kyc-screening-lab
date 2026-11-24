import random

from generator.config import load_config
from generator.clean import build_clean_dataset


def _build(seed=42):
    cfg = load_config()
    return cfg, build_clean_dataset(cfg, random.Random(seed))


def test_ownership_sums_to_100():
    cfg, t = _build()
    totals = t["ownership_links"].groupby("owned_company_id")["pct"].sum().round(1)
    assert (totals == 100.0).all()
    assert len(totals) == cfg["n_companies"]


def test_same_seed_same_data():
    _, a = _build(7)
    _, b = _build(7)
    for name in a:
        assert a[name].equals(b[name])


def test_each_company_has_director_and_two_agreeing_documents():
    _, t = _build()
    assert set(t["directors"]["company_id"]) == set(t["companies"]["company_id"])
    docs = t["documents"]
    assert (docs.groupby("company_id").size() == 2).all()
    assert (docs.groupby("company_id")["registration_number"].nunique() == 1).all()
    assert (docs.groupby("company_id")["address"].nunique() == 1).all()


def test_clean_companies_use_low_risk_countries_only():
    cfg, t = _build()
    assert set(t["companies"]["country_of_registration"]) <= set(cfg["low_risk_countries"])
    assert set(t["persons"]["country"]) <= set(cfg["low_risk_countries"])


def test_ids_are_unique():
    _, t = _build()
    assert t["persons"]["person_id"].is_unique
    assert t["companies"]["company_id"].is_unique
    assert t["companies"]["registration_number"].is_unique