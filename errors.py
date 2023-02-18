import json
import traceback

import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import dcc
from dash import html
from dash import no_update
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform

app = DashProxy(__name__)
server = app.server

app.layout = html.Div([
    html.Button('click', id='button'),
    html.Div(id='button-clicks'),
    html.Pre(id='error-console'),
    dcc.Store('error-spam'),
    dcc.Store('error-eggs'),
])


@app.callback(
    Output('error-console', 'children'),
    inputs=dict(errors=[
        Input('error-spam', 'data'),
        Input('error-eggs', 'data'),
    ])
)
def update_info(errors):
    print(errors)
    return errors


@app.callback(
    Output('button-clicks', 'children'),
    Output('error-spam', 'data'),
    Input("button", "n_clicks"),
)
def update_clicks(n):
    try:
        if n == 2:
            raise Exception('boo')
        return str(n), None
    except Exception as e:
        tb = e.__traceback__
        print(tb)
        return 'no_update', ''.join(traceback.format_exception(e, None, None))


if __name__ == "__main__":
    app.run_server(debug=True, port=9023)
