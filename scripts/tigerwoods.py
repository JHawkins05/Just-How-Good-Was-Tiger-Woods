""" 1_MAIN_script.py         jameshawkins             yyyy-mm-dd:2025-04-28
---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8

  This file collects and analyzes PGA Tour player data to explore the 
  career dominance of Tiger Woods. It does so by scraping player statistics, 
  cleaning the dataset, visualizing key performance measures, and creating 
  an animated ranking of former World No. 1 players.

  Data sources include:
    - PGA Tour Player Profiles: https://www.pgatour.com/players
    - DataGolf Rankings: https://datagolf.com/datagolf-rankings

  The script generates all figures, cleaned datasets, and the animation 
  required for the Quarto blog project.

  Full details related to the replication of this file can be found in the 
   README code in the top level of this directory.

  ChromeDriver must be installed and correctly referenced in the CHROMEDRIVER_PATH 
  variable on line 63. All library versions are specified in README.

  Contact: mailto:hawkins.jd@outlook.com
"""



# ============================================================================
# 0. IMPORTS
# ============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from matplotlib.dates import DateFormatter



# ============================================================================
# 1. SCRAPE DATA FROM PGATOUR.COM
# ============================================================================

import time
start_time = time.time()

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Setup ChromeDriver
CHROMEDRIVER_PATH = "C:/Users/hawki/chromedriver-win64/chromedriver.exe"
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Setup select all players function
def select_all_players(driver):
    try:
        # Click the dropdown button
        dropdown_button = driver.find_element(By.CSS_SELECTOR, ".css-1lbp250")
        dropdown_button.click()
        time.sleep(1)  # Give dropdown time to open

        # Click the "All Players" option
        all_option = driver.find_element(By.CSS_SELECTOR, ".css-9ylzes")
        all_option.click()
        time.sleep(1)  # Allow page to refresh

        print("✅ 'All Players' selected.")
    
    except Exception as e:
        print(f"❌ Failed to select 'All Players': {e}")

# Load main player page and select all players 
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://www.pgatour.com/players")
time.sleep(5)
select_all_players(driver)  # Selects All Players (not just Active)
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

driver.quit()

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
        print(f"✅ {name} scraped.")
        return stats_dict

    except Exception as e:
        print(f"❌ ERROR for {name}: {e}")
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

# Convert to dataframe and print
df_raw = pd.DataFrame(raw_data)
print("\n=== RAW DATAFRAME (UNCLEANED) ===")
print(df_raw)
df_raw.to_csv("data/pga_raw_data.csv", index=False)

end_time = time.time()
print(f"⏱️ PGA tour scrape: {end_time - start_time:.2f} seconds")  # 6236 seconds for 2518 players (104 minutes)



# ============================================================================
# 2. DATA CLEANING
# ============================================================================

import pandas as pd
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

# Save cleaned DataFrame
df_clean.to_csv("data/pga_clean_data.csv", index=False)



# ============================================================================
# 3. GRAPH BUILDING
# ============================================================================

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Load cleaned data
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



# ============================================================================
# 4. SCRAPE DATA FROM DATAGOLF.COM
# ============================================================================

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ⏱️ Start timing
start_time = time.time()

# List of players who have ever been OWGR No. 1 (format: LASTNAME FIRSTNAME)       taken our Ian Woosnam, Tom Lehman, David Duval, Seve Ballesteros, Martin Kaymer, Ernie Els
no1_players = [
    "WOODS TIGER", "NORMAN GREG", "FALDO NICK", "COUPLES FRED", 
    "PRICE NICK", "SINGH VIJAY", "WESTWOOD LEE", "DONALD LUKE", 
    "MCILROY RORY", "SPIETH JORDAN", "DAY JASON", "JOHNSON DUSTIN", 
    "THOMAS JUSTIN", "RAHM JON", "KOEPKA BROOKS", "SCHEFFLER SCOTTIE",
    "WOOSNAM IAN", "LEHMAN TOM", "DUVAL DAVID", "BALLASTEROS SEVE",
    "KAYMER MARTIN", "ELS ERNIE"
]

# Setup ChromeDriver
options = Options()
# options.add_argument('--headless')  # uncomment to run in background
driver = webdriver.Chrome(options=options)
driver.get("https://datagolf.com/datagolf-rankings")

# Wait for page to fully load
time.sleep(5)

# Open the date dropdown
driver.find_element(By.CLASS_NAME, "the-selected-date").click()
time.sleep(1)

# Get all date option
date_elements = driver.find_elements(By.CLASS_NAME, "date-option")
date_elements_filtered = date_elements[1::13]  # Skip the most recent then take every 13th reading so we get 4 readings a year

all_data = []

for i, _ in enumerate(date_elements_filtered):
    try:
        # Reopen dropdown each time
        driver.find_element(By.CLASS_NAME, "the-selected-date").click()
        time.sleep(1)

        # Re-fetch dropdown elements
        date_elements = driver.find_elements(By.CLASS_NAME, "date-option")
        date_el = date_elements[1::13][i] 
        date_el.click()
        time.sleep(2)

        # Grab full date from selected date box (with year)
        date_str = driver.find_element(By.CLASS_NAME, "the-selected-date").text.strip()

        # Get player rows
        rows = driver.find_elements(By.CSS_SELECTOR, "div.datarow")

        for row in rows:
            try:
                # Extract player name and uppercase for matching
                name_el = row.find_element(By.CSS_SELECTOR, "div.data.name-col.qual-pop")
                name = name_el.text.strip().upper()

                if name not in no1_players:
                    continue

                # Extract DataGolf rank
                rank_el = row.find_element(By.CSS_SELECTOR, "div.data.rank-col.dg-rank-col")
                rank = int(rank_el.text.strip())

                # Save record with title-case name for nice formatting
                record = {"date": date_str, "player": name.title(), "rank": rank}
                all_data.append(record)

            except Exception as e:
                print(f"⚠️ Skipping row due to error: {e}")
                continue

        print(f"✅ Collected data for {date_str}")

    except Exception as e:
        print(f"❌ Error on date index {i}: {e}")
        continue

