import time

from celery import Celery
from dash import CeleryManager
from dash import Dash
from dash import DiskcacheManager
from dash import dash_table
from dash import dcc
from dash import html
from dash import no_update
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from dash_extensions.enrich import DashProxy
from dash_extensions.enrich import RedisStore
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform

REDIS_URL = 'redis://127.0.0.1:6379'

celery_app = Celery('tasks', broker=REDIS_URL, backend=REDIS_URL)
manager = CeleryManager(celery_app)

app = DashProxy(
    __name__,
    background_callback_manager=manager,
    transforms=[ServersideOutputTransform(
        backend=RedisStore(host=REDIS_URL)
    )],
)

server = app.server

app.layout = html.Div([
    html.Button('Click me', id='button'),
    html.Pre([''], id='output'),
    dcc.Store('store')
])


@app.callback(
    Output('output', 'children'),
    Input('store', 'data'),
)
def update_output(data):
    return str(data)


@app.callback(
    ServersideOutput('store', 'data'),
    Input('button', 'n_clicks'),
    background=True,
    prevent_initial_call=True,
)
def update_data(n_clicks):
    time.sleep(1)
    return n_clicks


app.register_celery_tasks()
if __name__ == '__main__':
    app.run_server(debug=True)
