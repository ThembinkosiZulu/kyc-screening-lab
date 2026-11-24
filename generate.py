import random
from pathlib import Path

from generator.config import load_config
from generator.clean import build_clean_dataset


def main():
    cfg = load_config()
    rng = random.Random(cfg["seed"])
    tables = build_clean_dataset(cfg, rng)

    out = Path("data")
    out.mkdir(exist_ok=True)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows")


if __name__ == "__main__":
    main()