# Quit browser
driver.quit()

# Save to CSV
rankings_df = pd.DataFrame(all_data)
rankings_df.to_csv("data/no1s_rankings.csv", index=False)

# Show preview
print("\n📊 Preview:")
print(rankings_df.head())
print("\n📁 Saved as 'no1s_rankings.csv'")

end_time = time.time()
print(f"⏱️ DataGolf Scrape: {end_time - start_time:.2f} seconds")


# ============================================================================
# 5. ANIMATED GRAPH
# ============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from matplotlib.dates import DateFormatter
import os

# === Step 1: Load and prepare data ===
rankings_df = pd.read_csv("data/no1s_rankings.csv")

# Clean up
rankings_df['date'] = pd.to_datetime(rankings_df['date'])

# Keep only top 50 ranks
top50_df = rankings_df[rankings_df['rank'] <= 50]

# Pivot for plotting
pivot_df = top50_df.pivot(index='date', columns='player', values='rank')

# Fill missing with 101 to ensure smooth drop-off
pivot_df = pivot_df.fillna(101)

# === Step 2: Set up figure ===
fig, ax = plt.subplots(figsize=(20, 8))

ax.invert_yaxis()

# Light, transparent border
for spine in ax.spines.values():
    spine.set_alpha(0.3)

colours = [
    "#1f77b4",  # Medium Blue
    "#17becf",  # Cyan / Light Blue
    "#2ca02c",  # Green
    "#9467bd",  # Purple
    "#7f7f7f",  # Medium Gray
    "#8c564b",  # Brownish Gray
    "#aec7e8",  # Light Blue
    "#98df8a",  # Light Green
    "#c5b0d5",  # Lavender
    "#9edae5",  # Light Cyan
    "#6baed6",  # Softer Blue
    "#31a354",  # Forest Green
    "#756bb1",  # Deep Purple
    "#636363",  # Dark Gray
    "#74c476",  # Mint Green
]


# Date formatting
ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))

# Labels
ax.set_title('Animated Rankings Over Time - Former World No. 1s', fontsize=20)
ax.set_xlabel('Date', fontsize=14)
ax.set_ylabel('Rank', fontsize=14)
ax.grid(True, linestyle='--', linewidth=0.5)

# Initialize lines and dots
lines = {}
dots = {}
color_index = 0

for player in pivot_df.columns:
    if player == "Woods Tiger":
        lines[player], = ax.plot([], [], label=player, color='#FF0000', linewidth=4)
        dots[player], = ax.plot([], [], 'o', color='#FF0000', markersize=8)
    else:
        color = colours[color_index % len(colours)]
        lines[player], = ax.plot([], [], label=player, color=color, linewidth=2.5)
        dots[player], = ax.plot([], [], 'o', color=color, markersize=6)
        color_index += 1

# Set title nicely
ax.set_title(
    'Animated Rankings Over Time - Former World No. 1s',
    fontsize=22,
    pad=30  # Move title up
)

# Legend clean and inside
ax.legend(
    title="Player",
    loc='center left',
    bbox_to_anchor=(1.01, 0.5),
    fontsize='small',
    frameon=False
)

# Tight layout to remove excess white space
fig.tight_layout(pad=2.0)

# === Step 3: Animation functions ===

def init():
    ax.set_xlim(pivot_df.index.min(), pivot_df.index.max())
    ax.set_ylim(50, 0)  # Space above rank 1
    for line in lines.values():
        line.set_data([], [])
    for dot in dots.values():
        dot.set_data([], [])
    return list(lines.values()) + list(dots.values())

def update(frame):
    for player in pivot_df.columns:
        ydata = pivot_df[player].values[:frame+1]
        xdata = pivot_df.index[:frame+1]
        lines[player].set_data(xdata, ydata)
        dots[player].set_data([xdata[-1]], [ydata[-1]])

    # Tiger Woods moving label
    tiger_x = pivot_df.index[:frame+1]
    tiger_y = pivot_df['Woods Tiger'].values[:frame+1]

    if hasattr(update, 'tiger_label'):
        update.tiger_label.remove()

    if len(tiger_x) > 0:
        update.tiger_label = ax.text(
            tiger_x[-1] + pd.Timedelta(days=10),  # Slightly to the right
            tiger_y[-1],
            "Tiger Woods", fontsize=10, color='red',
            ha='left', va='center'
        )

    return list(lines.values()) + list(dots.values()) + [update.tiger_label]

# === Step 4: Create the animation ===
ani = FuncAnimation(
    fig, update, frames=len(pivot_df.index),
    init_func=init, blit=True, interval=30 
)

# Ensure figures/ directory exists
os.makedirs('figures', exist_ok=True)

# Save the animation
plt.rcParams['animation.ffmpeg_path'] = r"C:\ffmpeg\bin\ffmpeg.exe"  # Adjust if needed
writer = animation.FFMpegWriter(fps=10, metadata=dict(artist='TigerWoodsProject'), bitrate=1800)

ani.save('figures/animated_rankings.mp4', writer=writer, dpi=200)

# plt.show()
