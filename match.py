from dash import ALL
from dash import MATCH
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import dcc
from dash import html
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform


def make_id(type, index):
    return locals()


def make_output(oid):
    return html.Div([
        html.Pre(id=make_id('output', oid)),
        dcc.Store(id=make_id('store', oid)),
    ])


app = DashProxy(__name__, transforms=[
    ServersideOutputTransform()
])

app.layout = html.Div([
    make_output('spam'),
    make_output('eggs'),
    html.Button('Click me', id=make_id('button', 'spam')),
])


@app.callback(
    Output(make_id('output', MATCH), 'children'),
    Input(make_id('store', MATCH), 'data'),
)
def display_output(data):
    return data


@app.callback(
    ServersideOutput(make_id('store', 'spam'), 'data'),
    Input(make_id('button', 'spam'), 'n_clicks')
)
def update_data(n_clicks):
    return f'Clicked {n_clicks}'


if __name__ == '__main__':
    app.run_server(debug=True)
