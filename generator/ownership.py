def links_by_owned_from_table(links):
    """Turn the ownership table into {company: [[owner_type, owner_id, pct], ...]}."""
    out = {}
    for row in links.itertuples():
        out.setdefault(row.owned_company_id, []).append(
            [row.owner_type, row.owner_id, row.pct])
    return out


def effective_stakes(links_by_owned, target, max_depth=25):
    """Total % each person owns in the target: multiply along each path,
    then add up all paths. Raises an error if the chain loops."""
    totals = {}

    def walk(company, factor, depth):
        if depth > max_depth:
            raise RuntimeError("Ownership chain loops or is too deep")
        for owner_type, owner_id, pct in links_by_owned.get(company, []):
            share = factor * pct / 100
            if owner_type == "person":
                totals[owner_id] = totals.get(owner_id, 0.0) + share
            else:
                walk(owner_id, share, depth + 1)

    walk(target, 100.0, 0)
    return totals


def check_ownership(tables):
    """Every company's owners add up to 100%, and no chain loops."""
    links = links_by_owned_from_table(tables["ownership_links"])
    for company, owners in links.items():
        total = round(sum(pct for _, _, pct in owners), 1)
        assert total == 100.0, f"{company} adds up to {total}"
    for company in links:
        effective_stakes(links, company)

def chain_companies(links_by_owned, target, max_depth=25):
    """The target company and every company above it in its ownership chain."""
    found = {target}

    def walk(company, depth):
        if depth > max_depth:
            raise RuntimeError("Ownership chain loops or is too deep")
        for owner_type, owner_id, _ in links_by_owned.get(company, []):
            if owner_type == "company":
                found.add(owner_id)
                walk(owner_id, depth + 1)

    walk(target, 0)
    return found