from dash import Input
from dash import Output
from dash import State
from dash import dcc
from dash import html
from dash import no_update
from dash_extensions.enrich import callback
from trace_updater import TraceUpdater


def make_id(type, id):
    return locals()


def graph_store(graph_id):
    graph = dcc.Graph(id=make_id('graph', graph_id))
    store = dcc.Store(id=make_id('store', graph_id))
    trace = TraceUpdater(gdID=graph_id)

    @callback(
        Output(graph, 'figure'),
        Input(store, 'data'),
        prevent_initial_call=True,
    )
    def update_graph(fig):
        print('update_graph', graph_id, type(fig))
        if fig is None:
            return no_update

        return fig

    @callback(
        Output(trace, 'updateData'),
        Input(graph, 'relayoutData'),
        State(store, 'data'),
        prevent_initial_call=True,
    )
    def update_data(relayout_data, fig):
        print('update_data', graph_id, type(fig))
        if fig is None:
            return no_update

        return fig.construct_update_data(relayout_data)

    return html.Div(children=[graph, store, trace])


class LoggingProxy:
    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, name):
        value = getattr(self.obj, name)

        if not callable(value):
            return value

        def wrapper(*args, **kwargs):
            result = value(*args, **kwargs)
            print(name, args, kwargs, result)
            return result

        return wrapper
