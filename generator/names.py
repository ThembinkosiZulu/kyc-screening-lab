import random

CULTURES = ["chinese", "spanish", "german", "arabic", "south_african"]

CHINESE_FAMILY = ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang",
                  "Huang", "Zhao", "Wu", "Zhou", "Xu", "Sun"]
CHINESE_SYLLABLES = ["Wei", "Xiao", "Ming", "Hua", "Jing", "Lei",
                     "Yan", "Fang", "Jun", "Hao", "Ting", "Qiang"]

SPANISH_GIVEN = ["Carlos", "José", "María", "Lucía", "Javier", "Ana",
                 "Miguel", "Sofía", "Pablo", "Elena", "Diego", "Carmen"]
SPANISH_FAMILY = ["García", "Gómez", "Ruiz", "Fernández", "López", "Martínez",
                  "Sánchez", "Pérez", "Romero", "Torres", "Navarro", "Ortega"]

GERMAN_GIVEN = ["Anna", "Lukas", "Hans", "Greta", "Jonas", "Katrin",
                "Felix", "Heidi", "Stefan", "Lena", "Markus", "Ingrid"]
GERMAN_FAMILY = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Becker",
                 "Hoffmann", "Wagner", "Koch", "Richter", "Strauß", "Berg"]
GERMAN_PREFIXES = ["von", "zu", "von der"]

ARABIC_GIVEN = ["Mohammed", "Ahmed", "Fatima", "Omar", "Layla", "Hassan",
                "Yusuf", "Amira", "Khalid", "Noor", "Ibrahim", "Samira"]
ARABIC_FAMILY = ["Hassan", "Rahman", "Saleh", "Nasser", "Haddad",
                 "Mansour", "Karim", "Farouk", "Aziz", "Khoury"]

SA_GIVEN = ["Thandi", "Sipho", "Nomsa", "Johan", "Lerato", "Pieter",
            "Zanele", "Thabo", "Annelie", "Bongani", "Palesa", "Willem"]
SA_FAMILY = ["Dlamini", "Nkosi", "Mokoena", "Khumalo", "Naidoo",
             "Botha", "Pretorius", "Ndlovu", "Sithole", "Venter"]
SA_AFRIKAANS = [("van der", "Merwe"), ("du", "Plessis"),
                ("van", "Wyk"), ("le", "Roux")]


def make_name(culture, rng):
    """Build one fictional person's name, as separate parts plus the full string."""
    given = family = second = prefix = None

    if culture == "chinese":
        family = rng.choice(CHINESE_FAMILY)
        syllables = rng.sample(CHINESE_SYLLABLES, rng.choice([1, 2]))
        given = syllables[0] + "".join(s.lower() for s in syllables[1:])
        full = f"{family} {given}"

    elif culture == "spanish":
        given = rng.choice(SPANISH_GIVEN)
        family, second = rng.sample(SPANISH_FAMILY, 2)
        full = f"{given} {family} {second}"

    elif culture == "german":
        given = rng.choice(GERMAN_GIVEN)
        family = rng.choice(GERMAN_FAMILY)
        if rng.random() < 0.15:
            prefix = rng.choice(GERMAN_PREFIXES)
            full = f"{given} {prefix} {family}"
        else:
            full = f"{given} {family}"

    elif culture == "arabic":
        given = rng.choice(ARABIC_GIVEN)
        family = rng.choice(ARABIC_FAMILY)
        if rng.random() < 0.5:
            prefix = "Al-"
            full = f"{given} {prefix}{family}"
        else:
            full = f"{given} {family}"

    elif culture == "south_african":
        given = rng.choice(SA_GIVEN)
        if rng.random() < 0.25:
            prefix, family = rng.choice(SA_AFRIKAANS)
            full = f"{given} {prefix} {family}"
        else:
            family = rng.choice(SA_FAMILY)
            full = f"{given} {family}"

    else:
        raise ValueError(f"Unknown culture: {culture}")

    return {
        "given_name": given,
        "family_name": family,
        "second_surname": second,
        "name_prefix": prefix,
        "full_name": full,
    }

    

