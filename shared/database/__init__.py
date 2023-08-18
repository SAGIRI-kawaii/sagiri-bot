from launart import Launart

from shared.database.interface import Database
from avilla.core import Context

def get_interface() :
    launart = Launart.current()
    return launart.get_interface(Database)
