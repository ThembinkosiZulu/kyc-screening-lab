import numpy as np
import pandas as pd

from screener.name_match import NameScores, rule_a, rule_b, score_names, screened_people
from screener.normalise import normalise_baseline, normalise_improved


def _tiny():
    return {
        "companies": pd.DataFrame({"company_id": ["C1", "C2"], "is_client": [True, True]}),
        "directors": pd.DataFrame({"company_id": ["C1", "C2"], "person_id": ["P1", "P2"]}),
        "ownership_links": pd.DataFrame({
            "owner_type": ["person"], "owner_id": ["P3"],
            "owned_company_id": ["C1"], "pct": [100.0]}),
        "persons": pd.DataFrame({
            "person_id": ["P1", "P2", "P3"],
            "full_name": ["Thandi Dlamini", "Mueller Hans", "Sipho Nkosi"],
            "date_of_birth": ["1980-01-01", "1970-05-05", "1990-09-09"],
            "country": ["Norvia"] * 3}),
        "sanctions_list": pd.DataFrame({
            "sanction_id": ["SL-0001", "SL-0002"],
            "full_name": ["Thandi Dlamini", "Hans Müller"],
            "date_of_birth": ["1980-01-01", "1970-05-05"],
            "country": ["Norvia", "Norvia"]}),
    }


def test_directors_and_owners_are_screened():
    people = screened_people(_tiny())
    assert sorted(people["person_id"]) == ["P1", "P2", "P3"]


def test_exact_name_is_flagged_at_100():
    ns = score_names(_tiny(), normalise_baseline)
    flagged = ns.people.loc[rule_a(ns, 100), "person_id"].tolist()
    assert flagged == ["P1"]


def test_improved_normalisation_beats_baseline_on_umlauts():
    base = score_names(_tiny(), normalise_baseline)
    better = score_names(_tiny(), normalise_improved)
    row = list(base.people["person_id"]).index("P2")
    assert better.scores[row, 1] > base.scores[row, 1]


def test_rule_b_uses_date_of_birth_below_the_strong_score():
    ns = NameScores(
        people=pd.DataFrame({"person_id": ["P1", "P2"]}),
        sanction_ids=["S1"],
        scores=np.array([[60.0], [60.0]]),
        dob_equal=np.array([[True], [False]]),
    )
    assert rule_a(ns, 50).tolist() == [True, True]
    assert rule_b(ns, 50).tolist() == [True, False]