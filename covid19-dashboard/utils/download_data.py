"""
Downloads the raw datasets into the data/ folder.

Run this only if a data file is missing (the project already ships with them):
    python utils/download_data.py

Source: Johns Hopkins University CSSE COVID-19 Data Repository
https://github.com/CSSEGISandData/COVID-19  (licensed CC BY 4.0)
"""
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

BASE = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data"
FILES = {
    "time_series_covid19_confirmed_global.csv": f"{BASE}/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv",
    "time_series_covid19_deaths_global.csv": f"{BASE}/csse_covid_19_time_series/time_series_covid19_deaths_global.csv",
    "time_series_covid19_recovered_global.csv": f"{BASE}/csse_covid_19_time_series/time_series_covid19_recovered_global.csv",
    "UID_ISO_FIPS_LookUp_Table.csv": f"{BASE}/UID_ISO_FIPS_LookUp_Table.csv",
}
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for name, url in FILES.items():
        print(f"Downloading {name} ...")
        try:
            with urlopen(url, timeout=60) as response:
                (DATA_DIR / name).write_bytes(response.read())
        except (URLError, TimeoutError) as err:
            print(f"  FAILED: {err}\n  Check your internet connection and try again.")
            return
    print("Done. Files saved in:", DATA_DIR)
    print("Note: data/who_region_mapping.csv is part of the project and is not downloaded.")


if __name__ == "__main__":
    main()
