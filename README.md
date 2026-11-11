# mini-config-file-locator

Search upward from a starting directory for a named config file and return
the absolute path of the first match, or `None` if there is no match.

```python
import os
from mini_config_file_locator import find_config, find_config_in

# Start from the current working directory (the common case).
path = find_config("pyproject.toml")
if path is not None:
    with open(path, "r", encoding="utf-8") as handle:
        contents = handle.read()

# Or start somewhere explicit. A file path is treated as the directory
# that contains it, which makes `__file__` a valid argument.
path = find_config_in(os.path.dirname(__file__), "pyproject.toml")
path = find_config_in(__file__, "pyproject.toml")
```

## Why this exists

Most tools that read a project-level config file want the *nearest* copy at
or above the working directory, not a fixed global path. Writing that walk
by hand tends to miss the same handful of cases: a start path that is a file
rather than a directory, a relative start path, a directory whose name
matches the config filename, and the filesystem root. This library handles
those cases and nothing else.

The trade-off is a deliberately narrow API. There is no glob support, no
list of candidate names, and no caching. Those can be layered on top by the
caller; adding them here would force choices about precedence and
invalidation that this library does not need to make.

## Behaviour

The search is **inclusive**: the starting directory is checked before any
ancestor, so a config file in the current directory wins over one higher up.
Only regular files count as matches; a directory whose name equals the
config filename is skipped. Symlinks are followed, so a symlink to a regular
file is a match and a broken symlink is not.

`name` must be a bare filename. Passing a value containing a path separator
raises `ValueError`, because a relative path would make the upward walk
ambiguous. An empty `name` also raises `ValueError`.

## API

- `find_config(name, start=None) -> Optional[str]` — `start` defaults to the
  current working directory. Returns the absolute path of the first match.
- `find_config_in(start, name) -> Optional[str]` — same search with `start`
  required and first, matching the order of the arguments in the function
  name.

Both return `None` when no ancestor contains `name`.

## The awkward edge

`find_config_in` walks up to the filesystem root. If you call it from a
directory that is not inside the project you expected, it will happily keep
going and may find a config file in your home directory or in `/`. The
function does not stop at a repository boundary, a `.git` directory, or any
other marker. If you need that, check the returned path against the
directory you consider the boundary.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

