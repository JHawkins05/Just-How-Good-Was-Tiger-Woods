""" 
TW_1.py & TW_2.py & TW_3.py         jameshawkins          yyyy-mm-dd:2025-04-28
---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8

  This file collects and analyzes PGA Tour player data to explore the 
  career dominance of Tiger Woods. 
  
  Due to complexity and runtime, the code is split into two separate scripts:

  • `TW_1.py` — Sections 0 to 3:
        - Imports
        - Scraping PGA Tour player profiles
        - Cleaning and filtering data
        - Generating figures for blog post

  • `TW_2.py` — Sections 0, 4 and 5:
        - Imports
        - Scraping and filtering historical DataGolf rankings
        - Animation of rankings over time

  • `TW_3.py` — Sections 0, 6 and 7:
        - Imports
        - Scraping and filtering historical DataGolf rankings
        - Animation of strokes gained over time

  Data sources include:
    - PGA Tour Player Profiles: https://www.pgatour.com/players
    - DataGolf Rankings: https://datagolf.com/datagolf-rankings

  The script generates all figures, cleaned datasets, and the animation 
  required for the Quarto blog project.

  Full details related to the replication of this file can be found in the 
  README code in the top level of this directory.

  ChromeDriver must be installed and correctly referenced in the 
  CHROMEDRIVER_PATH variable. All library versions are specified in README.

  Contact: mailto:hawkins.jd@outlook.com
"""



# ============================================================================
# 0. IMPORTS
# ============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.ticker as ticker



# ============================================================================
# 1. SCRAPE DATA FROM PGATOUR.COM
# ============================================================================

# Setup ChromeDriver
CHROMEDRIVER_PATH = "C:/Users/hawki/chromedriver-win64/chromedriver.exe"
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Setup select all players function
def select_all_players(driver):
    # Click the dropdown button
    dropdown_button = driver.find_element(By.CSS_SELECTOR, ".css-1lbp250")
    dropdown_button.click()
    time.sleep(1) 
    # Click the "All Players" option
    all_option = driver.find_element(By.CSS_SELECTOR, ".css-9ylzes")
    all_option.click()
    time.sleep(1) 

# Load main player page and select all players 
driver.get("https://www.pgatour.com/players")
time.sleep(5)
select_all_players(driver) 
time.sleep(2)

# Scroll to load all players
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
    time.sleep(3)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Collect player profile links
player_elements = driver.find_elements(By.CSS_SELECTOR, "a.chakra-linkbox__overlay.css-1hnz6hu")

player_links = []
for el in player_elements:
    name = el.text.strip()
    href = el.get_attribute("href")
    if name and href and "/player/" in href and "/tournaments/" not in href:
        player_links.append((name, href))

# Scraper function returns raw stat dict
def scrape_player(name, url):
    try:
        service = Service(CHROMEDRIVER_PATH)
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url + "/career")
        time.sleep(5)  

        stats_divs = driver.find_elements(By.CSS_SELECTOR, "div.css-11yv56q")
        stats_dict = {"Player": name}
        for div in stats_divs:
            try:
                lines = div.text.strip().split("\n")
                if len(lines) == 2:
                    label, value = lines
                    stats_dict[label.strip().upper()] = value.strip()
            except:
                continue

        driver.quit()
        return stats_dict

    except Exception as e:
        return None

# Run scraping in parallel
raw_data = []
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(scrape_player, name, url) for name, url in player_links]

    for future in as_completed(futures):
        result = future.result()
        if result:
            raw_data.append(result)

driver.quit()

# Convert to dataframe and save to csv
df_raw = pd.DataFrame(raw_data)
df_raw.to_csv("data/pga_raw_data.csv", index=False)



# ============================================================================
# 2. DATA CLEANING
# ============================================================================

df_raw = pd.read_csv("data/pga_raw_data.csv")

# Filter players with more than 20 events played
df_over20starts = df_raw.copy()
df_over20starts["EVENTS PLAYED"] = pd.to_numeric(df_over20starts["EVENTS PLAYED"], errors='coerce')
df_over20starts = df_over20starts[df_over20starts["EVENTS PLAYED"] > 20]

# Convert YEAR JOINED TOUR to numeric
df_post1968 = df_over20starts.copy()
df_post1968["YEAR JOINED TOUR"] = pd.to_numeric(df_post1968["YEAR JOINED TOUR"], errors="coerce")
# Remove players who joined before 1945
df_post1968 = df_post1968[(df_post1968["YEAR JOINED TOUR"].isna()) | (df_post1968["YEAR JOINED TOUR"] >= 1945)]

