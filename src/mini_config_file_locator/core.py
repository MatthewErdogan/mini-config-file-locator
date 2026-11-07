"""Core search logic for mini-config-file-locator.

Why this exists
---------------
Tools that read a project-level config file (``pyproject.toml``,
``.editorconfig``, ``.gitignore``) almost always want the *nearest* file
at or above the current working directory, not the first one found in a
fixed list of global locations.  Implementing that walk by hand is easy
to get subtly wrong: symlinks, a relative start path, a start path that
is a file rather than a directory, and the filesystem root are all cases
that people forget.

Design decision
---------------
The walk is *inclusive*: the starting directory itself is checked before
any parent.  This matches the intuition that a config file living in the
current directory should win over one in an ancestor, and it is the rule
used by tools like ``git`` and ``ruff``.  The alternative (start at the
parent) was rejected because it makes ``find_config("a.cfg", ".")``
surprising.
"""

from __future__ import annotations

import os
from typing import Optional


def _normalise_start(start: str) -> str:
    """Return an absolute directory path for *start*.

    A file path is interpreted as the directory that contains it, which
    is what callers almost always mean when they pass ``__file__``.
    """
    path = os.path.abspath(start)
    if not os.path.isdir(path):
        # ``os.path.dirname`` of a bare filename is the empty string, so
        # fall back to the current directory in that case.
        parent = os.path.dirname(path)
        path = parent if parent else os.path.abspath(os.curdir)
    return path


def find_config_in(start: str, name: str) -> Optional[str]:
    """Search *start* and its ancestors for a file called *name*.

    Parameters
    ----------
    start:
        Directory to begin the search in.  A path to a file is treated
        as the directory containing that file.
    name:
        Base name of the config file, e.g. ``"pyproject.toml"``.  It must
        not contain a path separator; if it does, a ``ValueError`` is
        raised, because a relative path would make the upward walk
        ambiguous.

    Returns
    -------
    The absolute path of the first match, or ``None`` if no ancestor
    contains the file.
    """
    if not name:
        raise ValueError("name must be a non-empty string")
    if os.sep in name or (os.altsep and os.altsep in name):
        raise ValueError("name must be a bare filename, not a path: %r" % (name,))

    current = _normalise_start(start)
    while True:
        candidate = os.path.join(current, name)
        if os.path.isfile(candidate):
            # ``os.path.isfile`` follows symlinks, so a symlink to a
            # regular file counts as a match.  A broken symlink does not.
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            # Reached the filesystem root without a match.
            return None
        current = parent


def find_config(name: str, start: Optional[str] = None) -> Optional[str]:
    """Convenience wrapper around :func:`find_config_in`.

    *start* defaults to the current working directory.  Passing ``None``
    explicitly is the same as omitting it, which keeps the common call
    ``find_config("pyproject.toml")`` short.
    """
    if start is None:
        start = os.getcwd()
    return find_config_in(start, name)
