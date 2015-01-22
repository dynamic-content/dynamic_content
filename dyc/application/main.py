"""
Main file that runs the application.
"""
python_logo_ascii_art = """
          .?77777777777777$.
          777..777777777777$+
         .77    7777777777$$$
         .777 .7777777777$$$$
         .7777777777777$$$$$$
         ..........:77$$$$$$$
  .77777777777777777$$$$$$$$$.=======.
 777777777777777777$$$$$$$$$$.========
7777777777777777$$$$$$$$$$$$$.=========
77777777777777$$$$$$$$$$$$$$$.=========
777777777777$$$$$$$$$$$$$$$$ :========+.
77777777777$$$$$$$$$$$$$$+..=========++~
777777777$$..~=====================+++++
77777777$~.~~~~=~=================+++++.
777777$$$.~~~===================+++++++.
77777$$$$.~~==================++++++++:
 7$$$$$$$.==================++++++++++.
 .,$$$$$$.================++++++++++~.
         .=========~.........
         .=============++++++
         .===========+++..+++
         .==========+++.  .++
          ,=======++++++,,++,
          ..=====+++++++++=.
                ..~+=...
"""
## Python logo Ascii art by @xero -> https://gist.github.com/xero/3555086

__author__ = 'Justus Adam'
__version__ = '0.2.4'


def bool_from_str(string, default=False):
    if not isinstance(string, str):
        return default
    if string.lower() == 'false':
        return False
    elif string.lower() == 'true':
        return True
    else:
        return default


def prepare():

    # print(python_logo_ascii_art)

    import os
    import pathlib
    import sys

    print('\n\n\n')

    _basedir = pathlib.Path(__file__).parent.parent.resolve()

    # if framework is not in the path yet, add it and import it
    if not str(_basedir.parent) in sys.path:
        sys.path.append(str(_basedir.parent))

    os.chdir(str(_basedir))
    # print(_basedir.parent)

    del _basedir

    try:
        import setproctitle
        import subprocess

        title = 'dynamic_content'

        res = subprocess.check_output(('ps', '-ef'))

        lines = tuple(filter(lambda a: ' ' + title + ' ' in a, res.decode().splitlines()))

        if len(lines) != 0:
            print(lines)
            a = input('\n\nAnother {} process has been detected.\nWould you like to kill it, in order to start a new one?\n[y|N]\n\n\n'.format(title))
            if a.lower() in ('y', 'yes'):
                subprocess.call(('pkill', 'dynamic_content'))
            else:
                sys.exit()

        if not setproctitle.getproctitle() == title:
            setproctitle.setproctitle(title)
    except ImportError:
        pass


def main():
    import argparse
    from dyc.includes import settings
    from dyc.util import structures

    sbool = ('true', 'false')

    parser = argparse.ArgumentParser()
    parser.add_argument('--runlevel', '-r', type=str, choices=tuple(map(str.lower, settings.RunLevel._fields)))
    parser.add_argument('--logfile', type=str)
    parser.add_argument('--loglevel', type=str, choices=tuple(map(str.lower, settings.LoggingLevel._fields)))
    parser.add_argument('--pathmap', type=str, choices=tuple(map(str.lower, settings.PathMaps._fields)))
    parser.add_argument('--port', type=int)
    parser.add_argument('--ssl_port', type=int)
    parser.add_argument('--https_enabled', type=str, choices=sbool)
    parser.add_argument('--http_enabled', type=str, choices=sbool)
    parser.add_argument('--host')
    parser.add_argument('--server', type=str, choices=tuple(map(str.lower, settings.ServerTypes._fields)))
    parser.add_argument('--ssl_certfile', type=str)
    parser.add_argument('--ssl_keyfile', type=str)

    startargs = parser.parse_args()

    settings.HTTPS_ENABLED = bool_from_str(startargs.https_enabled, settings.HTTPS_ENABLED)
    settings.HTTP_ENABLED = bool_from_str(startargs.http_enabled, settings.HTTP_ENABLED)

    if startargs.runlevel:
        settings.RUNLEVEL = getattr(settings.RunLevel, startargs.runlevel.upper())
    if startargs.logfile:
        settings.LOGFILE = startargs.logfile
    if startargs.loglevel:
        settings.LOGGING_LEVEL = getattr(settings.LoggingLevel, startargs.loglevel.upper())
    if startargs.port or startargs.host or startargs.ssl_port:
        settings.SERVER = type(settings.SERVER)(
            host=startargs.host if startargs.host else settings.SERVER.host,
            port=startargs.port if startargs.port else settings.SERVER.port,
            ssl_port=startargs.ssl_port if startargs.ssl_port else settings.SERVER.ssl_port,
            )
    if startargs.server:
        settings.SERVER_TYPE = getattr(settings.ServerTypes, startargs.server.upper())
    if startargs.ssl_certfile:
        settings.SSL_CERTFILE = startargs.ssl_certfile
    if startargs.ssl_keyfile:
        settings.SSL_KEYFILE = startargs.ssl_keyfile

    from dyc import application

    application.Application(
        application.Config(
            server_arguments=settings.SERVER
            )
        ).start()


if __name__ == '__main__':
    prepare()
    main()
