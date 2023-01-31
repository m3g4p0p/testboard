import base64
import datetime
import io
from itertools import starmap

import dash
import diskcache
import pandas as pd
from dash import DiskcacheManager
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform

REDIS_URL = 'redis://127.0.0.1:6379'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

cache = diskcache.Cache('./.cache')
background_callback_manager = DiskcacheManager(cache)

app = DashProxy(
    __name__,
    external_stylesheets=external_stylesheets,
    transforms=[ServersideOutputTransform()],
)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    dcc.Store('data-store'),
    html.Div([
        dcc.Download('download-data'),
        html.Button('Download Data', 'download-button'),
    ], id='download-wrapper', hidden=True),
    html.Div(id='output-data-upload'),
])


def read_data(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    return pd.read_csv(io.StringIO(decoded.decode('utf-8')))


def display_contents(df, filename, date):
    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns]
        ),
    ])


@app.callback(
    Output('download-wrapper', 'hidden'),
    Input('data-store', 'data'),
    prevent_initial_call=True,
)
def toggle_download_button(data):
    return not bool(data)


@app.callback(
    Output('output-data-upload', 'children'),
    ServersideOutput('data-store', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    background=True,
    manager=background_callback_manager,
    prevent_initial_call=True,
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        data = list(map(read_data, list_of_contents))

        children = list(starmap(display_contents, zip(
            data, list_of_names, list_of_dates)))

        return children, data


if __name__ == '__main__':
    app.run_server(debug=True)
