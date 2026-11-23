import random
from generator.names import make_name, CULTURES


def test_every_culture_makes_a_name():
    rng = random.Random(1)
    for culture in CULTURES:
        name = make_name(culture, rng)
        assert name["given_name"]
        assert name["family_name"]
        assert name["full_name"]


def test_same_seed_gives_same_name():
    a = make_name("spanish", random.Random(5))
    b = make_name("spanish", random.Random(5))
    assert a == b