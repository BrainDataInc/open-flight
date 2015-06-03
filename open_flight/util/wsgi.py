import os
import signal
import sys

import eventlet
from eventlet import wsgi
from eventlet import greenio
from oslo_log import log
from oslo_log import loggers
from oslo_config import cfg

LOG = log.getLogger(__name__)

CONF = cfg.CONF

server_opts = [
    cfg.StrOpt('bind_host', default='0.0.0.0',
               help='IP address to listen on.'),
    cfg.IntOpt('bind_port', default=9797,
               help='Port number to listen on.'),
    cfg.IntOpt('workers', default=4,
               help='The number of child processes that serve requests.'),
    cfg.IntOpt('backlog', default=500,
               help='The maximum number of queued connections.')
]
CONF.register_opts(server_opts)

log.register_options(CONF)


class WSGIServer(object):
    def __init__(self, threads=500):
        self.threads = threads
        self.children = set()
        self.running = True

    def run(self, app):
        self.app = app
        self.setup()
        self.run_wsgi()

    def setup(self):
        log.setup(CONF, 'open-flight')
        self.setup_socket()

    def run_wsgi(self):
        if CONF.workers == 0:
            # TODO: (yvoderatskiy) there we should use handler for single run
            pass
        else:
            LOG.info("Starting %d workers", CONF.workers)
            signal.signal(signal.SIGTERM, self.kill_children)
            signal.signal(signal.SIGINT, self.kill_children)
            signal.signal(signal.SIGHUP, self.hup)
            while len(self.children) < CONF.workers:
                self.run_child_process()

    def kill_children(self, *args):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.running = False
        os.killpg(os.getpid(), signal.SIGTERM)

    def hup(self, *args):
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

    def get_pool(self):
        return eventlet.GreenPool(size=self.threads)

    def setup_socket(self):
        # TODO: (yvoderatskiy) there we should check if ssl required
        self.sock = eventlet.listen((CONF.bind_host, CONF.bind_port), backlog=500)

    def run_child_process(self):
        def child_hup(*args):
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            eventlet.wsgi.is_accepting = False
            self.sock.close()

        pid = os.fork()
        if pid == 0:
            signal.signal(signal.SIGHUP, child_hup)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.run_server()
            sys.exit(0)
        else:
            LOG.info("Started children %s", pid)
            self.children.add(pid)

    def run_server(self):
        self.pool = self.get_pool()
        eventlet.wsgi.server(self.sock,
                             self.app,
                             log=loggers.WritableLogger(LOG),
                             custom_pool=self.pool,
                             debug=False)
        self.pool.waitall()

    def wait(self):
        try:
            if self.children:
                self.wait_on_children()
            else:
                self.pool.wait()
        except KeyboardInterrupt:
            print 'Interrupt'

    def wait_on_children(self):
        while self.running:
            try:
                pid, status = os.wait()
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    if pid in self.children:
                        self.children.remove(pid)
                    else:
                        LOG.warn("Unknown children %s", pid)
            except OSError as e:
                pass
            except KeyboardInterrupt as e:
                LOG.info("Keyboard interrupt. Exiting")
        eventlet.greenio.shutdown_safe(self.sock)
        self.sock.close()
