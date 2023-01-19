from collections import namedtuple

from dash import Input
from dash import Output
from dash import State
from dash import dcc
from dash import no_update
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import callback
from plotly_resampler import FigureResampler
from trace_updater import TraceUpdater

StoredGraph = namedtuple(
    'StoredGraph',
    ['Components', 'Output'],
)


def stored_graph(graph_id):
    graph = dcc.Graph(id=graph_id)
    store = dcc.Store(id='store-' + graph_id)

    trace = TraceUpdater(
        id='trace-updater-' + graph_id, gdID=graph_id)

    @callback(
        ServersideOutput(store, 'data'),
        Input(graph, 'figure'),
    )
    def update_figure(fig):
        if fig is None:
            return no_update

        return fig

    @callback(
        Output(trace, 'updateData'),
        Input(graph, 'relayoutData'),
        State(store, 'data'),
        prevent_initial_call=True,
    )
    def update_data(relayout_data, fig_data):
        if fig_data is None:
            return no_update

        return FigureResampler(
            fig_data).construct_update_data(relayout_data)

    components = graph, store, trace
    output = ServersideOutput(store, 'data')

    return StoredGraph(components, output)
