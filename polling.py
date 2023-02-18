import time
from urllib.parse import urlparse

import pandas as pd
import requests
from celery import Celery
from celery import Task
from celery import shared_task
from celery.result import AsyncResult
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
from flask import Flask
from flask import request
from flask import url_for

REDIS_URL = 'redis://127.0.0.1:6379'


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(
        app.name,
        task_cls=FlaskTask,
        backend=REDIS_URL,
        broker=REDIS_URL,
    )

    celery_app.set_default()
    return celery_app


app = DashProxy(
    __name__,
    transforms=[ServersideOutputTransform(
        backend=RedisStore(host=REDIS_URL)
    ), NoOutputTransform()],
)


server = app.server
assert server is not None
celery = celery_init_app(server)

app.layout = html.Div([
    html.Button('Start', 'start'),
    html.Progress(id='progress', value='0'),
    html.Pre(id='status'),
    html.Pre(id='result'),
    dcc.Interval('poll', max_intervals=0),
    dcc.Store('task-id'),
    dcc.Store('task-result'),
])


def get_endpoint_url(endpoint, **values):
    scheme, netloc, *_ = urlparse(request.base_url)
    return f'{scheme}://{netloc}' + url_for(endpoint, **values)


@app.callback(
    Output('task-id', 'data'),
    Input('start', 'n_clicks'),
    prevent_initial_call=True,
)
def trigger_process(n):
    endpoint_url = get_endpoint_url('post_process')
    response = requests.post(endpoint_url)
    response.raise_for_status()

    return response.json()


@app.callback(
    Output('poll', 'max_intervals'),
    Input('task-id', 'data'),
    Input('task-result', 'data'),
)
def start_polling(task_id, task_result):
    if not task_id or task_result:
        return 0

    return -1


@app.callback(
    Output('task-result', 'data'),
    Output('status', 'children'),
    Output('progress', 'value'),
    Input('poll', 'n_intervals'),
    State('task-id', 'data'),
    prevent_initial_call=True,
)
def poll_process(n, data):
    endpoint_url = get_endpoint_url('get_process', **data)
    response = requests.get(endpoint_url)
    json_data = response.json()
    result = json_data.get('result', no_update)

    if result is not no_update:
        progress = '1'
    else:
        progress = json_data.get('progress')
        progress = progress and str(progress)

    return result, response.text, progress


@app.callback(
    Output('result', 'children'),
    Input('task-result', 'data')
)
def update_result(data):
    return data


@shared_task(name='process', bind=True)
def process(self: Task, n=10):
    for i in range(n):
        time.sleep(1)

        self.update_state(
            state='PROGRESS', meta=(i + 1) / n)

    return 'Hello world!'


@server.post('/process')
def post_process():
    task = process.delay()
    return dict(task_id=task.id)


@server.get('/process/<task_id>')
def get_process(task_id):
    result = AsyncResult(task_id)
    data = dict(status=result.status)

    if isinstance(result.info, float):
        data['progress'] = result.info

    if result.successful():
        data['result'] = result.result
    elif result.failed():
        data['reason'] = repr(result.result)

    return data


if __name__ == '__main__':
    app.run_server(debug=True)
