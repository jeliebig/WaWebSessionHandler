from abc import abstractmethod, ABC

from SessionHandler.SessionObject import SessionObject


class Version(ABC):
    @staticmethod
    @abstractmethod
    def is_version(wa_session: SessionObject) -> bool:
        pass

    @abstractmethod
    def __init__(self, wa_session: SessionObject):
        pass
