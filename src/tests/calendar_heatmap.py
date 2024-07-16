import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Define persons and days of the week
persons = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank']
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Generate availability data (0 for unavailable, 1 for available)
np.random.seed(0)  # for reproducibility
availability = np.random.choice([0, 1], size=(len(persons), len(days_of_week)))

# Create a DataFrame for better handling
availability_df = pd.DataFrame(availability, index=persons, columns=days_of_week)

# Calculate summary row
summary_row = []
for day in days_of_week:
    count_available = np.sum(availability_df[day] == 1)
    count_unavailable = np.sum(availability_df[day] == 0)
    if count_available > count_unavailable:
        summary_row.append(1)  # green
    elif count_available < count_unavailable:
        summary_row.append(0)  # red
    else:
        summary_row.append(0.5)  # orange

# Append summary row to the availability matrix
summary_df = pd.DataFrame([summary_row], columns=days_of_week)
availability_with_summary = pd.concat([summary_df, availability_df], ignore_index=True)

# Define colorscale with three states: unavailable, 50/50, available
colorscale = [[0, 'red'], [0.5, 'orange'], [1, 'green']]

# Create the heatmap
fig = go.Figure(data=go.Heatmap(
    z=availability_with_summary.values,
    x=days_of_week,
    y=['Summary'] + persons,
    colorscale=colorscale,
    showscale=False
))

# Add a table with borders for the main heatmap
for i in range(len(persons) + 1):  # +1 to include the summary row
    for j in range(len(days_of_week)):
        fig.add_shape(
            type='rect',
            x0=j-0.5, y0=i-0.5,
            x1=j+0.5, y1=i+0.5,
            line=dict(color='black', width=1)
        )

# Update layout for better readability
fig.update_layout(
    title='Availability Calendar with Summary',
    xaxis_title='Day of the Week',
    yaxis_title='Person',
    xaxis={'side': 'top'},
    yaxis_autorange='reversed',
    plot_bgcolor='rgba(0,0,0,0)'  # make plot background transparent
)

# Show the figure
fig.show()
