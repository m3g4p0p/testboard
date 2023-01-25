from dash import Input
from dash import Output
from dash import State
from dash import dcc
from dash import no_update
from dash_extensions.enrich import RedisStore
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import callback
from plotly_resampler import FigureResampler
from trace_updater import TraceUpdater


def GraphWithTraceUpdater(graph_id):
    graph = dcc.Graph(id=graph_id)
    store = dcc.Store(id='stored-' + graph_id)
    trace = TraceUpdater(gdID=graph_id)

    @callback(
        ServersideOutput(store, 'data', backend=RedisStore(
            host='127.0.0.1', port='6379')),
        Input(graph, 'figure'),
        prevent_initial_call=True,
    )
    def update_figure(fig):
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

    return dcc.Loading(children=[graph, store, trace])
