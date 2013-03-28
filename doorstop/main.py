"""
Common interface to Veracity's command-line interface.
"""

import os

# Check for installed packages
if os.name == 'nt':
    import pbs  # pylint: disable=F0401,W0611
else:
    import sh  # pylint: disable=F0401,W0611

# Check for Veracity
try:
    if os.name == 'nt':
        VV_PATH_WINDOWS = r"C:\Program Files\SourceGear\Veracity\vv.exe"
        if not os.path.isfile(VV_PATH_WINDOWS):
            raise ImportError
        vv = pbs.Command(VV_PATH_WINDOWS)  # pylint: disable=C0103
    else:
        from sh import vv  # pylint: disable=F0401,E0611
except ImportError:
    raise EnvironmentError("Veracity is not installed")
else:
    if not vv.version().startswith('2.'):
        raise EnvironmentError("only Veracity 2.x is supported")


def run(name, *args, **kwargs):
    """Run a Veracity command with the given arguments.
    @raise VeracityException: when Veracity returns an error
    """
    attr = getattr(vv, name)
    if os.name == 'nt':
        try:
            output = attr(*args, **kwargs)
        except pbs.ErrorReturnCode:
            msg = "vv {} {} {}".format(name,
                                       ' '.join(str(arg) for arg in args),
                                       ' '.join("{}={}".format(key, repr(value))
                                                for key, value in kwargs.items()))
            raise VeracityException(msg)
    else:
        output = attr(*args, **kwargs)
        if output.exit_code:
            raise VeracityException(output)

    return str(output)


class VeracityException(Exception):
    """Exception for Veracity errors."""
    pass