# Convert key stats to numeric
df_clean = df_post1968.copy()
df_clean["PGA TOUR WINS"] = pd.to_numeric(df_clean["PGA TOUR WINS"], errors='coerce')
df_clean["CUTS MADE"] = pd.to_numeric(df_clean["CUTS MADE"].astype(str).str.split("/").str[0], errors='coerce')
df_clean["TOP 5 FINISHES"] = pd.to_numeric(df_clean["TOP 5 FINISHES"], errors='coerce')
df_clean["TOP 10 FINISHES"] = pd.to_numeric(df_clean["TOP 10 FINISHES"], errors='coerce')

# Calculate Win %
df_clean["Win %"] = df_clean.apply(
    lambda row: round(100 * row["PGA TOUR WINS"] / row["EVENTS PLAYED"], 2)
    if pd.notna(row["EVENTS PLAYED"]) and row["EVENTS PLAYED"] > 0 else 0.0,
    axis=1
)

# Calculate Cuts Made %
df_clean["Cuts Made %"] = df_clean.apply(
    lambda row: round(100 * row["CUTS MADE"] / row["EVENTS PLAYED"], 2)
    if pd.notna(row["EVENTS PLAYED"]) and row["EVENTS PLAYED"] > 0 else 0.0,
    axis=1
)

# Calculate Top 5 %
df_clean["Top 5 %"] = df_clean.apply(
    lambda row: round(100 * row["TOP 5 FINISHES"] / row["EVENTS PLAYED"], 2)
    if pd.notna(row["EVENTS PLAYED"]) and row["EVENTS PLAYED"] > 0 else 0.0,
    axis=1
)

# Calculate Top 10 %
df_clean["Top 10 %"] = df_clean.apply(
    lambda row: round(100 * row["TOP 10 FINISHES"] / row["EVENTS PLAYED"], 2)
    if pd.notna(row["EVENTS PLAYED"]) and row["EVENTS PLAYED"] > 0 else 0.0,
    axis=1
)

# Save cleaned dataframe to csv
df_clean.to_csv("data/pga_clean_data.csv", index=False)



# ============================================================================
# 3. GRAPH BUILDING
# ============================================================================

df_clean = pd.read_csv("data/pga_clean_data.csv")

# Set style globally
sns.set(style="whitegrid")

# ===== New Prime Tiger Woods data =====
# To show how good Tiger Woods was in his prime, we will add data to the graphs for his prime years between 1999 and 2008
prime_tiger = {
    'Player': 'Tiger Woods 99-08',
    'EVENTS PLAYED': 173,
    'PGA TOUR WINS': 56,
    'Win %': 32.3,
    'Cuts Made %': 97.7,
    'Top 5 %': 54.9,
    'Top 10 %': 72.7,
}
# Create Prime Tiger Woods DataFrame
primetw_df = pd.DataFrame([prime_tiger])

# ===== New Prime Jack Nicklaus data =====
# Too compare prime Tiger to probably the second best player of all time, we will add data to the graphs for Jack Nicklaus in his prime years between 1962 and 1975
prime_jack = {
    'Player': 'Jack Nicklaus 62-75',
    'EVENTS PLAYED': 273,
    'PGA TOUR WINS': 54,
    'Win %': 19.8,
    'Cuts Made %': 97.4,
    'Top 5 %': 50.5,
    'Top 10 %': 70.7,
}
primejn_df = pd.DataFrame([prime_jack])


# ===== a) Win Percentage vs Cuts Made Percentage =====

# Create new df that only contains players with valid Win % and Cuts Made %
df_win_cut = df_clean.dropna(subset=["Win %", "Cuts Made %"]).copy()

plt.figure(figsize=(14, 8))
sns.scatterplot(data=df_win_cut, x="Win %", y="Cuts Made %", alpha=0.7)

# List of players to label
players_to_label = ["Tiger Woods", "Rory McIlroy", "Scottie Scheffler", "Jon Rahm", 
                    "Seve Ballesteros", "Phil Mickelson", "Min Woo Lee", "Jack Nicklaus",
                    "Vijay Singh", "Jason Day", "Macdonald Smith", "Willie MacFarlane",
                    "Bryson DeChambeau", "Bubba Watson", "Patrick Cantlay"]

# Add a label for each of the specific players
for i, row in df_win_cut.iterrows():
    if row["Player"] in players_to_label:
        plt.annotate(row["Player"],
                     (row["Win %"], row["Cuts Made %"]),
                     textcoords="offset points", xytext=(0, 5),
                     ha='center', va='bottom',
                     fontsize=8, color='black')

# Add Prime Tiger Woods data
sns.scatterplot(data=primetw_df, x="Win %", y="Cuts Made %", color="red", s=50)
for i, row in primetw_df.iterrows():
    plt.annotate(row["Player"],
                 (row["Win %"], row["Cuts Made %"]),
                 textcoords="offset points", xytext=(0, 10),
                 ha='center', va='bottom',
                 fontsize=8, color='red', weight='bold')

