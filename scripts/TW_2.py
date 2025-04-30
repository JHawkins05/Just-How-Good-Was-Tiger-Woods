# ============================================================================
# 0. IMPORTS
# ============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from matplotlib.dates import DateFormatter



# ============================================================================
# 4. SCRAPE DATA FROM DATAGOLF.COM
# ============================================================================

# List of players who have ever been OWGR No. 1 (format: LASTNAME FIRSTNAME)
no1_players = [
    "WOODS TIGER", "NORMAN GREG", "FALDO NICK", "COUPLES FRED", 
    "PRICE NICK", "SINGH VIJAY", "WESTWOOD LEE", "DONALD LUKE", 
    "MCILROY RORY", "SPIETH JORDAN", "DAY JASON", "JOHNSON DUSTIN", 
    "THOMAS JUSTIN", "RAHM JON", "KOEPKA BROOKS", "SCHEFFLER SCOTTIE",
    "WOOSNAM IAN", "LEHMAN TOM", "DUVAL DAVID", "BALLASTEROS SEVE",
    "KAYMER MARTIN", "ELS ERNIE"
]

# Setup ChromeDriver
CHROMEDRIVER_PATH = "C:/Users/hawki/chromedriver-win64/chromedriver.exe"
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Load DataGolf rankings page
driver.get("https://datagolf.com/datagolf-rankings")
# Wait for page to fully load
time.sleep(5)

# Open the date dropdown
driver.find_element(By.CLASS_NAME, "the-selected-date").click()
time.sleep(1)

# Get all date option
date_elements = driver.find_elements(By.CLASS_NAME, "date-option")
date_elements_filtered = date_elements[1::9]  # Skip the most recent then take every 9th reading so we get roughly 6 readings a year

all_data = []

for i, _ in enumerate(date_elements_filtered):
    try:
        # Reopen dropdown each time
        driver.find_element(By.CLASS_NAME, "the-selected-date").click()
        time.sleep(1)

        # Re-fetch dropdown elements
        date_elements = driver.find_elements(By.CLASS_NAME, "date-option")
        date_el = date_elements[1::9][i] 
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

    except Exception as e:
        continue

driver.quit()

# Save to CSV
rankings_df = pd.DataFrame(all_data)
rankings_df.to_csv("data/no1s_rankings.csv", index=False)



# ============================================================================
# 5. ANIMATED GRAPH
# ============================================================================

# ===== Load and prepare data =====
rankings_df = pd.read_csv("data/no1s_rankings.csv")

# Clean up
rankings_df['date'] = pd.to_datetime(rankings_df['date'])

# Keep only top 30 ranks
top30_df = rankings_df[rankings_df['rank'] <= 30]

# Pivot for plotting
pivot_df = top30_df.pivot(index='date', columns='player', values='rank')

# Fill missing with 40 to ensure smooth drop-off
pivot_df = pivot_df.fillna(40)

# ===== Set up figure =====
fig, ax = plt.subplots(figsize=(20, 8))

ax.invert_yaxis()

# Transparent border
for spine in ax.spines.values():
    spine.set_alpha(0.1)

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

# Set title
ax.set_title(
    'Animated Rankings Over Time - Former World No. 1s',
    fontsize=22,
    pad=30 
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

# ===== Animation functions =====

def init():
    ax.set_xlim(pivot_df.index.min(), pivot_df.index.max())
    ax.set_ylim(30, 0)
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
            tiger_x[-1] + pd.Timedelta(days=10),
            tiger_y[-1],
            "Tiger Woods", fontsize=10, color='red',
            ha='left', va='center'
        )

    return list(lines.values()) + list(dots.values()) + [update.tiger_label]

# ===== Create the animation =====
ani = FuncAnimation(
    fig, update, frames=len(pivot_df.index),
    init_func=init, blit=True, interval=30 
)

# Save the animation
plt.rcParams['animation.ffmpeg_path'] = r"C:\ffmpeg\bin\ffmpeg.exe" 
writer = animation.FFMpegWriter(fps=10, metadata=dict(artist='TigerWoodsProject'), bitrate=1800)

ani.save('figures/animated_rankings.mp4', writer=writer, dpi=200)



# ============================================================================

end_time = time.time()
print(f"⏱️ DataGolf elapsed time: {end_time - start_time:.2f} seconds")