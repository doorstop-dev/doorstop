## Bottle

Doorstop can be run as a standalone web server by running
`doorstop-server`.

It will use the current working directory as the
document source by default.

## WSGI

Doorstop can also be used as a WSGI application by Apache or other web
servers.  To configure this, copy `bin/example-adapter.wsgi` from this
repository to an appropriate place in your web data directory, such as
`/var/www/doorstop/adapter.wsgi`. Edit that file to give it the
correct path to your doorstop installation. Now alter your apache
configuration and add something similar to this:

    WSGIDaemonProcess doorstop user=www-data group=www-data processes=1 threads=5

    WSGIScriptAlias /doorstop /var/www/doorstop/adapter.wsgi
    <Directory /var/www/doorstop>
      SetEnv DOORSTOP_PROJECT_DIR /path/to/your/document
      SetEnv DOORSTOP_BASE_URL /doorstop
      WSGIProcessGroup doorstop
      WSGIApplicationGroup %{GLOBAL}
      Require all granted
    </Directory>

Change `path/to/your/document` to the path to the Doorstop data you
wish to display.
