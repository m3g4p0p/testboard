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

import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import dcc
from dash import html
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import ServersideOutputTransform
from plotly_resampler import FigureResampler

from lib import GraphWithTraceUpdater


def get_data():
    return pd.read_parquet('data2022.parquet.gzip')


df = get_data()

# --------------------------------------Globals ---------------------------------------
app = DashProxy(__name__, transforms=[ServersideOutputTransform()])
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
        GraphWithTraceUpdater('graph-id'),
    ]
)


# ------------------------------------ DASH logic -------------------------------------
# The callback used to construct and store the graph's data on the serverside
@app.callback(
    Output('graph-id', 'figure'),
    Input("column-select", "value"),
    prevent_initial_call=True,
)
def plot_graph(column):
    # Note how the replace method is used here on the global figure object
    resampled = df.resample('600s').mean()
    fig: FigureResampler = FigureResampler()
    fig.replace(go.Figure())
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
    )

    fig.update_layout(
        margin={'l': 40, 'b': 40, 't': 40, 'r': 40},
        hovermode='closest',
    )

    return fig


# --------------------------------- Running the app ---------------------------------
if __name__ == "__main__":
    app.run_server(debug=True, port=9023)
