from oslo_config import cfg
from oslo_log import log

CONF = cfg.CONF

common_opts = [
    cfg.StrOpt('bind_host',
               default='0.0.0.0',
               help='IP address to listen on.'),
    cfg.IntOpt('bind_port',
               default=9797,
               help='Port number to listen on.')
]
CONF.register_opts(common_opts)

log.register_options(CONF)
