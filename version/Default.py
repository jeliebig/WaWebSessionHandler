from . import Version
from ..SessionObject import SessionObject


class Default(Version):
    @staticmethod
    def is_version(wa_session: SessionObject) -> bool:
        return "WAToken1" in wa_session.local_storage.keys() and "WAToken2" in wa_session.local_storage.keys()

    def __init__(self, wa_session: SessionObject):
        pass
