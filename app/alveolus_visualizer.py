import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import numpy as np
import plotly.express as px
import re
import base64
import io

file_path = 'app/Workbook.xlsm'
get_workbook = pd.read_excel(file_path, sheet_name='Counter', engine='openpyxl')
# Save the DataFrame to a CSV file
get_workbook.to_csv('app/WorkbookCounterSheet.csv',index=False)
df= pd.read_csv('app/WorkbookCounterSheet.csv')
# Remove rows with a NaN count
df = df.dropna(subset=['Count'])
# Remove rows where any column's value is 'AA'
#data = data[~data.apply(lambda x: x == 'AA').any(axis=1)]
df = df.dropna(thresh=1)
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
total_entries = len(df)
matched_entries = 0

# Check for regular expression matches and process data
for _, row in df.iterrows():
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
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
        multiple=False  # Only allow uploading one file at a time
    ),
    html.Div(id='output-data-upload'),
    dcc.Graph(id='heatmap-graph')  # Define the graph component to display the heatmap
])

# Callback to handle file upload and process data
@app.callback(
    [Output('output-data-upload', 'children'),
     Output('heatmap-graph', 'figure')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def update_output(contents, filename, date):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            # Load the Excel file using pandas
            df_new = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')
        except Exception as e:
            return html.Div([
                'Error loading Excel file:', str(e)
            ]), dash.no_update
        
        # Update the existing workbook with the new data
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_new.to_excel(writer, sheet_name='Counter', index=False)
        
        # Reload the data from the updated Excel file
        data = pd.read_excel(file_path, sheet_name='Counter', engine='openpyxl')
        
        # Data processing steps...

        # Update the heatmap figure
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Channel and Column", y="Aisle", color="Count"),
            x=x,
            y=y,
            text_auto=True,
            color_continuous_scale=px.colors.sequential.Plasma
        )
        fig.update_traces(text=text_labels.flatten(), hoverinfo="text")
        fig.update_xaxes(
            tickvals=[(i + 0.5) * len(channels) - 0.5 for i in range(len(columns))],
            ticktext=[f"C{c}" for c in columns]
        )
        for i in range(1, len(columns)):
            fig.add_vline(x=i * len(channels) - 0.5, line_width=3, line_dash="dash", line_color="white")

        return html.Div([
            html.H4('Data uploaded and processed successfully!'),
            # You can add more HTML components here as needed
        ]), fig
    else:
        return html.Div([
            'Please upload a file.'
        ]), dash.no_update  # Return dash.no_update to keep the existing figure

if __name__ == '__main__':
    app.run_server(debug=True)
