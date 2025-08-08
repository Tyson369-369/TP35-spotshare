#CBD Population Insights
import pandas as pd

file_path = "Datasets/Melbourne Population.xlsx"
xls = pd.ExcelFile(file_path, engine='openpyxl')

# Load Table 1 sheet
df = pd.read_excel(xls, sheet_name="Table 4", skiprows=7)

# Drop empty columns (often unnamed or NaN-filled)
df = df.dropna(axis=1, how='all')

# Drop empty rows
df = df.dropna(how='all')

# Clean column names
df.columns = df.columns.astype(str).str.strip()

# Filter for Greater Melbourne
melbourne_data = df[df['GCCSA code'] == '2GMEL']

# Define the actual years corresponding to the 'no.' columns
year_columns = ['no.', 'no..1', 'no..2', 'no..3', 'no..4', 'no..5', 'no..6', 'no..7', 'no..8', 'no..9',
                'no..10', 'no..11', 'no..12', 'no..13', 'no..14', 'no..15', 'no..16', 'no..17', 'no..18',
                'no..19', 'no..20']

actual_years = list(range(2001, 2022))

# Extract the population data and assign the correct years as index
population_values = melbourne_data[year_columns].iloc[0].values
population_series = pd.Series(data=population_values, index=actual_years)

# Print or plot
print("\n--- Greater Melbourne Population (2001–2021) ---")
print(population_series)

# Load Table 2
df2 = pd.read_excel(xls, sheet_name="Table 2", skiprows=7)
df2 = df2.dropna(axis=1, how='all').dropna(how='all')
df2.columns = df2.columns.astype(str).str.strip()

# Filter for Melbourne City
melb_cbd = df2[df2['SA3 name'] == "Melbourne City"]

# Extract Melbourne City CBD population time series
cbd_population_values = melb_cbd[year_columns].iloc[0].values
cbd_population_series = pd.Series(data=cbd_population_values, index=actual_years)

print("\n--- Melbourne City (CBD) Population (2001–2021) ---")
print(cbd_population_series)

years = list(range(2001, 2022))
data = [
    {"year": y, "greaterMelbourne": int(gm), "melbourneCBD": int(cbd)}
    for y, gm, cbd in zip(years, population_series, cbd_population_series)
]

pd.DataFrame(data).to_json("melbourne_trend.json", orient="records", indent=2)



import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator, ScalarFormatter

fig, ax1 = plt.subplots(figsize=(12, 7))

# Primary axis for Greater Melbourne
color1 = 'tab:blue'
ax1.set_xlabel("Year")
ax1.set_ylabel("Greater Melbourne Population", color=color1)
ax1.plot(population_series.index, population_series.values, label='Greater Melbourne', marker='o', color=color1)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, axis='y')

# Remove scientific notation
ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
ax1.ticklabel_format(style='plain', axis='y')
ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

# Secondary axis for Melbourne CBD
ax2 = ax1.twinx()
color2 = 'tab:orange'
ax2.set_ylabel("Melbourne CBD Population", color=color2)
ax2.plot(cbd_population_series.index, cbd_population_series.values, label='Melbourne CBD', marker='s', color=color2)
ax2.tick_params(axis='y', labelcolor=color2)

# Format y-axis with commas
formatter = FuncFormatter(lambda x, _: f'{int(x):,}')
ax1.yaxis.set_major_formatter(formatter)
ax2.yaxis.set_major_formatter(formatter)

# Title and annotation
plt.title("Population Growth: Greater Melbourne vs Melbourne CBD (2001–2021)")
ax2.annotate('COVID impact', xy=(2021, cbd_population_series[2021]),
             xytext=(2015, cbd_population_series[2021] + 20000),
             arrowprops=dict(facecolor='black', arrowstyle='->'),
             fontsize=10)

fig.tight_layout()
plt.show()