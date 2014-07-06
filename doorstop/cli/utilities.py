"""Shared command-line functions."""


def ask(question, default=None):
    """Display a console yes/no prompt.

    :param question: text of yes/no question ending in '?'
    :param default: 'yes', 'no', or None (for no default)

    :return: True = 'yes', False = 'no'

    """
    valid = {"yes": True,
             "y": True,
             "no": False,
             "n": False}

    if default == 'yes':
        prompt = " [Y/n] "
    elif default == 'no':
        prompt = " [y/N] "
    else:
        prompt = " [y/n] "

    while True:
        try:
            choice = input(question + prompt).lower().strip() or default
        except KeyboardInterrupt as exc:
            print()
            raise exc from None
        try:
            return valid[choice]
        except KeyError:
            options = ', '.join(sorted(valid.keys()))
            print("valid responses: {}".format(options))
