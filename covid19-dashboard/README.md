# COVID-19 Global Data Analysis Dashboard

An interactive data-analytics project built with **Python, Pandas, NumPy, Streamlit, Plotly, Matplotlib and Seaborn**. It analyses worldwide COVID-19 data across countries and WHO regions, and is careful to separate **reported (actual) data** from **values calculated by this project (derived)**.

## 1. How the project is organised (beginner-friendly)

```
covid19-dashboard/
├── app.py                      Starts the dashboard and builds the sidebar menu
├── requirements.txt            Python libraries to install
├── .streamlit/config.toml      Colours and settings (blue / white / teal theme)
├── data/                       The datasets (already included, so it works offline)
│   ├── time_series_covid19_confirmed_global.csv
│   ├── time_series_covid19_deaths_global.csv
│   ├── time_series_covid19_recovered_global.csv
│   ├── UID_ISO_FIPS_LookUp_Table.csv      country codes and population
│   └── who_region_mapping.csv             which WHO region each country belongs to
├── pages/                      One file per dashboard page
│   ├── 0_Global_Overview.py        KPI cards, top 10, regional split, trends, insights
│   ├── 1_Country_Analysis.py       rankings, country comparison, scatter plot
│   ├── 2_WHO_Region_Analysis.py    cases, deaths, recoveries and trends by region
│   ├── 3_Time_Series_Analysis.py   daily/monthly trends with date filters
│   ├── 4_Maps_and_Heatmaps.py      world map and monthly heatmap
│   ├── 5_Statistical_View.py       Seaborn / Matplotlib statistics
│   └── 6_Data_Quality_and_About.py source, cleaning log, definitions, limitations
└── utils/                      Reusable code shared by all pages
    ├── data_loader.py          reads, cleans and validates the data
    ├── metrics.py              calculations (KPIs, regional totals, daily values)
    ├── charts.py               all Plotly charts in one consistent style
    ├── ui.py                   styling, KPI cards, friendly error messages
    └── download_data.py        re-downloads the data if a file is missing
```

**How data flows:** `data/*.csv` → `utils/data_loader.py` (clean and validate once, then cached) → `utils/metrics.py` (calculate) → `utils/charts.py` (draw) → `pages/*.py` (arrange on screen).

## 2. Install and run (Windows)

1. Install **Python 3.10 or newer** from https://www.python.org/downloads/ . On the first installer screen, tick **"Add python.exe to PATH"**.
2. Unzip the project and open the folder in **VS Code** (File → Open Folder).
3. Open the terminal (Terminal → New Terminal) and run these commands one by one:

