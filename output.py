from dash import Input
from dash import Output
from dash import dcc
from dash import no_update
from dash_extensions.enrich import ServersideOutput
from dash_extensions.enrich import callback


def StoredOutput(component_id, property_id):
    store = dcc.Store('store-' + component_id)

    @callback(
        Output(component_id, property_id),
        Input(store, 'data'),
        prevent_initial_call=True,
        memoize=True,
    )
    def update_component(data):
        if not data:
            return no_update

        return data

    return ServersideOutput(store, 'data')
