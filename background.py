import time
from urllib.parse import urlsplit

import pandas as pd
from celery import Celery
from dash import CeleryManager
from dash import ClientsideFunction
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
from dash_extensions.enrich import NoOutputTransform
from dash_extensions.enrich import RedisStore
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import ServersideOutputTransform
from redis import Redis

REDIS_URL = 'redis://127.0.0.1:6379'
redis_url = urlsplit(REDIS_URL)


def value_count(data):
    if not data:
        return 0

    return sum(map(len, data.values()))


def get_queue():
    inspect = celery_app.control.inspect()

    return {
        'active': value_count(inspect.active()),
        'reserved': value_count(inspect.reserved()),
        'scheduled': value_count(inspect.scheduled()),
    }


def get_stats():
    return celery_app.control.inspect().stats()


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=REDIS_URL,
        backend=REDIS_URL,
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


redis = Redis(redis_url.hostname, redis_url.port)
celery_app = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)
manager = CeleryManager(celery_app)

app = DashProxy(
    __name__,
    background_callback_manager=manager,
    transforms=[ServersideOutputTransform(
        backend=RedisStore(host=REDIS_URL)
    ), NoOutputTransform()],
)

# celery_app = make_celery(app.server)
# manager = CeleryManager(celery_app)
# app._background_manager = manager
server = app.server
assert server is not None

app.layout = html.Div([
    html.Button('Click me', id='button'),
    html.Progress(id='progress', value='0', style={
        'display': 'block'}),
    html.Pre(['Hello'], id='queue-output'),
    html.Pre([''], id='output'),
    dcc.Store('store'),
    dcc.Interval(
        'interval',
        interval=1000,
        n_intervals=0,
        max_intervals=100,
    )
])


app.clientside_callback(
    ClientsideFunction(
        namespace='cx',
        function_name='pollQueue',
    ),
    Output('queue-output', 'children'),
    # Input('interval', 'n_intervals'),
    Input('button', 'n_clicks'),
)


@app.callback(
    Input('button', 'n_clicks'),
)
def handle_click(n):
    pass


@app.callback(
    Input('interval', 'n_intervals'),
)
def handle_interval(n):
    pass


@app.callback(
    Output('output', 'children'),
    Input('store', 'data'),
)
def update_output(data):
    return str(data)


@app.callback(
    Output('store', 'data'),
    Input('button', 'n_clicks'),
    # Input('interval', 'n_intervals'),
    background=True,
    prevent_initial_call=True,
    progress=[
        Output('progress', 'value'),
        Output('progress', 'max'),
    ],
)
def update_data(set_progress, n):
    for i in range(n + 1):
        set_progress((str(i), str(n)))
        time.sleep(1)

    return pd.DataFrame({
        'n_clicks': range(n),
    }).to_dict()


@server.route('/celery-queue')
def celery_queue():
    return get_queue()


@server.route('/celery-stats')
def celery_stats():
    return get_stats() or {}


app.register_celery_tasks()

if __name__ == '__main__':
    app.run_server(debug=True)
