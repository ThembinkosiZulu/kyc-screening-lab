import random
from pathlib import Path

from generator.config import load_config
from generator.clean import build_clean_dataset
from generator.sanctions import build_sanctions_list
from generator.collisions import fix_collisions


def main():
    cfg = load_config()
    tables = build_clean_dataset(cfg, random.Random(f"{cfg['seed']}-clean"))
    sanctions = build_sanctions_list(cfg, random.Random(f"{cfg['seed']}-sanctions"))
    tables["sanctions_list"] = sanctions[["sanction_id", "full_name", "date_of_birth", "country"]]
    tables["persons"], n_fixed = fix_collisions(
        tables["persons"], sanctions, cfg, random.Random(f"{cfg['seed']}-collisions"))
    print(f"people re-rolled to avoid the sanctions list: {n_fixed}")

    out = Path("data")
    out.mkdir(exist_ok=True)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows")


if __name__ == "__main__":
    main()