# Add Prime Jack Nicklaus data
sns.scatterplot(data=primejn_df, x="Win %", y="Cuts Made %", color="#4c72b0", alpha=0.7)
for i, row in primejn_df.iterrows():
    plt.annotate(row["Player"],
                 (row["Win %"], row["Cuts Made %"]),
                 textcoords="offset points", xytext=(0, 10),
                 ha='center', va='bottom',
                 fontsize=8, color='black')

# Labels and layout
plt.title("Win % vs Cuts Made % — Players with 20+ Starts")
plt.xlabel("Win Percentage")
plt.ylabel("Cuts Made Percentage")
plt.tight_layout()
plt.savefig("figures/win_vs_cuts.png")


# ===== b) Top 5% and Top 10% Finishes =====

# Create a new DataFrame that only contains players with valid Top 5% and Top 10% values
df_top5and10 = df_clean.dropna(subset=["Top 5 %", "Top 10 %"])

# Remove select players who played pre 1913
players_to_remove = ["Macdonald Smith", "Bobby Locke", "Jim Barnes", "Leo Diegel", "Willie MacFarlane"]
df_top5and10 = df_top5and10[~df_top5and10["Player"].isin(players_to_remove)]

plt.figure(figsize=(14, 8))
sns.scatterplot(data=df_top5and10, x="Top 10 %", y="Top 5 %", alpha=0.7)

# List of players to label
players_to_label = ["Tiger Woods", "Rory McIlroy", "Scottie Scheffler", 
                    "Phil Mickelson", "Min Woo Lee", "Greg Norman",
                    "Jason Day", "Bryson DeChambeau", "Bubba Watson",
                    "Patrick Cantlay", "Victor Ghezzi", "Jack Nicklaus"
                    "Harry Cooper"]

# Add a label for each of the specific players
for i, row in df_top5and10.iterrows():
    if row["Player"] in players_to_label:
        plt.annotate(row["Player"],
                     (row["Top 10 %"], row["Top 5 %"]),
                     textcoords="offset points", xytext=(0, 10),
                     ha='center', va='bottom',
                     fontsize=8, color='black')

# Add Prime Tiger Woods data
sns.scatterplot(data=primetw_df, x="Top 10 %", y="Top 5 %", color="red", s=70)
for i, row in primetw_df.iterrows():
    plt.annotate(row["Player"],
                 (row["Top 10 %"], row["Top 5 %"]),
                 textcoords="offset points", xytext=(0, 10),
                 ha='center', va='bottom',
                 fontsize=8, color='red', weight='bold')

# Add Prime Jack Nicklaus data
sns.scatterplot(data=primejn_df, x="Top 10 %", y="Top 5 %", color="#4c72b0", alpha=0.7)
for i, row in primejn_df.iterrows():
    plt.annotate(row["Player"],
                 (row["Top 10 %"], row["Top 5 %"]),
                 textcoords="offset points", xytext=(0, 10),
                 ha='center', va='bottom',
                 fontsize=8, color='black')

# Labels and layout
plt.title("Top 5% vs Top 10% Finishes — Players with 20+ Starts")
plt.xlabel("% of Finishes in Top 10")
plt.ylabel("% of Finishes in Top 5")
plt.tight_layout()
plt.savefig("figures/top5_vs_top10.png")


# ===== c) Top Career Earnings =====

# Convert OFFICIAL MONEY to numeric
df_clean["OFFICIAL MONEY"] = (
    df_clean["OFFICIAL MONEY"]
    .replace(r'[\$,]', '', regex=True)
    .astype(float)
)

# Create a new DataFrame that only contains players with valid Earnings values
df_top_earnings = df_clean.sort_values("OFFICIAL MONEY", ascending=False).head(20)

plt.figure(figsize=(10, 8))
barplot = sns.barplot(
    data=df_top_earnings,
    x="OFFICIAL MONEY",
    y="Player",
)

# Add earnings labels to bars
for i, row in df_top_earnings.iterrows():
    barplot.text(
        row["OFFICIAL MONEY"] + 100000,
        df_top_earnings.index.get_loc(i),
        f"${row['OFFICIAL MONEY']:,.0f}",
        va="center"
    )

# Format x-axis with dollar formatting
plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))

# Labels and layout
plt.title("PGA Tour Career Earnings — Top 20 All Time", fontsize=14, weight='bold')
plt.xlabel("Official Earnings")
plt.ylabel("")
plt.tight_layout()
plt.savefig("figures/earnings.png")
