import json

import pandas as pd

from generator.lookalikes import make_lookalike
from generator.variants import make_variant, pick_variant_level


class Injector:
    """Plants red flags into the clean data and records them in the answer key."""

    def __init__(self, tables, sanctions, cfg, rng):
        self.cfg = cfg
        self.rng = rng
        self.persons = tables["persons"].copy()
        self.row_of = {pid: idx for idx, pid in
                       zip(self.persons.index, self.persons["person_id"])}
        self.sanctions = sanctions.to_dict("records")
        self.sanction_names = set(sanctions["full_name"])
        self.n_companies = len(tables["companies"])

        company_ids = sorted(tables["companies"]["company_id"])
        self.clean_pool = list(company_ids)   # companies with nothing planted yet
        self.flagged = []                     # companies with something planted
        self.key_rows = []

        # who belongs to which company, and in what role
        self.company_of, self.roles = {}, {}
        links = tables["ownership_links"]
        for row in links[links["owner_type"] == "person"].itertuples():
            self.company_of[row.owner_id] = row.owned_company_id
            self.roles.setdefault(row.owner_id, set()).add("owner")
        for row in tables["directors"].itertuples():
            self.company_of[row.person_id] = row.company_id
            self.roles.setdefault(row.person_id, set()).add("director")

        # people in each company who have not been changed yet
        self.free_people = {cid: [] for cid in company_ids}
        for pid in sorted(self.company_of):
            self.free_people[self.company_of[pid]].append(pid)

    # ---------- helpers ----------

    def _count(self, flag):
        """Exact number of companies that get this flag."""
        return round(self.cfg["rates"][flag] * self.n_companies)

    def _choose_company(self, chosen, need_person=True):
        """Pick a company that has not had this flag yet and still has a free person.
        Mostly from clean companies, sometimes from already-flagged ones."""
        p = self.cfg["multi_flag_probability"] if self.cfg["allow_multi_flag"] else 0.0
        for _ in range(200):
            if self.flagged and self.rng.random() < p:
                cid = self.rng.choice(self.flagged)
            else:
                cid = self.rng.choice(self.clean_pool)
            if cid not in chosen and (self.free_people[cid] or not need_person):
                return cid
        raise RuntimeError("Could not find a company to plant in")

    def _take_person(self, cid):
        people = self.free_people[cid]
        return people.pop(self.rng.randrange(len(people)))

    def _mark_flagged(self, cid):
        if cid in self.clean_pool:
            self.clean_pool.remove(cid)
            self.flagged.append(cid)

    def _set_person(self, pid, **values):
        idx = self.row_of[pid]
        for column, value in values.items():
            self.persons.at[idx, column] = value

    def _role(self, pid):
        return "+".join(sorted(self.roles[pid]))

    def _add_key(self, cid, flag_type, is_red_flag, pid, details):
        self.key_rows.append({
            "key_id": f"AK-{len(self.key_rows) + 1:05d}",
            "company_id": cid,
            "flag_type": flag_type,
            "is_red_flag": is_red_flag,
            "person_id": pid,
            "details": json.dumps(details, ensure_ascii=False),
        })

    # ---------- planting ----------

    def plant_sanctions_matches(self):
        chosen = set()
        for _ in range(self._count("sanctions_match")):
            cid = self._choose_company(chosen)
            chosen.add(cid)
            pid = self._take_person(cid)

            entry = self.rng.choice(self.sanctions)
            level = pick_variant_level(self.cfg, self.rng)
            variant = make_variant(entry, level, self.rng)

            self._set_person(pid, full_name=variant["name"],
                             date_of_birth=entry["date_of_birth"])
            self._mark_flagged(cid)
            self._add_key(cid, "sanctions_match", True, pid, {
                "sanction_id": entry["sanction_id"],
                "sanctioned_name": entry["full_name"],
                "planted_name": variant["name"],
                "variant_level": level,
                "changes": variant["changes"],
                "role": self._role(pid),
            })

    def plant_lookalikes(self):
        chosen = set()
        for _ in range(self._count("look_alike")):
            cid = self._choose_company(chosen)
            chosen.add(cid)
            pid = self._take_person(cid)

            entry = self.rng.choice(self.sanctions)
            la = make_lookalike(entry, self.cfg, self.rng, self.sanction_names)

            self._set_person(pid, full_name=la["full_name"],
                             date_of_birth=la["date_of_birth"],
                             country=la["country"])
            self._mark_flagged(cid)
            self._add_key(cid, "look_alike", False, pid, {
                "sanction_id": entry["sanction_id"],
                "sanctioned_name": entry["full_name"],
                "planted_name": la["full_name"],
                "kind": la["lookalike_kind"],
                "role": self._role(pid),
            })

    def results(self):
        return self.persons, pd.DataFrame(self.key_rows)