import random
from pathlib import Path

from generator.config import load_config
from generator.clean import build_clean_dataset
from generator.sanctions import build_sanctions_list
from generator.collisions import fix_collisions
from generator.inject import Injector


def main():
    cfg = load_config()
    seed = cfg["seed"]

    tables = build_clean_dataset(cfg, random.Random(f"{seed}-clean"))
    sanctions = build_sanctions_list(cfg, random.Random(f"{seed}-sanctions"))
    tables["persons"], n_fixed = fix_collisions(
        tables["persons"], sanctions, cfg, random.Random(f"{seed}-collisions"))
    print(f"people re-rolled to avoid the sanctions list: {n_fixed}")

    injector = Injector(tables, sanctions, cfg, random.Random(f"{seed}-inject"))
    injector.plant_sanctions_matches()
    injector.plant_lookalikes()
    persons, answer_key = injector.results()

    # the detector only gets the columns the spec asks for
    tables["persons"] = persons[["person_id", "full_name", "date_of_birth", "country"]]
    tables["sanctions_list"] = sanctions[["sanction_id", "full_name", "date_of_birth", "country"]]

    out, key_dir = Path("data"), Path("answer_key")
    out.mkdir(exist_ok=True)
    key_dir.mkdir(exist_ok=True)

    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows")

    answer_key.to_csv(key_dir / "answer_key.csv", index=False)
    print(f"answer_key: {len(answer_key)} rows")        


if __name__ == "__main__":
    main()