```
python --version
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

4. Your browser opens at http://localhost:8501 . Press `Ctrl + C` in the terminal to stop.

Next time, you only need:
```
venv\Scripts\activate
python -m streamlit run app.py
```

If PowerShell blocks `activate`, choose **Command Prompt** from the terminal dropdown, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

The world map downloads its outline from the internet, so it needs a connection. If a data file is ever missing, the app shows a message; fix it with `python utils/download_data.py`.

**Low-RAM friendly:** the cleaned data is about 26 MB in memory and is cached, and there is no animation or heavy processing.

## 3. Data source and coverage

- **Source:** Johns Hopkins University CSSE COVID-19 Data Repository (https://github.com/CSSEGISandData/COVID-19), licensed CC BY 4.0.
- **Coverage:** 22 January 2020 to 9 March 2023, 201 countries/regions. The source stopped updating after that date.
- **WHO regions:** `data/who_region_mapping.csv` is a reference table compiled for this project from WHO's regional groupings (not part of the JHU data). Non-member entries such as Kosovo, Taiwan and the Holy See are noted in the file.

## 4. Data cleaning and honesty rules

| Step | What was done |
|---|---|
| Duplicates | Checked for duplicate province/country rows (none found). |
| Validation | Every value converted to a number; non-numeric cells counted (none found). |
| Country names | 11 inconsistent names standardised (for example `US` to United States, `Burma` to Myanmar). The original name is kept. |
| Provinces | Combined into country totals. |
| Cumulative corrections | The source sometimes lowers a cumulative total. These are counted (171 for confirmed, 199 for deaths) and daily values are floored at zero in charts. |
| Recovered data | The source **stopped publishing recoveries on 4 Aug 2021** (later values are zeros, not real). Those later dates are left empty. |
| Recovered coverage | 188 countries still reported at that date. 10 never reported and 3 (United States, Belgium, Serbia) stopped earlier. They are left out of recovered and active totals for **all** dates so totals stay comparable. This covers about 81% of confirmed cases. |
| Active cases | **Derived** as confirmed − deaths − recovered, only for reporting countries, and left empty where the result would be negative (459 country-days). |
| Missing values | Never filled in or estimated. |

**Actual vs derived:** confirmed, deaths and recovered are *actual* (reported). Death rate, active cases, daily values, 7-day averages and per-100,000 figures are *derived* and labelled as such in the dashboard.

## 5. Dashboard features

- **Global overview:** KPI cards (confirmed, deaths, death rate, recovered, active), WHO-region donut, top 10 countries, global trends, auto-generated insights.
- **Country analysis:** choose date, regions, metric and number of countries; compare any countries (cumulative or 7-day average, per 100,000 people, log scale); confirmed-vs-deaths scatter plot.
- **WHO regions:** cases, deaths, recovered, death rate, shares and trends by region.
- **Time series:** global, region or country scope; date range slider; daily or monthly; new or cumulative; 7-day average.
- **Maps and heatmaps:** interactive world map (5 metrics, date slider, log colour scale) and a country-by-month heatmap.
- **Statistical view (Seaborn/Matplotlib):** death-rate distribution by region, per-capita distribution, Spearman correlation heatmap.
- **Data quality:** source, date coverage, cleaning log, definitions, limitations.

## 6. Key findings (as of 9 March 2023, calculated from the data)

- Global totals: **676,570,149 confirmed cases** and **6,881,802 deaths**, a reported death rate of **1.02%**.
- The **United States** reported the most confirmed cases (103.8 million); the top five countries together account for **39.0%** of all confirmed cases.
- **Europe** has the largest share of confirmed cases (**40.8%**), then the Americas (28.2%) and the Western Pacific (17.3%).
- **Africa** has the highest reported death rate by region (1.94%) and the Western Pacific the lowest (0.34%). Lower reported cases in Africa partly reflect limited testing, so this ratio should not be read as true mortality.
- The 7-day average of new confirmed cases peaked at about **3.44 million per day around 24 January 2022**, while the deaths peak was about **14,860 per day around 26 January 2021**. Later waves had far more recorded cases per death than the early ones.
- Among countries with at least 100,000 cases, reported death rates range from **0.08% (Singapore) to 4.89% (Peru)**.
- Relative to population, **Austria** had the highest confirmed cases per 100,000 people among countries above 1 million population.

The first five findings follow from the dashboard's numbers. The sentence about later waves is an interpretation of the two peak dates and values, not a causal claim.

## 7. Limitations

- Reported cases are not true infections; testing and reporting differ by country and over time.
- Death rate is a reported ratio, affected by testing, reporting delays and age structure.
- Recovered and active cases are incomplete (see section 4).
- Population is one fixed value per country, so per-100,000 figures are approximate.
- The WHO region table is compiled by hand and should be checked against WHO if exact grouping matters.

## 8. Interview explanation

**One-minute summary:** "I built an interactive COVID-19 analytics dashboard in Python using Johns Hopkins data for 201 countries over three years. I cleaned and validated the data with Pandas, aggregated it by country and WHO region, and built a seven-page Streamlit app with Plotly charts, a world map, heatmaps and Seaborn statistics. A key part was data integrity: the source stopped publishing recoveries in 2021 and some countries never reported them, so I excluded those from recovered and active totals instead of showing misleading numbers, and I labelled every metric as actual or derived."

**Questions you may be asked:**
- *Why not show active cases worldwide?* Because recoveries are missing after Aug 2021 and for some countries, so the calculation would be wrong. I show it only where it is reliable and say so.
- *How did you get daily cases?* By differencing the cumulative totals per country. The source sometimes corrects totals downwards, so I counted those corrections and floored daily values at zero in charts.
- *Why compare per 100,000 people?* Raw counts mostly reflect population size. Per-capita values make countries comparable.
- *Why a minimum case count for death rates?* Tiny counts give unstable percentages.
- *How did you keep it fast?* Data is loaded and cleaned once, cached with `st.cache_data`, and kept in memory at about 26 MB.
- *What would you improve?* Add vaccination and testing data, age-adjusted rates, and a forecasting page with clear uncertainty.

## 9. Resume-ready description

**COVID-19 Global Data Analysis Dashboard** | Python, Pandas, NumPy, Streamlit, Plotly, Seaborn
- Built a seven-page interactive dashboard analysing Johns Hopkins CSSE COVID-19 data for 201 countries (Jan 2020 to Mar 2023), covering KPIs, country and WHO-region comparisons, time-series trends, a choropleth map and heatmaps.
- Cleaned and validated three time-series datasets with Pandas: checked duplicates and non-numeric values, standardised 11 country names, merged province-level rows, and mapped countries to WHO regions.
- Identified that recovered-case data was discontinued in August 2021 and incomplete for some countries, and excluded unreliable values instead of estimating them. Labelled metrics as actual or derived.
- Derived daily cases, 7-day averages, death rates and per-100,000 metrics, and documented data limitations in an in-app data-quality page.

## 10. Upload to GitHub

1. Create a free account at https://github.com and click **New repository**. Name it `covid19-dashboard`, keep it Public, and do **not** tick "Add a README".
2. Install Git from https://git-scm.com/download/win if needed.
3. In the VS Code terminal, inside the project folder, run:

```
git init
git add .
git commit -m "COVID-19 Global Data Analysis Dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/covid19-dashboard.git
git push -u origin main
```

(Replace `YOUR-USERNAME`. Do not upload the `venv` folder; the included `.gitignore` already excludes it.)

4. Optional free hosting: go to https://share.streamlit.io, sign in with GitHub, choose the repository, set the main file to `app.py`, and deploy. Once deployed, add the real repository link to your portfolio.

## Credits

Data: Johns Hopkins University Center for Systems Science and Engineering (CC BY 4.0). WHO regional groupings follow WHO's published regions.
