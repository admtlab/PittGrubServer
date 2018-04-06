import os

__version__ = open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '../VERSION')).read().strip()
