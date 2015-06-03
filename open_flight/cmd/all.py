import eventlet

from oslo_log import log
from oslo_config import cfg

from open_flight.api import flaskhandler
from open_flight.util import wsgi


LOG = log.getLogger(__name__)

CONF = cfg.CONF
log.register_options(CONF)

eventlet.patcher.monkey_patch(all=False, socket=True, time=True,
                              select=True, thread=True, os=True)

def main():
    log.setup(CONF, 'open-flight')
    server = wsgi.WSGIServer()
    server.run(flaskhandler.app)
    LOG.info("Running server")
    server.wait()


if __name__ == "__main__":
    main()
