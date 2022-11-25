# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
from dash import ctx
from dash import Input
from dash import Output
from dash import State
from plotly_resampler import FigureResampler
from trace_updater import TraceUpdater
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})


def get_data(stop):
    return pd.DataFrame({
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    }).iloc[:int(stop)]


def create_spam(data):
    print('create spam')
    return px.bar(
        data,
        x="Fruit",
        y="Amount",
        color="City",
        barmode="group",
    )


def create_eggs(data):
    print('create eggs')
    return px.bar(
        data,
        x="Amount",
        y="Fruit",
        color="City",
        barmode="group",
    )


figure_factories = {
    '#spam': create_spam,
    '#eggs': create_eggs,
}

slider = dcc.Slider(1, len(df), value=len(df), step=1)
max_input = dcc.Input(type='number', value=len(df))
fig = FigureResampler(go.Figure())
graph_1 = dcc.Graph(figure=fig)
graph_2 = dcc.Graph()

app.layout = html.Div(children=[
    dcc.Location('location'),
    dcc.Store('session-storage', 'session'),

    dbc.Nav([
        dbc.NavItem(dbc.NavLink('spam', href='#spam')),
        dbc.NavItem(dbc.NavLink('eggs', href='#eggs')),
    ]),

    dbc.Container([
        html.H1(children='Hello Dash'),

        html.Div(children='''
            Dash: A web application framework for your data.
        '''),

        html.Div([slider, max_input]),
        html.Div(graph_1),
        html.Div(graph_2),
    ]),
])


@app.callback(
    Output(slider, 'max'),
    Output(slider, 'value'),
    Input(max_input, 'value'),
    State(slider, 'value')
)
def update_max(max_value, value):
    return max_value, min(max_value, value)


@app.callback(
    Output(graph_1, 'figure'),
    Output(graph_2, 'figure'),
    Input(slider, 'value'),
    Input('location', 'hash'),
)
def update_range(value, hash):
    print('---')
    data = get_data(value)
    dynamic = figure_factories[hash]

    fig.replace(create_spam(data))
    return fig, dynamic(data)


if __name__ == '__main__':
    app.run_server(debug=True)
