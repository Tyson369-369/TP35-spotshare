import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter

# Data
years = [2017, 2018, 2019, 2020, 2021]
vehicles_added = [209495, 214408, 236429, 215728, 188855]
growth_rate = [4.2, 4.2, 4.5, 4.0, 3.5]

# Plot
fig, ax1 = plt.subplots(figsize=(12, 6))

# Primary Y-axis (vehicles)
color1 = 'tab:blue'
ax1.set_xlabel('Year')
ax1.set_ylabel('Vehicles Added in Victoria', color=color1)
ax1.plot(years, vehicles_added, marker='o', color=color1, label='Vehicles Added')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x):,}'))

# Secondary Y-axis (% growth)
ax2 = ax1.twinx()
color2 = 'tab:orange'
ax2.set_ylabel('% Growth Rate', color=color2)
ax2.plot(years, growth_rate, marker='s', linestyle='--', color=color2, label='% Growth')
ax2.tick_params(axis='y', labelcolor=color2)

# Annotation
ax1.annotate('COVID-19 impact',
             xy=(2021, vehicles_added[-1]),           # arrow tip at 2021 value
             xytext=(2020.3, vehicles_added[-1] - 4000),  # slightly to the left and above the tip
             arrowprops=dict(facecolor='black', arrowstyle='->'),
             fontsize=10,
             ha='left')

# Title
plt.title('Growth in Registered Vehicles – Victoria (2016–2021)', pad=20)

# Tight layout
fig.tight_layout()
plt.show()

import pandas as pd

# Define the data
years = [2017, 2018, 2019, 2020, 2021]
vehicles_added = [209495, 214408, 236429, 215728, 188855]
growth_rate = [4.2, 4.2, 4.5, 4.0, 3.5]

# Structure the data as a list of dictionaries
data = [
    {"year": y, "vehiclesAdded": v, "growthRatePercent": g}
    for y, v, g in zip(years, vehicles_added, growth_rate)
]

# Export to JSON
df = pd.DataFrame(data)
df.to_json("vic_car_growth.json", orient="records", indent=2)