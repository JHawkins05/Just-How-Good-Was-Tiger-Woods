# ============================================================================
# 0. IMPORTS
# ============================================================================

import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation



# ============================================================================
# 6. SCRAPE DATA FROM DATAGOLF.COM (Strokes Gained)
# ============================================================================


# Setup ChromeDriver
CHROMEDRIVER_PATH = "C:/Users/hawki/chromedriver-win64/chromedriver.exe"
service = Service(CHROMEDRIVER_PATH)
options = Options()
driver = webdriver.Chrome(service=service, options=options)

# Define years to scrape
years = list(range(2004, 2026)) 

# List to hold data
all_data = []

for year in years:
    try:
        url = f"https://datagolf.com/stats/tour-lists?tour=pga&year={year}&sg=raw"
        driver.get(url)
        time.sleep(4)  # Wait for content to load

        # Get all player rows
        rows = driver.find_elements(By.CSS_SELECTOR, "div.datarow.lists-datarow")
        
        # Take top 10 rows (rank determined by Total SG)
        for i, row in enumerate(rows[:15]):
            try:
                name_el = row.find_element(By.CSS_SELECTOR, "div.data.lists-col.player-col")
                sg_total_el = row.find_element(By.CSS_SELECTOR, "div.data.lists-col.tour-sg-col.total-col")
                rounds_el = row.find_element(By.CSS_SELECTOR, "div.data.lists-col.rounds-col")

                name = name_el.text.strip()
                sg_total = float(sg_total_el.text.strip().split()[0])  # just the number part
                rounds_raw = rounds_el.text.strip()
                rounds_clean = rounds_raw.split('\n')[0]  # take only first number (total rounds)
                rounds = int(rounds_clean)

                all_data.append({
                    "year": year,
                    "player": name,
                    "sg_total": sg_total,
                    "rounds": rounds,
                    "rank": i + 1
                })
            except Exception as e:
                continue

    except Exception as e:
        continue

driver.quit()

# Convert to DataFrame
sg_df = pd.DataFrame(all_data)
sg_df.to_csv("data/strokes_gained.csv", index=False)



# ============================================================================
# 7. ANIMATED GRAPH (Strokes Gained)
# ============================================================================
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation

# Load data
df = pd.read_csv("data/strokes_gained.csv")
df["year"] = df["year"].astype(int)

# Create pivot (year x player)
pivot_df = df.pivot(index='year', columns='player', values='sg_total').fillna(0)
players = pivot_df.columns
years = pivot_df.index

# Build interpolated values with 10 steps between each year
interpolated_rows = []
for i in range(len(years) - 1):
    year_start = years[i]
    year_end = years[i + 1]
    start_vals = pivot_df.loc[year_start]
    end_vals = pivot_df.loc[year_end]
    for step in range(10):
        alpha = step / 10
        row = start_vals * (1 - alpha) + end_vals * alpha
        interpolated_rows.append(row)
interpolated_rows.append(pivot_df.loc[years[-1]])  # Final year

# Create interpolated DataFrame
pivot_df_interp = pd.DataFrame(interpolated_rows).reset_index(drop=True)

# X-axis setup (1 tick per real year)
xticks = [i * 10 for i in range(len(years))]
xtick_labels = [str(y) for y in years]

# Set up plot
fig, ax = plt.subplots(figsize=(20, 10))
colors = plt.cm.tab20.colors

ax.set_xlim(0, len(pivot_df_interp))
ax.set_ylim(1.4, pivot_df.max().max() + 0.2)
ax.set_xticks(xticks)
ax.set_xticklabels(xtick_labels, rotation=45)
ax.set_title("Strokes Gained – Top 10 Players Per Year", fontsize=24, pad=20)
ax.set_xlabel("Year", fontsize=14)
ax.set_ylabel("Total Strokes Gained", fontsize=14)
ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)

# Plot lines and store final dots + labels
lines = {}
dots = {}
labels = {}

for i, player in enumerate(players):
    color = "red" if player == "Tiger Woods" else colors[i % len(colors)]
    line, = ax.plot([], [], color=color, linewidth=5 if player == "Tiger Woods" else 3, label=player)
    dot, = ax.plot([], [], 'o', color=color, markersize=10 if player == "Tiger Woods" else 6)
    lbl = ax.text(0, 0, "", fontsize=12, color=color, va='center', ha='left')
    lines[player] = line
    dots[player] = dot
    labels[player] = lbl

def init():
    for player in players:
        lines[player].set_data([], [])
        dots[player].set_data([], [])
        labels[player].set_text("")
    return list(lines.values()) + list(dots.values()) + list(labels.values())

def update(frame):
    xdata = list(range(frame + 1))
    for player in players:
        ydata = pivot_df_interp[player].values[:frame + 1]
        lines[player].set_data(xdata, ydata)
        dots[player].set_data([xdata[-1]], [ydata[-1]])
        labels[player].set_position((xdata[-1] + 0.5, ydata[-1]))
        labels[player].set_text(f"{player} {ydata[-1]:.2f}" if ydata[-1] > 0 else "")
    return list(lines.values()) + list(dots.values()) + list(labels.values())

# Animate
ani = FuncAnimation(fig, update, frames=len(pivot_df_interp), init_func=init, blit=True, interval=200)

# Save
plt.rcParams['animation.ffmpeg_path'] = r"C:\ffmpeg\bin\ffmpeg.exe"
writer = animation.FFMpegWriter(fps=7, metadata=dict(artist='TigerWoodsProject'), bitrate=1800)
ani.save('figures/animated_strokesgained.mp4', writer=writer, dpi=200)
