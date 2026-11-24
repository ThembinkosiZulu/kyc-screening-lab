import random

from rapidfuzz import fuzz, utils

from generator.config import load_config
from generator.sanctions import build_sanctions_list
from generator.lookalikes import make_lookalike

cfg = load_config()
sanctions = build_sanctions_list(cfg, random.Random("preview-sanctions"))
names = set(sanctions["full_name"])
rng = random.Random("preview-lookalikes")

for entry in sanctions.sample(12, random_state=2).to_dict("records"):
    la = make_lookalike(entry, cfg, rng, names)
    score = fuzz.token_sort_ratio(entry["full_name"], la["full_name"],
                                  processor=utils.default_process)
    print(f'{entry["full_name"]:28} ~ {la["full_name"]:28} {score:5.1f}  '
          f'DOB {entry["date_of_birth"]} vs {la["date_of_birth"]}')