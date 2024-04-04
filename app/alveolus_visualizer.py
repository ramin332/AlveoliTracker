import dash
from dash import dcc  # Import dcc for Dash core components
from dash import html  # Import html for Dash HTML components
from dash.dependencies import Input, Output  # This remains correct but can also be imported directly from dash
import pandas as pd
import numpy as np
import plotly.express as px
import re

# Load the data from CSV file
data = pd.read_csv('Alveolus_evolution_in_time_v3.csv')
# Remove rows with a NaN count
data = data.dropna(subset=['Count'])
# Remove rows where any column's value is 'AA'
#data = data[~data.apply(lambda x: x == 'AA').any(axis=1)]
data = data.dropna(thresh=1)
# Define the size of the map
columns = range(1, 9)
aisles = range(15, 0, -1)  # Reversed the order
channels = range(1, 13)

# Initialize a 2D numpy array to hold the heatmap data
heatmap_data = np.zeros((len(aisles), len(columns) * len(channels)))

# Also create a text label array for the hover information
text_labels = np.empty((len(aisles), len(columns) * len(channels)), dtype=object)

# Use regular expression to extract the column, aisle, channel, height, depth, and side from the "Alveoli" string
pattern = r"C(\d+)A(\d+)Ch(\d+)H(\d+)d(\d+)_([AB])"
total_entries = len(data)
matched_entries = 0

# Check for regular expression matches and process data
for _, row in data.iterrows():
    match = re.search(pattern, row['Alveoli'])
    if match:
        matched_entries += 1
        c, a, ch, _, _, _ = match.groups()  # Ignore Height, Depth, and Side
        c, a, ch = map(int, [c, a, ch])
        count = row['Count']
        idx = (c - 1) * len(channels) + (ch - 1)
        heatmap_data[a - 1, idx] += count  # Sum the counts if there are multiple entries for the same location
        text_labels[a - 1, idx] = f"C{c}A{a}Ch{ch}<br>Count: {count}"  # Modify the text label
    else:
        print(f"No match for Alveoli string: {row['Alveoli']}")

# Print out the results of the regular expression check
print(f"Total entries: {total_entries}")
print(f"Matched entries: {matched_entries}")
if total_entries != matched_entries:
    print("Some entries did not match the regular expression and were not processed.")

# Create the x and y coordinates for the heatmap
x = [f"C{c}Ch{ch}" for c in columns for ch in channels]
y = [f"A{a}" for a in aisles]

# Create the interactive heatmap
fig = px.imshow(
    heatmap_data,
    labels=dict(x="Channel and Column", y="Aisle", color="Count"),
    x=x,
    y=y,
    text_auto=True,
    color_continuous_scale=px.colors.sequential.Plasma
)

# Update the hover information
fig.update_traces(text=text_labels.flatten(), hoverinfo="text")

# Adjust the x-axis to show separation
fig.update_xaxes(
    tickvals=[(i + 0.5) * len(channels) - 0.5 for i in range(len(columns))],
    ticktext=[f"C{c}" for c in columns]
)

# Draw vertical lines to create the visual effect of separation between each column
for i in range(1, len(columns)):
    fig.add_vline(x=i * len(channels) - 0.5, line_width=3, line_dash="dash", line_color="white")

# Show the figure in the web browser
#fig.show()
#fig.write_html("output_figure.html")

# Initialize Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Interactive Heatmap"),
    dcc.Graph(id='heatmap', figure=fig)
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')