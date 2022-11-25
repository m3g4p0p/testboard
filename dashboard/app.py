# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import ctx
from dash import dcc
from dash import html
from dotenv import load_dotenv
from plotly_resampler import EveryNthPoint
from plotly_resampler import FigureResampler
from trace_updater import TraceUpdater

from dashboard.components import DataFilter
from dashboard.util import process_time

load_dotenv()

app = Dash(__name__)

data = pd.read_parquet(os.getenv(
    'PARQUET_FILE', 'data.parquet.gzip'))
result = data.resample('600s').mean()
min_year = result.index.min().year
max_year = result.index.max().year

fig_resampled = FigureResampler(
    go.Figure(), default_n_shown_samples=15000)

fig_resampled.register_update_graph_callback(
    app, 'example-graph', 'trace-updater')


app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    html.Div(children=[
        DataFilter(result, id='data-filter'),
        # DataFilter(result),
        dcc.Dropdown(
            result.columns.unique(),
            'RackMaxCellVoltVal',
            id='yaxis-column',
        ),
        dcc.Graph(
            id='example-graph',
            figure=fig_resampled
        ),
        TraceUpdater(
            id='trace-updater',
            gdID='example-graph',
        ),
        dcc.RangeSlider(
            min_year,
            max_year,
            step=1,
            id='year-slider',
            value=[min_year, max_year],
            marks={
                str(year): str(year)
                for year in result.index.year.unique()
            },
        ),
    ]),
])


@app.callback(
    Output('example-graph', 'figure'),
    Input(DataFilter.ids.column('data-filter'), 'value'),
    Input('year-slider', 'value'),
)
@process_time
def update_resampled(yaxis_column, year_range):
    fig_resampled.replace(go.Figure())

    fig_resampled.add_trace(
        go.Scattergl(),
        hf_x=result.index,
        hf_y=result[yaxis_column],
        downsampler=EveryNthPoint(
            interleave_gaps=False),
    )

    return fig_resampled
