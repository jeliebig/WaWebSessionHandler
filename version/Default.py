from . import Version
from ..SessionObject import SessionObject


class Default(Version):
    @staticmethod
    def is_version(wa_session: SessionObject) -> bool:
        pass

    def __init__(self, wa_session: SessionObject):
        pass
