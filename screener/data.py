from pathlib import Path

import pandas as pd

FILES = ["persons", "companies", "directors", "ownership_links",
         "documents", "sanctions_list", "high_risk_countries"]


def load_data(folder="data"):
    """Read the detector's inputs. This is the only place the screener reads files."""
    return {name: pd.read_csv(Path(folder) / f"{name}.csv") for name in FILES}