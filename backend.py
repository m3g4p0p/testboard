import json

import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import State
from dash import dcc
from dash import html
from dash import no_update
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import RedisStore
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform
from plotly_resampler import FigureResampler
from trace_updater import TraceUpdater

REDIS_URL = 'redis://127.0.0.1:6379'
redis_backend = RedisStore(host='127.0.0.1', port='6379')


def get_data():
    return pd.read_parquet('data2022.parquet.gzip')


app = DashProxy(__name__, transforms=[ServersideOutputTransform()])
server = app.server
df = get_data()

app.layout = html.Div([
    dcc.Dropdown(df.columns, id='column-select'),
    dcc.Graph('graph-id'),
    dcc.Loading(dcc.Store('store-id')),
    TraceUpdater(id="trace-updater", gdID="graph-id"),
    html.Pre(id='debug-info')
])


@app.callback(
    Output('debug-info', 'children'),
    Input('graph-id', 'relayoutData')
)
def update_info(data):
    return json.dumps(data, indent=2)


@app.callback(
    [
        Output('graph-id', 'figure'),
        ServersideOutput(
            'store-id', 'data', backend=redis_backend)
    ],
    Input("column-select", "value"),
    prevent_initial_call=True,
    memoize=True,
)
def plot_graph(column):
    resampled = get_data().resample('600s').mean()
    fig = FigureResampler(go.Figure())

    fig.add_trace(go.Scattergl(
        x=resampled.index,
        y=resampled[column],
        name=column,
        showlegend=True,
        line_width=1,
        mode="lines+markers",
        marker_size=4,
        line_color="#47B5FF",
        marker_color="#256D85",
    ))

    fig.update_layout(
        margin={'l': 40, 'b': 40, 't': 40, 'r': 40},
        hovermode='closest',
    )

    return fig, fig


@app.callback(
    Output("trace-updater", "updateData"),
    Input("graph-id", "relayoutData"),
    # The server side cached FigureResampler per session
    State("store-id", "data"),
    prevent_initial_call=True,
    memoize=True,
)
def update_fig(relayoutdata, fig):
    if fig is None:
        return no_update
    return fig.construct_update_data(relayoutdata)


if __name__ == "__main__":
    app.run_server(debug=True, port=9023)
