import json
import sys

import pandas as pd

flag = sys.argv[1] if len(sys.argv) > 1 else "high_risk_location"

key = pd.read_csv("answer_key/answer_key.csv")
companies = pd.read_csv("data/companies.csv").set_index("company_id")
docs = pd.read_csv("data/documents.csv")

for row in key[key["flag_type"] == flag].head(3).itertuples():
    details = json.loads(row.details)
    print(f"\n{row.company_id}   {row.flag_type}   red flag: {row.is_red_flag}")
    for name, value in details.items():
        print(f"   {name}: {value}")

    if flag == "high_risk_location":
        entity = details["entity_id"]
        print("   -> in companies.csv:", companies.loc[entity, "name"],
              "| country:", companies.loc[entity, "country_of_registration"])
    if flag == "document_mismatch":
        print(docs[docs["company_id"] == row.company_id].to_string(index=False))