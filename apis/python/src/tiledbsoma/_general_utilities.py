# Copyright (c) 2021-2023 The Chan Zuckerberg Initiative Foundation
# Copyright (c) 2021-2023 TileDB, Inc.
#
# Licensed under the MIT License.

"""General utility functions.
"""

import sys

import tiledb
from pkg_resources import DistributionNotFound, get_distribution


def get_SOMA_version() -> str:
    """Returns semver-compatible version of the supported SOMA API.

    Lifecycle: Experimental.
    """
    return "0.2.0-dev"


def get_implementation() -> str:
    """Returns the implementation name, e.g., "python-tiledb".

    Lifecycle: Experimental.
    """
    return "python-tiledb"


def get_implementation_version() -> str:
    """Returns the package implementation version as a semver.

    Lifecycle: Experimental.
    """
    try:
        return get_distribution("tiledbsoma").version
    except DistributionNotFound:
        return "unknown"


def get_storage_engine() -> str:
    """Returns underlying storage engine name, e.g., "tiledb".

    Lifecycle: Experimental.
    """
    return "tiledb"


def show_package_versions() -> None:
    """Nominal use is for bug reports, so issue filers and issue fixers can be on
    the same page.

    Lifecycle: Experimental.
    """
    print("tiledbsoma.__version__   ", get_implementation_version())
    print("tiledb.__version__       ", tiledb.__version__)
    print(
        "core version             ",
        ".".join(str(ijk) for ijk in list(tiledb.libtiledb.version())),
    )
    print("python version           ", ".".join(str(v) for v in sys.version_info))
