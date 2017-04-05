#!/usr/bin/env python3
#
# Example adapter.wsgi for doorstop.

import os
import sys
import bottle

app = None

def application(environ, start_response):
    global app
    if not app:
        doorstop_path = "/opt/doorstop"
        os.chdir(os.path.dirname(__file__))

        project_path = environ['DOORSTOP_PROJECT_DIR']
        baseurl = environ['DOORSTOP_BASE_URL']

        parameters = [
            '--project', project_path,
            '--baseurl', baseurl
            '--wsgi'
        ]

        sys.path.append(doorstop_path)
        from doorstop.server.main import main as servermain

        servermain(parameters)

        app = bottle.default_app()

    return app(environ, start_response)

