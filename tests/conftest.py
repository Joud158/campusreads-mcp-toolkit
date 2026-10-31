"""Keep pytest temporary files isolated from other Windows user contexts."""

import tempfile
from pathlib import Path


def pytest_configure(config):
    # Respect an explicit --basetemp supplied by the caller.
    if config.option.basetemp is None:
        # The default pytest-of-<name> folder can have incompatible ACLs when
        # an editor sandbox and a normal terminal share the same TEMP path.
        directory = tempfile.TemporaryDirectory(prefix="campusreads-pytest-")
        config.option.basetemp = Path(directory.name) / "run"
        config.add_cleanup(directory.cleanup)
