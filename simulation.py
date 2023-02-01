import base64
import datetime
import io
import os
import time
from itertools import starmap

import celery
import diskcache
import dotenv
import pandas as pd
from dash import CeleryManager
from dash import DiskcacheManager
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import MultiplexerTransform
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform

dotenv.load_dotenv()
REDIS_URL = 'redis://127.0.0.1:6379'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


def get_manager():
    redis_url = os.getenv('REDIS_URL')

    if not redis_url:
        cache = diskcache.Cache('./.cache')
        return DiskcacheManager(cache)

    celery_app = celery.Celery(
        __name__, broker=redis_url, backend=redis_url)

    return CeleryManager(celery_app)


app = DashProxy(
    __name__,
    background_callback_manager=get_manager(),
    external_stylesheets=external_stylesheets,
    transforms=[ServersideOutputTransform(), MultiplexerTransform()],
)

server = app.server

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
        accept='text/csv',
        multiple=True,
    ),
    dcc.Loading([
        dcc.Store('store-data-upload'),
        dcc.Download('download-data'),
    ]),
    html.Div([
        html.Button('Process Data', 'process-button'),
        html.Div(html.Progress(id='progress-bar', value='0')),
    ], id='button-wrapper', hidden=True),
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
    Output('download-data', 'data'),
    Output('upload-data', 'contents'),
    Input('process-button', 'n_clicks'),
    State('store-data-upload', 'data'),
    background=True,
    prevent_initial_call=True,
    running=[
        (Output('process-button', 'disabled'), True, False)
    ],
    progress=[
        Output('progress-bar', 'value'),
        Output('progress-bar', 'max'),
    ],
)
def process_data(set_progress, n_clicks, data):
    total = len(data) * 10

    for i in range(total + 1):
        set_progress((str(i), str(total)))
        time.sleep(0)

    return dcc.send_data_frame(
        pd.concat(data).to_csv,
        'results.csv',
    ), None


@app.callback(
    Output('button-wrapper', 'hidden'),
    Input('store-data-upload', 'data'),
    prevent_initial_call=True,
)
def toggle_process_button(data):
    return not bool(data)


@app.callback(
    Output('output-data-upload', 'children'),
    ServersideOutput('store-data-upload', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    prevent_initial_call=True,
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is None:
        return [], None

    data = list(map(read_data, list_of_contents))

    children = list(starmap(display_contents, zip(
        data, list_of_names, list_of_dates)))

    return children, data


if __name__ == '__main__':
    app.run_server(debug=True)
