import numpy as np
import pandas as pd

from evaluation.name_metrics import name_metrics


def test_name_metrics_counts():
    people = pd.DataFrame({"person_id": ["P1", "P2", "P3", "P4"]})
    key = pd.DataFrame({
        "flag_type": ["sanctions_match", "sanctions_match", "look_alike"],
        "person_id": ["P1", "P2", "P3"]})
    alerted = np.array([True, False, True, True])

    m = name_metrics(people, alerted, key)
    assert m["caught"] == 1
    assert m["recall"] == 0.5
    assert m["lookalike_false_alarms"] == 1.0
    assert m["other_false_alarms"] == 1
    assert abs(m["precision"] - 1 / 3) < 1e-9