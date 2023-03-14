"""Utility functions for pyadtpulse."""
from typing import Optional

from aiohttp import ClientResponse
from bs4 import BeautifulSoup
import logging
import sys
from threading import RLock

LOG = logging.getLogger(__name__)


def handle_response(
    response: Optional[ClientResponse], level: int, error_message: str
) -> bool:
    """Handle the response from query().

    Args:
        response (Optional[Response]): the response from the query()
        level (int): Level to log on error (i.e. INFO, DEBUG)
        error_message (str): the error message

    Returns:
        bool: True if no error occurred.
    """
    if response is None:
        LOG.log(level, f"{error_message}")
        return False

    if response.ok:
        return True

    LOG.log(level, f"{error_message}: error code={response.status}")

    return False


def remove_prefix(text: str, prefix: str) -> str:
    """Remove prefix from a string.

    Args:
        text (str): original text
        prefix (str): prefix to remove

    Returns:
        str: modified string
    """
    return text[text.startswith(prefix) and len(prefix) :]


async def make_soup(
    response: Optional[ClientResponse], level: int, error_message: str
) -> Optional[BeautifulSoup]:
    """Make a BS object from a Response.

    Args:
        response (Optional[Response]): the response
        level (int): the logging level on error
        error_message (str): the error message

    Returns:
        Optional[BeautifulSoup]: a BS object, or None on failure
    """
    if not handle_response(response, level, error_message):
        return None

    if response is None:  # shut up type checker
        return None
    body_text = await response.text()
    response.close()
    return BeautifulSoup(body_text, "html.parser")


class debugRLock:
    """Provides a debug lock logging caller who acquired/released."""

    def __init__(self, name: str):
        """Initlize the lock."""
        self._Rlock = RLock()
        self._lock_name = name

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        """Acquire the lock.

        Args:
            blocking (bool, optional): blocks if can't obtain the lock if True.
                                       Defaults to True.
            timeout (float, optional): timeout to wait to acquire the lock.
                                       Defaults to -1.

        Returns:
            bool: True if lock obtained, False if blocking is False and lock couldn't be
                  obtained
        """
        caller = sys._getframe().f_back
        if caller is not None:
            caller2 = caller.f_code.co_name
        else:
            caller2 = "*Unknown*"
        LOG.debug(
            f"pyadtpulse acquiring lock {self._lock_name} "
            f"blocking: {blocking} from {caller2}"
        )
        retval = self._Rlock.acquire(blocking, timeout)
        LOG.debug(
            f"pyadtpulse acquisition of {self._lock_name} from {caller2} "
            f"returned {retval} info: {self._Rlock.__repr__()}"
        )
        return retval

    __enter__ = acquire

    def release(self) -> None:
        """Releases the lock."""
        caller = sys._getframe().f_back
        if caller is not None:
            caller2 = caller.f_code.co_name
        else:
            caller2 = "*Unknown*"
        LOG.debug(f"pyadtpulse released lock {self._lock_name} from {caller2}")
        self._Rlock
        LOG.debug(
            f"pyadtpulse released lock {self._lock_name} from {caller2} "
            f"info: {self._Rlock.__repr__()}"
        )

    def __exit__(self, t, v, b):
        """Automatically release lock on exit.

        Args:
            t (_type_): _description_
            v (_type_): _description_
            b (_type_): _description_
        """
        self._Rlock.release()
