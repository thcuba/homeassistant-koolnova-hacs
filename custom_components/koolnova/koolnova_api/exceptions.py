"""Exceptions for Koolnova."""

from typing import Any


class KoolnovaError(Exception):
    """Error from Koolnova API."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception.

        Args:
            args: the message or root cause of the error
        """
        Exception.__init__(self, *args)
