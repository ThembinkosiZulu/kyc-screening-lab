import random

from rapidfuzz import fuzz

from generator.config import load_config
from generator.sanctions import build_sanctions_list
from generator.variants import make_variant

cfg = load_config()
sanctions = build_sanctions_list(cfg, random.Random("preview-sanctions"))
rng = random.Random("preview")

for entry in sanctions.sample(15, random_state=1).to_dict("records"):
    level = rng.choice([1, 2])
    v = make_variant(entry, level, rng)
    score = fuzz.token_sort_ratio(entry["full_name"], v["name"])
    print(f'{entry["culture"]:14} {entry["full_name"]:28} -> {v["name"]:28} {score:5.1f}  {v["changes"]}')


    