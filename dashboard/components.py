import json
import uuid

import pandas as pd
from dash import MATCH
from dash import Input
from dash import Output
from dash import callback
from dash import dcc
from dash import html


class DataFilter(html.Div):

    class ids:

        @staticmethod
        def column(id_): return {
            'component': 'DataFilter',
            'element': 'column',
            'id': id_
        }

        @staticmethod
        def date_range(id_): return {
            'component': 'DataFilter',
            'element': 'date_range',
            'id': id_
        }

        @staticmethod
        def output(id_): return {
            'component': 'DataFilter',
            'element': 'output',
            'id': id_
        }

        @staticmethod
        def store(id_): return {
            'component': 'DataFilter',
            'element': 'store',
            'id': id_
        }

    ids = ids

    def __init__(self, data: pd.DataFrame, **kwargs):
        id_ = kwargs.setdefault('id', str(uuid.uuid4()))

        super().__init__([
            dcc.Dropdown(
                data.columns,
                data.columns[0],
                id=self.ids.column(id_),
            ),
            dcc.RangeSlider(
                0, len(data),
                id=self.ids.date_range(id_),
            ),
            dcc.Store(
                id=self.ids.store(id_),
                storage_type=kwargs.pop(
                    'storage_type', 'session')
            ),
            html.Div(
                id=self.ids.output(id_),
                children=[],
            ),
            dcc.Store
        ], **kwargs)

    @callback(
        Output(ids.output(MATCH), 'children'),
        Output(ids.store(MATCH), 'data'),
        Input(ids.column(MATCH), 'value'),
        Input(ids.date_range(MATCH), 'value'),
    )
    def update_figure(column, date_range):
        return [html.P(f'{column} {date_range}')], \
            json.dumps(locals())
