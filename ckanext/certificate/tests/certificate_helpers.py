import webtest
import ckan.plugins
from pylons import config
from ckan import model
from ckan.new_tests import helpers, factories


def get_ckan_app(extend_config={}, plugins=[]):
    # Return a test app with the custom config.
    extend_config.update(config)

    app = ckan.config.middleware.make_app(extend_config['global_conf'], **extend_config)
    app = webtest.TestApp(app)

    for plugin in plugins:
        ckan.plugins.load(plugin)

    return app
