from oslo_log import log
from oslo_config import cfg
import eventlet
from eventlet import wsgi

LOG = log.getLogger(__name__)

CONF = cfg.CONF

CONF.import_opt('bind_host', 'open_flight.conf')
CONF.import_opt('bind_port', 'open_flight.conf')


class WSGIServer(object):
    def __init__(self):
        self.host = CONF.bind_host
        self.port = CONF.bind_port
        self.sock = eventlet.listen((self.host, self.port))
        self.pool = eventlet.GreenPool()

    def run(self, app):
        LOG.info("Starting server")
        wsgi.server(self.sock,
                    app,
                    custom_pool=self.pool)

    def wait(self):
        try:
            self.pool.waitall()
        except KeyboardInterrupt:
            pass
