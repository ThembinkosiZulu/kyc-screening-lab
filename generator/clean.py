from datetime import date
import pandas as pd
from generator.names import make_name

WORD_A = ["Alder", "Bright", "Cedar", "Delta", "Ember", "Falcon", "Granite",
          "Harbor", "Ivory", "Juniper", "Kestrel", "Lumen", "Meridian",
          "Northfield", "Orchid", "Pinnacle"]
WORD_B = ["Trading", "Logistics", "Mining", "Foods", "Textiles",
          "Software", "Consulting", "Farming", "Energy", "Retail"]
SUFFIX = ["Ltd", "Inc", "Group", "Co"]
STREETS = ["Main", "Station", "Market", "Church", "Mill",
           "River", "Park", "Hill", "Garden", "Bridge"]
CITIES = ["Eastport", "Northgate", "Lakeview", "Stonebridge", "Redfield", "Highmoor"]


def _random_dob(rng):
    start = date(1950, 1, 1).toordinal()
    end = date(2000, 12, 31).toordinal()
    return date.fromordinal(rng.randint(start, end))


def _pct_split(n, rng):
    """Split 100% between n owners. The pieces always add up to exactly 100."""
    weights = [rng.random() + 0.2 for _ in range(n)]
    total = sum(weights)
    pcts = [round(100 * w / total, 1) for w in weights[:-1]]
    pcts.append(round(100 - sum(pcts), 1))
    return pcts


def _unique_company_name(rng, used):
    for _ in range(100):
        name = f"{rng.choice(WORD_A)} {rng.choice(WORD_B)} {rng.choice(SUFFIX)}"
        if name not in used:
            used.add(name)
            return name
    name = f"{rng.choice(WORD_A)} {rng.choice(WORD_B)} {len(used) + 1} Ltd"
    used.add(name)
    return name


def _unique_reg_number(country, rng, used):
    code = country[:3].upper()
    while True:
        reg = f"FAKE-{code}-{rng.randint(0, 999999):06d}"
        if reg not in used:
            used.add(reg)
            return reg


def _address(rng):
    return f"{rng.randint(1, 999)} {rng.choice(STREETS)} Street, {rng.choice(CITIES)}"


def build_clean_dataset(cfg, rng):
    """Build companies, people, directors, ownership links and documents.
    Everything is consistent and low-risk. No flags are planted here."""
    low_risk = cfg["low_risk_countries"]
    cultures = list(cfg["cultures"].keys())
    weights = list(cfg["cultures"].values())

    persons, companies, directors, links, documents = [], [], [], [], []
    used_names, used_regs = set(), set()

    def new_person(country):
        culture = rng.choices(cultures, weights=weights, k=1)[0]
        parts = make_name(culture, rng)
        pid = f"PE-{len(persons) + 1:06d}"
        persons.append({
            "person_id": pid,
            **parts,
            "culture": culture,
            "date_of_birth": _random_dob(rng),
            "country": country,
        })
        return pid

    for i in range(cfg["n_companies"]):
        cid = f"CO-{i + 1:06d}"
        country = rng.choice(low_risk)
        reg = _unique_reg_number(country, rng, used_regs)
        address = _address(rng)

        companies.append({
            "company_id": cid,
            "name": _unique_company_name(rng, used_names),
            "registration_number": reg,
            "country_of_registration": country,
            "period": i % cfg["n_periods"] + 1,
        })

        # declared direct owners (people), adding up to 100%
        n_owners = rng.choice([1, 2, 2, 3, 3, 4])
        owner_ids = [new_person(rng.choice(low_risk)) for _ in range(n_owners)]
        for pid, pct in zip(owner_ids, _pct_split(n_owners, rng)):
            links.append({
                "owner_type": "person",
                "owner_id": pid,
                "owned_company_id": cid,
                "pct": pct,
            })

        # directors: sometimes the owners, sometimes other people
        director_ids = []
        for _ in range(rng.choice([1, 1, 2, 3])):
            if rng.random() < 0.6:
                candidate = rng.choice(owner_ids)
            else:
                candidate = new_person(rng.choice(low_risk))
            if candidate not in director_ids:
                director_ids.append(candidate)
        for pid in director_ids:
            directors.append({"company_id": cid, "person_id": pid})

        # two documents that agree with each other
        for doc_type in ["application", "certificate"]:
            documents.append({
                "document_id": f"DOC-{len(documents) + 1:06d}",
                "company_id": cid,
                "doc_type": doc_type,
                "registration_number": reg,
                "address": address,
            })

    return {
        "persons": pd.DataFrame(persons),
        "companies": pd.DataFrame(companies),
        "directors": pd.DataFrame(directors),
        "ownership_links": pd.DataFrame(links),
        "documents": pd.DataFrame(documents),
    }
