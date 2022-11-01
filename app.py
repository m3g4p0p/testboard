# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc
from dash import Input, Output
from dotenv import load_dotenv
from plotly_resampler import EveryNthPoint
from plotly_resampler import FigureResampler
from trace_updater import TraceUpdater

load_dotenv()

app = Dash(__name__)

data = pd.read_parquet(os.getenv(
    'PARQUET_FILE', 'data.parquet.gzip'))
result = data.resample('600s').mean()

fig = FigureResampler(
    go.Figure(), default_n_shown_samples=15000)

fig.register_update_graph_callback(
    app, 'example-graph', 'trace-updater')

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    html.Div(children=[
        dcc.Graph(
            id='example-graph',
            figure=fig
        ),
        TraceUpdater(
            id='trace-updater',
            gdID='example-graph',
        ),
        dcc.RangeSlider(
            result.index[0].year,
            result.index[-1].year,
            step=1,
            id='year-slider',
            value=[result.index[0].year, result.index[-1].year],
            marks={str(year): str(year)
                   for year in result.index.year.unique()},
        )
    ]),
])


@app.callback(
    Output('example-graph', 'figure'),
    Input('year-slider', 'value')
)
def update_graph(value):
    fig.replace(go.Figure())

    fig.add_trace(
        go.Scattergl(),
        hf_x=result.index,
        hf_y=result['RackMinCellVoltVal'],
        downsampler=EveryNthPoint(
            interleave_gaps=False),
    )

    return fig


if __name__ == '__main__':
    print(result.columns)
    app.run_server(debug=True)
