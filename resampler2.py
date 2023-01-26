import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import dcc
from dash import html
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import ServersideOutputTransform
from plotly_resampler import EveryNthPoint
from plotly_resampler import FigureResampler

from lib import graph_with_resampler


def get_data():
    return pd.read_parquet('data2022.parquet.gzip')


app = DashProxy(__name__, transforms=[ServersideOutputTransform()])
server = app.server
df = get_data()

app.layout = html.Div(
    [
        html.H1("plotly-resampler global variable",
                style={"textAlign": "center"}),

        dcc.Dropdown(df.columns, df.columns[0], id='column-select'),
        graph_with_resampler('graph-id'),
    ]
)


@app.callback(
    Output('graph-id', 'figure'),
    Input("column-select", "value"),
    # prevent_initial_call=True,
)
def plot_graph(column):
    resampled = df.resample('600s').mean()
    fig = FigureResampler(
        go.Figure(),
        default_n_shown_samples=15000,
    )

    fig.add_trace(
        go.Scattergl(
            name=column,
            showlegend=True,
            line_width=1,
            mode="lines+markers",
            marker_size=4,
            line_color="#47B5FF",
            marker_color="#256D85",
        ),
        hf_x=resampled.index,
        hf_y=resampled[column],
        max_n_samples=10_000,
        downsampler=EveryNthPoint(interleave_gaps=False)
    )

    fig.update_layout(
        margin={'l': 40, 'b': 40, 't': 40, 'r': 40},
        hovermode='closest',
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True, port=9023)
