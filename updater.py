from dash import MATCH
from dash import Input
from dash import Output
from dash import State
from dash import dcc
from dash import html
from dash import no_update
from dash_extensions.enrich import callback
from trace_updater import TraceUpdater


def id_factory(subcomponent):
    return lambda gu_id: {
        'component': 'GraphUpdater',
        'subcomponent': subcomponent,
        'gu_id': gu_id
    }


class GraphUpdater(html.Div):

    class ids:
        graph = id_factory('graph')
        store = id_factory('store')
        trace = id_factory('trace')

    ids = ids

    def __init__(self, gu_id, *args, **kwargs):
        super().__init__([
            dcc.Graph(id=self.ids.graph(gu_id)),
            dcc.Store(id=self.ids.store(gu_id)),
            TraceUpdater(self.ids.trace(gu_id), gu_id),
        ], *args, **kwargs)

    @callback(
        Output(ids.graph(MATCH), 'figure'),
        Input(ids.store(MATCH), 'data'),
        prevent_initial_call=True,
    )
    def update_figure(fig):
        if fig is None:
            return no_update

        return fig

    @callback(
        Output(ids.trace(MATCH), 'updateData'),
        Input(ids.graph(MATCH), 'relayoutData'),
        State(ids.store(MATCH), 'data'),
        prevent_initial_call=True,
    )
    def update_data(relayout_data, fig):
        if fig is None:
            return no_update

        return fig.construct_update_data(relayout_data)
