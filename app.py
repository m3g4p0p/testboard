# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
from dash import ctx
from dash import Input
from dash import Output
from dash import State
import dash_bootstrap_components as dbc
import plotly.express as px
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

figures = {
    '#spam': px.bar(df, x="Fruit", y="Amount", color="City", barmode="group"),
    '#eggs': px.bar(df, x="Amount", y="Fruit", color="City", barmode="group"),
}

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

        dcc.Graph(
            id='example-graph',
        )
    ]),
])


@app.callback(
    Output('example-graph', 'figure'),
    Output('session-storage', 'data'),
    Input('location', 'hash'),
    State('session-storage', 'data'),
)
def handle_hash(value, data):
    if data is None:
        data = {}

    data.setdefault(value, 0)
    data[value] += 1

    return figures[value], data


if __name__ == '__main__':
    app.run_server(debug=True)
