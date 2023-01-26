from dash import Input
from dash import Output
from dash import State
from dash import dcc
from dash import html
from dash import no_update
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import callback
from plotly_resampler import FigureResampler
from trace_updater import TraceUpdater


def graph_with_resampler(graph_id):
    graph = dcc.Graph(id=graph_id)
    store = dcc.Store(id='stored-' + graph_id)
    trace = TraceUpdater(gdID=graph_id)

    @callback(
        ServersideOutput(store, 'data'),
        Input(graph, 'figure'),
        prevent_initial_call=True,
    )
    def update_resampler(fig):
        if fig is None:
            return no_update

        return FigureResampler(
            fig, default_n_shown_samples=15000)

    @callback(
        Output(trace, 'updateData'),
        Input(graph, 'relayoutData'),
        State(store, 'data'),
        prevent_initial_call=True,
    )
    def update_data(relayout_data, fig):
        if fig is None:
            return no_update

        return fig.construct_update_data(relayout_data)

    return html.Div(children=[graph, store, trace])
