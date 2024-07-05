import logging
from os import makedirs, environ
from os.path import dirname


def config_log(file: str):
    d = dirname(file)
    if d:
        makedirs(d, exist_ok=True)

    log_frmt = '%(asctime)s %(name)s - %(levelname)s - %(message)s'
    log_mode = environ.get('LOG_MODE', 'w')
    log_level = int(environ.get('LOG_LEVEL', logging.INFO))
    strm_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(file, mode=log_mode)
    logging.basicConfig(
        level=logging.DEBUG,
        format=environ.get('LOG_FORMAT', log_frmt),
        datefmt='%H:%M:%S',
        handlers=[
            strm_handler,
            file_handler
        ]
    )
    for name in ('seleniumwire.proxy.handler', 'seleniumwire.proxy.client', 'urllib3.connectionpool', 'seleniumwire.proxy.storage', 'selenium.webdriver.remote.remote_connection', 'asyncio'):
        logging.getLogger(name).setLevel(logging.CRITICAL)

    if log_level != logging.DEBUG:
        strm_handler.setLevel(log_level)
        file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        log_frmt,
        datefmt='%H:%M:%S'
    ))
