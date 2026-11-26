from dataclasses import dataclass

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process


@dataclass
class NameScores:
    people: pd.DataFrame      # one row per screened person
    sanction_ids: list
    scores: np.ndarray        # people x sanctions entries, similarity 0-100
    dob_equal: np.ndarray     # people x sanctions entries, True if birth dates match


def screened_people(data):
    """Every director and declared person-owner of every client company."""
    companies = data["companies"]
    clients = set(companies.loc[companies["is_client"], "company_id"])

    directors = data["directors"][["company_id", "person_id"]].assign(role="director")
    links = data["ownership_links"]
    owners = (links.loc[links["owner_type"] == "person", ["owned_company_id", "owner_id"]]
              .rename(columns={"owned_company_id": "company_id", "owner_id": "person_id"})
              .assign(role="owner"))

    both = pd.concat([directors, owners])
    both = both[both["company_id"].isin(clients)]
    roles = (both.groupby(["company_id", "person_id"])["role"]
             .agg(lambda s: "+".join(sorted(set(s)))).reset_index())
    people = roles.merge(
        data["persons"][["person_id", "full_name", "date_of_birth"]], on="person_id")
    return people.sort_values(["company_id", "person_id"]).reset_index(drop=True)


def score_names(data, normalise):
    """Score every screened person against every sanctions entry."""
    people = screened_people(data)
    sanctions = data["sanctions_list"]

    queries = [normalise(n) for n in people["full_name"]]
    choices = [normalise(n) for n in sanctions["full_name"]]
    scores = process.cdist(queries, choices, scorer=fuzz.token_sort_ratio, dtype=np.float32)

    person_dob = people["date_of_birth"].astype(str).to_numpy()
    sanction_dob = sanctions["date_of_birth"].astype(str).to_numpy()
    dob_equal = person_dob[:, None] == sanction_dob[None, :]

    return NameScores(people, sanctions["sanction_id"].tolist(), scores, dob_equal)


def rule_a(ns, threshold):
    """Name only: alert if the best name score reaches the threshold."""
    return ns.scores.max(axis=1) >= threshold


def rule_b(ns, threshold, strong=90):
    """Name plus date of birth: alert if the name is very close (strong),
    or the name reaches the threshold AND the date of birth matches."""
    best = ns.scores.max(axis=1)
    dob_hit = ((ns.scores >= threshold) & ns.dob_equal).any(axis=1)
    return (best >= strong) | dob_hit