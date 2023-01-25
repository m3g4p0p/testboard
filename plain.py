"""Minimal dash app example.

Click on a button, and see a plotly-resampler graph of two noisy sinusoids.
No dynamic graph construction / pattern matching callbacks are needed.

This example uses a global FigureResampler object, which is considered a bad practice.
source: https://dash.plotly.com/sharing-data-between-callbacks:

    Dash is designed to work in multi-user environments where multiple people view the
    application at the same time and have independent sessions.
    If your app uses and modifies a global variable, then one user's session could set
    the variable to some value which would affect the next user's session.

"""
import json

import pandas as pd
import plotly.express as px
from celery import Celery
from dash import CeleryManager
from dash import Dash
from dash import Input
from dash import Output
from dash import dcc
from dash import html
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import ServersideOutputTransform

REDIS_URL = 'redis://127.0.0.1:6379'


def get_data():
    return pd.read_parquet('data2022.parquet.gzip')


df = get_data()

celery_app = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)
background_callback_manager = CeleryManager(celery_app)

# app = DashProxy(__name__, transforms=[ServersideOutputTransform()])
app = Dash(__name__)
server = app.server

# NOTE: in this example, this reference to a FigureResampler is essential to preserve
# throughout the whole dash app! If your dash app wants to create a new go.Figure(),
# you should not construct a new FigureResampler object, but replace the figure of this
# FigureResampler object by using the FigureResampler.replace() method.

app.layout = html.Div(
    [
        html.H1("plotly-resampler global variable",
                style={"textAlign": "center"}),

        dcc.Dropdown(df.columns, id='column-select'),
        dcc.Graph('graph-id'),
        html.Pre(id='debug-info')
    ]
)


@app.callback(
    Output('debug-info', 'children'),
    Input('graph-id', 'relayoutData')
)
def update_info(data):
    return json.dumps(data, indent=2)


@app.callback(
    Output('graph-id', 'figure'),
    Input("column-select", "value"),
    prevent_initial_call=True,
    background=True,
    manager=background_callback_manager,
)
def plot_graph(column):
    # Note how the replace method is used here on the global figure object
    resampled = get_data().resample('600s').mean().head()

    return px.scatter(resampled, x=resampled.index, y=resampled[column])


# --------------------------------- Running the app ---------------------------------
if __name__ == "__main__":
    app.run_server(debug=True, port=9023)
