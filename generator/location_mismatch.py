from generator.clean import CITIES, _unique_reg_number


def _swap_two_digits(reg, rng):
    prefix, digits = reg.rsplit("-", 1)
    spots = [i for i in range(len(digits) - 1) if digits[i] != digits[i + 1]]
    if not spots:
        return f"{prefix}-{digits[:-1]}{(int(digits[-1]) + 1) % 10}"
    i = rng.choice(spots)
    swapped = digits[:i] + digits[i + 1] + digits[i] + digits[i + 2:]
    return f"{prefix}-{swapped}"


def _change_address(address, rng):
    street, city = address.rsplit(", ", 1)
    if rng.random() < 0.5:
        number, name = street.split(" ", 1)
        new_number = number
        while new_number == number:
            new_number = str(rng.randint(1, 999))
        return f"{new_number} {name}, {city}", "house number changed"
    new_city = rng.choice([c for c in CITIES if c != city])
    return f"{street}, {new_city}", "city changed"


def plant_high_risk_locations(inj, tables, cfg, rng):
    """Register a company in the client's ownership chain in a high-risk country."""
    companies = tables["companies"]
    docs = tables["documents"]
    row_of = {cid: idx for idx, cid in zip(companies.index, companies["company_id"])}
    used_regs = set(companies["registration_number"])

    modes = list(cfg["high_risk_mode_mix"].keys())
    weights = list(cfg["high_risk_mode_mix"].values())
    chain_targets = sorted(inj.chains)
    chosen = set()

    for _ in range(inj._count("high_risk_location")):
        mode = rng.choices(modes, weights=weights, k=1)[0]
        available = [c for c in chain_targets if c not in chosen]
        if mode == "holding" and available:
            target = rng.choice(available)
            shells = inj.chains[target]
            i = rng.randrange(len(shells))
            entity, level = shells[i], len(shells) - i   # 1 = directly above the client
        else:
            target = inj._choose_company(chosen, need_person=False)
            entity, level = target, 0                    # the client itself
        chosen.add(target)

        country = rng.choice(cfg["high_risk_countries"])
        new_reg = _unique_reg_number(country, rng, used_regs)
        idx = row_of[entity]
        companies.at[idx, "country_of_registration"] = country
        companies.at[idx, "registration_number"] = new_reg
        if level == 0:   # keep the client's documents consistent with its record
            docs.loc[docs["company_id"] == entity, "registration_number"] = new_reg

        inj._mark_flagged(target)
        inj._add_key(target, "high_risk_location", True, None, {
            "entity_id": entity, "level": level, "country": country,
        })


def plant_document_mismatches(inj, tables, cfg, rng):
    """Make the application and the certificate disagree. Run this last."""
    docs = tables["documents"]
    fields = list(cfg["mismatch_field_mix"].keys())
    weights = list(cfg["mismatch_field_mix"].values())
    chosen = set()

    for _ in range(inj._count("document_mismatch")):
        cid = inj._choose_company(chosen, need_person=False)
        chosen.add(cid)

        field = rng.choices(fields, weights=weights, k=1)[0]
        doc_type = rng.choice(["application", "certificate"])
        mask = (docs["company_id"] == cid) & (docs["doc_type"] == doc_type)
        original = docs.loc[mask, field].iloc[0]

        if field == "registration_number":
            planted, how = _swap_two_digits(original, rng), "two digits swapped"
        else:
            planted, how = _change_address(original, rng)
        docs.loc[mask, field] = planted

        inj._mark_flagged(cid)
        inj._add_key(cid, "document_mismatch", True, None, {
            "field": field, "document": doc_type,
            "original": original, "planted": planted, "how": how,
        })