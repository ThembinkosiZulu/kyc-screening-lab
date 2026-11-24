from pathlib import Path
import yaml


def load_config(path="config/config.yaml"):
    cfg = yaml.safe_load(Path(path).read_text())
    validate(cfg)
    return cfg


def validate(cfg):
    assert 300 <= cfg["n_companies"] <= 500, "n_companies must be 300-500"
    assert 200 <= cfg["n_sanctions_entries"] <= 500, "sanctions list must be 200-500"
    assert 0 < cfg["ownership_threshold_pct"] < 100
    assert abs(sum(cfg["variant_level_mix"].values()) - 1.0) < 1e-9, "variant mix must sum to 1"
    assert 0 < cfg["collision_max_similarity"] <= 100, "collision limit must be between 0 and 100"
    assert abs(sum(cfg["high_risk_mode_mix"].values()) - 1.0) < 1e-9, "high-risk mode mix must sum to 1"
    assert abs(sum(cfg["mismatch_field_mix"].values()) - 1.0) < 1e-9, "mismatch field mix must sum to 1"

    for flag, rate in cfg["rates"].items():
        assert 0 <= rate <= 1, f"rate for {flag} must be between 0 and 1"

    assert abs(sum(cfg["cultures"].values()) - 1.0) < 1e-9, "culture weights must sum to 1"

    lo, hi = cfg["chain_depth"]["before_evasion"]
    assert 2 <= lo <= hi, "hidden owners need depth of at least 2"
    lo2, hi2 = cfg["chain_depth"]["after_evasion"]
    assert lo2 <= hi2

    assert 1 <= cfg["evasion_period"] <= cfg["n_periods"]
    assert not set(cfg["high_risk_countries"]) & set(cfg["low_risk_countries"]), \
        "a country cannot be both high-risk and low-risk"
    lo, hi = cfg["hidden_owner_stake_range"]
    assert cfg["ownership_threshold_pct"] < lo <= hi < 100, "hidden owners must sit above the threshold"
    lo, hi = cfg["near_miss_stake_range"]
    assert 0 < lo <= hi < cfg["ownership_threshold_pct"], "near misses must sit below the threshold"