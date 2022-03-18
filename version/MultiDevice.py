from SessionHandler.SessionObject import SessionObject
from .Version import Version


class MultiDevice(Version):
    @staticmethod
    def is_version(wa_session: SessionObject) -> bool:
        return "WANoiseInfo" in wa_session.local_storage.keys()

    def __init__(self, wa_session: SessionObject):
        pass
