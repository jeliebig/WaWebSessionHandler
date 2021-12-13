from typing import Optional

from SessionHandler.SessionObject import SessionObject
from .Default import Default
from .MultiDevice import MultiDevice
from .Version import Version

versions = [
    Default,
    MultiDevice
]


def get_version(wa_session: SessionObject) -> Optional[Version]:
    """
    Create a :class:`Version` object from a :class:`SessionObject` if possible

    :param wa_session: the session of which a `Version` object should be created from

    :return: the resulting `Version` object or `None` if no matching version was found
    """
    for version in versions:
        if version.is_version(wa_session):
            return version(wa_session)
    return None


def is_any_version(wa_session: SessionObject) -> bool:
    for version in versions:
        if version.is_version(wa_session):
            return True
    return False
