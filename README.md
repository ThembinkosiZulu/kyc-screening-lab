# KYC Screening Lab

Synthetic KYC onboarding data with planted red flags, a screening pipeline that has to find them and a comparison of rules against a machine-learning model. All people, companies, countries and sanctions entries are fictional.

This README covers **Part 1: the synthetic onboarding generator**. The screening pipeline and dashboard are documented as they are built.

## Setup

Python 3.12 or 3.13 (64-bit) is recommended.

Windows (PowerShell):

```
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Mac or Linux:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```
python generate.py            # builds data/ and answer_key/
python validate_dataset.py    # audits the generated data against the answer key
python -m pytest              # runs the unit tests
python peek_key.py hidden_owner   # shows 3 examples of one flag type
```

The same seed in `config/config.yaml` always produces the same data.

## Configuration (`config/config.yaml`)

All counts, rates and switches live in this file. The main settings:

| Setting | Meaning |
|---|---|
| `seed` | Random seed. Same seed gives the same dataset. |
| `n_companies`, `n_sanctions_entries` | Number of client companies (300-500) and sanctions entries (200-500). |
| `ownership_threshold_pct` | Beneficial ownership threshold (25). |
| `rates` | Share of client companies given each flag. Exact counts are planted, not coin flips. |
| `chain_depth` | Ownership chain depth ranges before and after the evasion event and the tracer cap. |
| `evasion_period` | Period from which hidden-owner chains get deeper than the tracer cap. |
| `variant_level_mix` | Mix of exact, one-change and two-change spelling variants for sanctions matches. |
| `cultures` | Name cultures and their weights: Chinese, Spanish, German, Arabic, South African. |
| `collision_max_similarity` | Clean people must score below this against every sanctions name. |
| `high_risk_mode_mix`, `mismatch_field_mix` | Where high-risk locations and document mismatches are planted. |
| `allow_multi_flag`, `multi_flag_probability` | Whether a company can carry more than one flag and how often. |

## What the detector gets (`data/`)

| File | Columns |
|---|---|
| `persons.csv` | person_id, full_name, date_of_birth, country |
| `companies.csv` | company_id, name, registration_number, country_of_registration, period, is_client |
| `directors.csv` | company_id, person_id |
| `ownership_links.csv` | owner_type (person or company), owner_id, owned_company_id, pct |
| `documents.csv` | document_id, company_id, doc_type (application or certificate), registration_number, address |
| `sanctions_list.csv` | sanction_id, full_name, date_of_birth, country |
| `high_risk_countries.csv` | country |

Notes:
- `is_client` is True for the 400 onboarded companies. Holding companies in ownership chains are listed too (they carry a country) but are not clients and have no directors or documents. Screen clients only.
- `period` is the onboarding week (1 to 52).
- Each company's ownership adds up to 100% and chains never loop.
- IDs and registration numbers use obviously fictional formats (`PE-`, `CO-`, `SL-`, `FAKE-XXX-`).

## The answer key (`answer_key/answer_key.csv`)

Kept in its own folder. **The detector must never read it.** It is used only to score the detector.

One row per planted case. The flag type is a value in the `flag_type` column.

| Column | Meaning |
|---|---|
| key_id | Row ID |
| company_id | Client company the case belongs to |
| flag_type | `sanctions_match`, `hidden_owner`, `document_mismatch`, `high_risk_location`, `look_alike`, `near_miss_chain` |
| is_red_flag | False for traps: look-alikes and near-misses should NOT be flagged |
| person_id | The person involved (empty for company-level flags) |
| details | JSON with specifics: variant level, effective stake, chain depth and path, country, changed field and so on |

Flag definitions follow the sponsor spec:
- **Sanctions match:** a director or owner whose name is an exact or spelling-variant match to a sanctions entry. Date of birth is copied from the sanctioned person.
- **Hidden owner:** a person with 25% or more in total through a chain of companies, not declared as an owner.
- **Document mismatch:** application and certificate disagree on registration number or address.
- **High-risk location:** a company anywhere in the ownership chain (the client or a holding company) is registered in a listed country.
- **Look-alike (trap):** an innocent person with a similar name and a different date of birth.
- **Near-miss chain (trap):** a chain whose person ends up between 15% and 22%, below the threshold.

Depth means the number of ownership links from the person to the client. A direct owner is depth 1.

## How the generator works

1. Load and validate the config. Each part of the generator gets its own random stream from the seed.
2. Build clean companies: people, directors, declared direct owners (100%) and two matching documents.
3. Build the sanctions list and re-roll any clean person whose name scores 90 or more against it.
4. Plant sanctions matches and look-alikes (exact counts, random owner or director).
5. Plant hidden owners and near-misses by building chains backwards from a target stake.
6. Plant high-risk locations.
7. Plant document mismatches last, so earlier steps cannot overwrite them.
8. Write the data and the answer key.

## Validation

`python validate_dataset.py` recomputes hidden owners, high-risk locations and document mismatches from the saved files and compares them with the answer key. Results for the shipped config (seed 42):

- All six planted rates match the configured rates (+0.00 pp).
- Hidden owners: 40 found in the data, 40 in the key. High-risk locations: 28 and 28. Document mismatches: 32 and 32.
- Chain depth is 2 to 4 before period 27 and 5 to 6 from period 27 (the evasion event).
- 8 of 176 flagged companies carry more than one answer key row.

## limitations

- **Small name lists.** Each culture uses a short hand-written name list. 274 of about 1,250 clean people had to be re-rolled to avoid close matches with the sanctions list. As a result, clean people never resemble a sanctions name closely, so name frequency must not be used as a model feature.
- **Chains only exist where planted.** Clean companies have only direct declared owners, so having a holding company currently signals a hidden-owner or near-miss case. A model can exploit this. Planned fix: add harmless declared holding structures to clean companies.
- **Overlap by design.** High-risk holding-company cases can only be planted on companies that already have a chain, so they overlap with hidden-owner and near-miss cases.
- **Ownership only.** Control through voting rights or board appointments is not modelled.
- **Clean chains.** Chains have no missing links or missing percentages, so tracing is easier than in real data.
- **One evasion pattern.** Only the deeper-chain evasion is implemented. Heavier spelling changes and split stakes are not yet switches.

## Project structure

```
config/config.yaml        settings
generator/                generator code (names, clean data, sanctions, variants,
                          look-alikes, collisions, injection, chains, location and mismatch)
tests/                    unit tests
generate.py               builds the data
validate_dataset.py       audits the data against the answer key
peek_key.py               prints examples of one flag type
data/                     detector inputs (generated)
answer_key/               scoring key (generated, never read by the detector)
```