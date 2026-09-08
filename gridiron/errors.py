"""The error family: every refusal in this engine descends from one name."""

from __future__ import annotations


class GridError(Exception):
    """Base for everything this engine refuses to do."""


class Invalid(GridError):
    """The request contradicts itself or the grammar."""


class Missing(GridError):
    """The cell, name, or function addressed does not exist."""


class Circular(GridError):
    """A formula depends on itself and iterative solve is off."""


class Unparseable(GridError):
    """The formula text does not survive the parser, with the spot named."""
