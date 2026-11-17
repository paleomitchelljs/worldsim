"""Where runs live, and how a run named on the command line is found.

The runs root is $WORLDSIM_RUNS, or sim/runs/ beside this file (D2, U,
2026-11-17). A bare name (no path separator), such as `base_seed101` or the
pattern `base_seed10?`, is looked up in the root; anything with a separator,
such as `runs/x` or an absolute path into the old Dropbox folder, is used as
given. Kept outside the wsim package so snapcheck.py can import it without
fixing which wsim is loaded.
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def root():
    """The runs root, created if missing."""
    r = os.path.expanduser(os.environ.get("WORLDSIM_RUNS") or
                           os.path.join(HERE, "runs"))
    os.makedirs(r, exist_ok=True)
    return r


def path(name):
    """A run folder or file: a bare name resolves against the root."""
    if os.sep in name or (os.altsep and os.altsep in name):
        return name
    return os.path.join(root(), name)


def expand(names):
    """Resolve names and expand glob patterns (for quoted patterns the
    shell did not expand); a name matching nothing is kept, so the caller
    reports it as missing."""
    out = []
    for n in names:
        p = path(n)
        hits = sorted(glob.glob(p)) if glob.has_magic(p) else []
        out.extend(hits or [p])
    return out
