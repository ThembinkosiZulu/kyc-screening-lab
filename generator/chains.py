import pandas as pd

from generator.clean import SUFFIX, WORD_A, _random_dob, _unique_reg_number
from generator.collisions import _worst_score
from generator.names import make_name
from generator.ownership import effective_stakes, links_by_owned_from_table

HOLDING_WORDS = ["Holdings", "Capital", "Ventures", "Investments", "Partners"]


def _sample_chain(depth, stake_range, link_range, filler_limit, rng):
    """Pick link percentages whose product lands in the wanted range,
    and where no filler owner of a holding company reaches the limit."""
    lo, hi = stake_range
    for _ in range(5000):
        pcts = [round(rng.uniform(*link_range), 1) for _ in range(depth)]
        stake = 100.0
        for p in pcts:
            stake *= p / 100
        if not lo <= stake <= hi:
            continue

        fillers_ok = True
        for i in range(depth - 1):
            filler = 100 - pcts[i]
            for p in pcts[i + 1:]:
                filler *= p / 100
            if filler >= filler_limit:
                fillers_ok = False
                break
        if fillers_ok:
            return pcts
    raise RuntimeError(f"Could not sample a chain of depth {depth}")


def plant_chains(inj, tables, cfg, rng):
    """Plant hidden owners and near-misses behind chains of holding companies."""
    companies = tables["companies"].to_dict("records")
    for c in companies:
        c["is_client"] = True
    period_of = {c["company_id"]: c["period"] for c in companies}
    links = links_by_owned_from_table(tables["ownership_links"])

    used_names = {c["name"] for c in companies}
    used_regs = {c["registration_number"] for c in companies}
    sanction_list = sorted(inj.sanction_names)
    cultures = list(cfg["cultures"].keys())
    weights = list(cfg["cultures"].values())
    low_risk = cfg["low_risk_countries"]
    limit = cfg["collision_max_similarity"]
    threshold = cfg["ownership_threshold_pct"]

    new_persons, new_companies = [], []
    base_persons = len(inj.persons)
    base_companies = len(companies)

    def new_person():
        for _ in range(500):
            culture = rng.choices(cultures, weights=weights, k=1)[0]
            parts = make_name(culture, rng)
            if _worst_score(parts["full_name"], sanction_list) < limit:
                break
        else:
            raise RuntimeError("Could not make a name that avoids the sanctions list")
        pid = f"PE-{base_persons + len(new_persons) + 1:06d}"
        new_persons.append({
            "person_id": pid, **parts, "culture": culture,
            "date_of_birth": _random_dob(rng), "country": rng.choice(low_risk),
        })
        return pid

    def new_shell(period):
        for _ in range(100):
            name = f"{rng.choice(WORD_A)} {rng.choice(HOLDING_WORDS)} {rng.choice(SUFFIX)}"
            if name not in used_names:
                break
        else:
            name = f"{rng.choice(WORD_A)} {rng.choice(HOLDING_WORDS)} {len(used_names) + 1} Ltd"
        used_names.add(name)
        country = rng.choice(low_risk)
        cid = f"CO-{base_companies + len(new_companies) + 1:06d}"
        new_companies.append({
            "company_id": cid, "name": name,
            "registration_number": _unique_reg_number(country, rng, used_regs),
            "country_of_registration": country, "period": period, "is_client": False,
        })
        return cid

    def plant_one(target, kind):
        period = period_of[target]
        after = period >= cfg["evasion_period"]
        lo, hi = cfg["chain_depth"]["after_evasion" if after else "before_evasion"]
        depth = rng.randint(lo, hi)
        stake_range = cfg["hidden_owner_stake_range" if kind == "hidden_owner"
                          else "near_miss_stake_range"]
        link_range = (55, 95) if kind == "hidden_owner" else (25, 95)
        pcts = _sample_chain(depth, stake_range, link_range, threshold - 5, rng)

        hidden_person = new_person()
        shells = [new_shell(period) for _ in range(depth - 1)]
        owners = [("person", hidden_person)] + [("company", s) for s in shells]
        owned = shells + [target]

        # make room on the target's register for the last link
        declared = links[target]
        declared_ids = {d[1] for d in declared}
        room = round(100 - pcts[-1], 1)
        scaled = [round(d[2] * room / 100, 1) for d in declared]
        scaled[-1] = round(room - sum(scaled[:-1]), 1)
        assert all(s > 0 for s in scaled), "declared owners squeezed to zero"
        for d, pct in zip(declared, scaled):
            d[2] = pct

        # the chain: person -> shell 1 -> shell 2 -> ... -> target
        for i in range(depth):
            links.setdefault(owned[i], []).append([owners[i][0], owners[i][1], pcts[i]])
        # a filler owner fills the rest of each holding company
        for i, shell in enumerate(shells):
            links[shell].append(["person", new_person(), round(100 - pcts[i], 1)])

        # self-check
        stakes = effective_stakes(links, target)
        expected = 100.0
        for p in pcts:
            expected *= p / 100
        got = stakes[hidden_person]
        assert abs(got - expected) < 1e-6
        if kind == "hidden_owner":
            assert got >= threshold
        else:
            assert got < threshold
        for pid, value in stakes.items():
            if pid != hidden_person and pid not in declared_ids:
                assert value < threshold, "an accidental hidden owner appeared"

        inj._mark_flagged(target)
        inj._add_key(
            target,
            "hidden_owner" if kind == "hidden_owner" else "near_miss_chain",
            kind == "hidden_owner",
            hidden_person,
            {
                "effective_stake": round(got, 2),
                "depth": depth,
                "path": [hidden_person] + shells + [target],
                "link_pcts": pcts,
                "after_evasion": after,
            },
        )

    chosen = set()
    for kind, flag in [("hidden_owner", "hidden_owner"), ("near_miss", "near_miss")]:
        for _ in range(inj._count(flag)):
            target = inj._choose_company(chosen, need_person=False)
            chosen.add(target)
            plant_one(target, kind)

    rows = [
        {"owner_type": t, "owner_id": o, "owned_company_id": cid, "pct": p}
        for cid, owners in links.items() for t, o, p in owners
    ]
    tables["ownership_links"] = pd.DataFrame(rows)
    tables["companies"] = pd.DataFrame(companies + new_companies)
    inj.persons = pd.DataFrame(inj.persons.to_dict("records") + new_persons)