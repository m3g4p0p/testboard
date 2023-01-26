import json

import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import dcc
from dash import html
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import RedisStore
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform

from output import StoredOutput


def get_data():
    return pd.read_parquet('data2022.parquet.gzip')


app = DashProxy(__name__, transforms=[ServersideOutputTransform(
    backend=RedisStore(host='127.0.0.1', port='6379')
)])

server = app.server
df = get_data()

app.layout = html.Div([
    dcc.Dropdown(df.columns, id='column-select'),
    dcc.Graph('graph-id'),
    dcc.Loading(dcc.Store('store-id')),
    html.Pre(id='debug-info')
])


@app.callback(
    Output('debug-info', 'children'),
    Input('graph-id', 'relayoutData')
)
def update_info(data):
    return json.dumps(data, indent=2)


@app.callback(
    StoredOutput('graph-id', 'figure', app),
    Input("column-select", "value"),
    prevent_initial_call=True,
    memoize=True,
)
def plot_graph(column):
    resampled = get_data().resample('600s').mean()
    fig = go.Figure()

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

    return fig


if __name__ == "__main__":
    app.run_server(debug=True, port=9023)
