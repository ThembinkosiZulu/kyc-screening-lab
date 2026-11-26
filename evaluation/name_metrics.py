import numpy as np
import pandas as pd


def load_key(path="answer_key/answer_key.csv"):
    return pd.read_csv(path)


def name_metrics(people, alerted, key):
    """Score alerts against the answer key. `alerted` lines up with `people`."""
    match_ids = set(key.loc[key["flag_type"] == "sanctions_match", "person_id"])
    look_ids = set(key.loc[key["flag_type"] == "look_alike", "person_id"])
    is_match = people["person_id"].isin(match_ids).to_numpy()
    is_look = people["person_id"].isin(look_ids).to_numpy()

    n_alerts = int(alerted.sum())
    caught = int((alerted & is_match).sum())
    look_flagged = int((alerted & is_look).sum())

    return {
        "alerts": n_alerts,
        "caught": caught,
        "recall": caught / max(int(is_match.sum()), 1),
        "precision": caught / n_alerts if n_alerts else np.nan,
        "lookalike_false_alarms": look_flagged / max(int(is_look.sum()), 1),
        "other_false_alarms": n_alerts - caught - look_flagged,
    }


def sweep(ns, rule, thresholds, key):
    """Run a rule at many thresholds and collect the metrics."""
    rows = []
    for t in thresholds:
        rows.append({"threshold": t, **name_metrics(ns.people, rule(ns, t), key)})
    return pd.DataFrame(rows)