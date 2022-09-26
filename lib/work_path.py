import os

import config


def get_path(
        _, *arguments

):
    path = os.sep.join([config.PATH_MAIN, *arguments])
    return path