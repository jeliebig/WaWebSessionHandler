from abc import abstractmethod, ABC
from typing import Optional

from .Default import Default
from .MultiDevice import MultiDevice
from ..SessionObject import SessionObject


class Version(ABC):
    @staticmethod
    @abstractmethod
    def is_version(wa_session: SessionObject) -> bool:
        pass

    @abstractmethod
    def __init__(self, wa_session: SessionObject):
        pass


versions = [
    Default,
    MultiDevice
]


def get_version(wa_session: SessionObject) -> Optional[Version]:
    """
    Create a :class:`Version` object from a :class:`SessionObject` if possible
    :param wa_session: the session of which a :class:`Version` object should be created from
    :return: the resulting `Version` object or `None` if no matching version was found
    """
    for version in versions:
        if version.is_version(wa_session):
            return version(wa_session)
    return None
