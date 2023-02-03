import time

import pandas as pd
from celery import Celery
from celery import _state
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


def get_enqueued():
    if celery_app is None:
        return 0

    inspect = celery_app.control.inspect()
    active = inspect.active()

    if not active:
        return 0

    return sum(map(len, active.values()))


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


celery_app = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)
manager = CeleryManager(celery_app)

app = DashProxy(
    __name__,
    background_callback_manager=manager,
    transforms=[ServersideOutputTransform(
        backend=RedisStore(host=REDIS_URL)
    )],
)

# celery_app = make_celery(app.server)
# manager = CeleryManager(celery_app)
# app._background_manager = manager
# server = app.server

app.layout = html.Div([
    html.Button('Click me', id='button'),
    html.Pre(['Hello'], id='queue-output'),
    html.Pre([''], id='output'),
    dcc.Store('store'),
    dcc.Interval(id='interval', interval=500, n_intervals=0),
])


@app.callback(
    Output('queue-output', 'children'),
    Input('button', 'n_clicks'),
    State('interval', 'n_intervals'),
)
def update_queue(n_clicks, n_intervals):
    return f'Clicks: {n_intervals}'


@app.callback(
    Output('output', 'children'),
    Input('store', 'data'),
)
def update_output(data):
    return str(data)


@app.callback(
    Output('store', 'data'),
    Input('button', 'n_clicks'),
    background=True,
    prevent_initial_call=True,
)
def update_data(n_clicks):
    time.sleep(1)
    return pd.DataFrame({
        'n_clicks': range(n_clicks),
    }).to_dict()


app.register_celery_tasks()

if __name__ == '__main__':
    app.run_server(debug=True)
