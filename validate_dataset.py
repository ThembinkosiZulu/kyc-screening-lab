import json

import pandas as pd

from generator.config import load_config
from generator.ownership import (
    chain_companies, check_ownership, effective_stakes, links_by_owned_from_table)

cfg = load_config()
companies = pd.read_csv("data/companies.csv")
links_df = pd.read_csv("data/ownership_links.csv")
docs = pd.read_csv("data/documents.csv")
key = pd.read_csv("answer_key/answer_key.csv")

clients = companies[companies["is_client"]]["company_id"].tolist()
n_clients = len(clients)
links = links_by_owned_from_table(links_df)
threshold = cfg["ownership_threshold_pct"]

# ---------- 1. planted rates ----------
print("\n1. PLANTED RATES (share of client companies)")
print(f"{'flag':20} {'configured':>10} {'planted':>9} {'difference':>12}")
key_name = {"near_miss": "near_miss_chain"}
for rate_name, rate in cfg["rates"].items():
    flag = key_name.get(rate_name, rate_name)
    planted = key.loc[key["flag_type"] == flag, "company_id"].nunique() / n_clients * 100
    print(f"{flag:20} {rate * 100:9.1f}% {planted:8.1f}% {planted - rate * 100:+9.2f} pp")

# ---------- 2. structure ----------
print("\n2. STRUCTURE CHECKS")
check_ownership({"ownership_links": links_df})
print("ownership adds up to 100% for every company, and no chain loops: OK")

# ---------- 3. answer key vs the data ----------
print("\n3. ANSWER KEY vs THE DATA (recomputed from scratch)")

direct = {}
for row in links_df[links_df["owner_type"] == "person"].itertuples():
    direct.setdefault(row.owned_company_id, set()).add(row.owner_id)

found_hidden = {}
for cid in clients:
    stakes = effective_stakes(links, cid)
    hidden = {p for p, v in stakes.items()
              if v >= threshold and p not in direct.get(cid, set())}
    if hidden:
        found_hidden[cid] = hidden
planted_hidden = {}
for row in key[key["flag_type"] == "hidden_owner"].itertuples():
    planted_hidden.setdefault(row.company_id, set()).add(row.person_id)
print(f"hidden owners:      data shows {sum(map(len, found_hidden.values()))}, "
      f"key lists {sum(map(len, planted_hidden.values()))}, "
      f"match: {found_hidden == planted_hidden}")

country = dict(zip(companies["company_id"], companies["country_of_registration"]))
high = set(cfg["high_risk_countries"])
found_high = {c for c in clients
              if any(country[x] in high for x in chain_companies(links, c))}
planted_high = set(key.loc[key["flag_type"] == "high_risk_location", "company_id"])
print(f"high-risk location: data shows {len(found_high)}, "
      f"key lists {len(planted_high)}, match: {found_high == planted_high}")

found_docs = set()
for cid, group in docs.groupby("company_id"):
    if group["registration_number"].nunique() > 1 or group["address"].nunique() > 1:
        found_docs.add(cid)
planted_docs = set(key.loc[key["flag_type"] == "document_mismatch", "company_id"])
print(f"document mismatch:  data shows {len(found_docs)}, "
      f"key lists {len(planted_docs)}, match: {found_docs == planted_docs}")

# ---------- 4. evasion event ----------
print("\n4. EVASION EVENT (chain depth before and after the evasion period)")
chains = key[key["flag_type"].isin(["hidden_owner", "near_miss_chain"])].copy()
chains["depth"] = chains["details"].map(lambda d: json.loads(d)["depth"])
chains["after_evasion"] = chains["details"].map(lambda d: json.loads(d)["after_evasion"])
print(f"evasion starts at period {cfg['evasion_period']}; "
      f"tracer depth cap is {cfg['chain_depth']['tracer_cap']}")
print(chains.groupby("after_evasion")["depth"]
      .agg(["count", "min", "max", "mean"]).round(2).to_string())

# ---------- 5. sanctions variants ----------
print("\n5. SANCTIONS MATCH VARIANT LEVELS (0 = exact, 1 = one change, 2 = two changes)")
levels = key.loc[key["flag_type"] == "sanctions_match", "details"].map(
    lambda d: json.loads(d)["variant_level"])
print(levels.value_counts().sort_index().to_string())

# ---------- 6. overlaps ----------
print("\n6. COMPANIES WITH MORE THAN ONE ANSWER KEY ROW")
per_company = key.groupby("company_id").size()
print(f"{(per_company > 1).sum()} of {len(per_company)} companies in the answer key")