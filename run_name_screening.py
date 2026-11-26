from evaluation.name_metrics import load_key, sweep
from screener.data import load_data
from screener.name_match import rule_a, rule_b, score_names
from screener.normalise import normalise_baseline, normalise_improved

data = load_data()
key = load_key()

setups = {"baseline": normalise_baseline, "improved": normalise_improved}
rules = {
    "A name only": (rule_a, range(30, 101)),
    "B name + DOB": (rule_b, range(30, 91)),
}

results = {}
for label, normalise in setups.items():
    ns = score_names(data, normalise)
    print(f"{label}: screened {len(ns.people)} people against {len(ns.sanction_ids)} sanctions entries")
    for rule_name, (rule, thresholds) in rules.items():
        results[(label, rule_name)] = sweep(ns, rule, thresholds, key)

show = [40, 50, 60, 70, 80, 90, 100]
for (label, rule_name), df in results.items():
    print(f"\n{label} normalisation | rule {rule_name}")
    view = df[df["threshold"].isin(show)].round(3)
    print(view.to_string(index=False))

print("\nSTRICTEST THRESHOLD THAT KEEPS RECALL AT 95% OR MORE")
for (label, rule_name), df in results.items():
    ok = df[df["recall"] >= 0.95]
    if ok.empty:
        print(f"{label:9} {rule_name:13} recall of 95% is never reached")
        continue
    best = ok.sort_values("threshold").iloc[-1]
    print(f"{label:9} {rule_name:13} threshold {int(best['threshold'])} | "
          f"recall {best['recall']:.3f} | "
          f"look-alike false alarms {best['lookalike_false_alarms']:.3f} | "
          f"other false alarms {int(best['other_false_alarms'])} | "
          f"precision {best['precision']:.3f}")