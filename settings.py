import os
import functools

TOKEN = '871466747:AAG7H4E-IHdy6Jm6b6yZd65HMSp8LJtef2g'
BASE_URL = f'https://api.telegram.org/bot{TOKEN}/'
WEB_HOOK_URL = f'https://bot.erc20crawler.com/{TOKEN}/'

HEADERS = {
    'Content-Type': 'application/json',
}
SITES_FOR_CHECK = {
    'https://chainartsoft.com',
}

HOST = '127.0.0.1'
PORT = 6060

info_log = os.path.join(os.getcwd(), 'info.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(name)s(%(lineno)d) - %(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
        'info_log': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': info_log,
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'info_log']
    }
}


COMMANDS = {}


def command(name=None):
    def _fun(fun):
        COMMANDS[name or fun.__name__] = fun

        @functools.wraps
        def _wrap(*args, **kwargs):
            res = fun(*args, **kwargs)
            return '\n'.join(res)
        return _wrap
    return _fun


@command()
def help():
    return COMMANDS.keys()


@command('addsite')
def add_site(url):
    SITES_FOR_CHECK.add(url)
    return sites()


@command()
def sites():
    return SITES_FOR_CHECK


@command('remsite')
def rem_site(url):
    SITES_FOR_CHECK.remove(url)
    return sites()
