import base64
import datetime
import io
import os
import sys
import time

import celery
import diskcache
import dotenv
import pandas as pd
from dash import CeleryManager
from dash import DiskcacheManager
from dash import dash_table
from dash import dcc
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform

dotenv.load_dotenv()
redis_url = os.getenv('REDIS_URL')

if not redis_url:
    cache = diskcache.Cache('./.cache')
    background_callback_manager = DiskcacheManager(cache)
else:
    celery_app = celery.Celery(
        __name__, broker=redis_url, backend=redis_url)
    background_callback_manager = CeleryManager(celery_app)

app = DashProxy(
    __name__,
    background_callback_manager=background_callback_manager,
    external_stylesheets=[
        'https://codepen.io/chriddyp/pen/bWLwgP.css'],
    suppress_callback_exceptions=True,
    transforms=[ServersideOutputTransform()],
)

server = app.server

app.layout = html.Div([
    html.Button('Show outlet', id='show-outlet'),
    html.Div(id='outlet')
])


@app.callback(
    Output('outlet', 'children'),
    Input('show-outlet', 'n_clicks'),
    prevent_initial_call=True,
)
def create_layout(n_clicks):
    print(n_clicks)
    if 'celery' in sys.argv[0]:
        return None

    inspect = celery_app.control.inspect()
    print(inspect.stats())

    for prop in ('active', 'scheduled', 'reserved'):
        tasks = getattr(inspect, prop)()
        if tasks and any(tasks.values()):
            return html.Div('Please try again later')

    return html.Div([
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
        ),
        dcc.Loading([
            dcc.Store('store-data-result'),
            dcc.Download('download-data'),
        ]),
        html.Div(id='output-data-upload'),
        html.Div(id='output-data-result'),
    ])


def read_file_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    return pd.read_csv(io.StringIO(decoded.decode('utf-8')))


@app.callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    prevent_initial_call=True,
)
def update_output_upload(contents, filename, date):
    if contents is None:
        return None

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),
        html.Button('Process Data', 'process-button'),
        html.Button('Cancel', 'cancel-button'),
        html.Progress(id='progress-bar', value='0'),
    ])


@app.callback(
    Output('store-data-result', 'data'),
    Output('upload-data', 'contents'),
    Input('process-button', 'n_clicks'),
    State('upload-data', 'contents'),
    background=True,
    prevent_initial_call=True,
    running=[
        (Output('process-button', 'disabled'), True, False)
    ],
    progress=[
        Output('progress-bar', 'value'),
        Output('progress-bar', 'max'),
    ],

    cancel=[
        Input('cancel-button', 'n_clicks')
    ]
)
def process_data(set_progress, n_clicks, contents):
    if n_clicks is None:
        return None, no_update

    data = read_file_contents(contents)
    total = len(data)

    for i in range(total + 1):
        set_progress((str(i), str(total)))
        time.sleep(1)

    return data, None


@app.callback(
    Output('output-data-result', 'children'),
    Input('upload-data', 'contents'),
    Input('store-data-result', 'data'),
    prevent_initial_call=True,
)
def update_output_result(contents, data):
    if contents or data is None:
        return None

    return html.Div([
        html.Button('Download Data', 'download-button'),
        dash_table.DataTable(
            data.to_dict('records'),
            [{'name': i, 'id': i} for i in data.columns]
        )
    ])


@app.callback(
    Output('download-data', 'data'),
    Input('download-button', 'n_clicks'),
    State('store-data-result', 'data'),
    prevent_initial_call=True,
)
def download_data(n_clicks, data):
    if n_clicks is None:
        return no_update

    return dcc.send_data_frame(data.to_csv, 'result.csv')


app.register_celery_tasks()

if __name__ == '__main__':
    app.run_server(debug=True)
