from oslo_log import log
from oslo_config import cfg

import open_flight.common.wsgi as wsgi

LOG = log.getLogger(__name__)

CONF = cfg.CONF

from open_flight.api import flaskhandler

def main():
    server = wsgi.WSGIServer()
    server.run(flaskhandler.app)
    server.wait()

if __name__ == "__main__":
    main()