# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import copy
import os


def chunks(listing, chunk_size):
    """
    Yield successive chunks from listing. Chunkify!
    """
    for i in range(0, len(listing), chunk_size):
        yield listing[i : i + chunk_size]


def slugify(name):
    """
    Slugify a name, replacing spaces with - and lowercase.
    """
    for char in [" ", ":", "/", "\\"]:
        name = name.replace(char, "-")
    name = name.replace("---", "-").replace("--", "-")
    return name.lower()


def print_bytes(byt, suffix="B"):
    """
    Pretty format size in bytes
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(byt) < 1024.0:
            return f"{byt:3.1f} {unit}{suffix}"
        byt /= 1024.0
    return f"{byt:.1f} Yi{suffix}"


def mb_to_bytes(mb):
    """
    Convert mb to bytes, usually so we can derive a better format.
    """
    return mb * (1048576)


def get_hash(obj):
    """
    Get a hash for a random object (set, tuple, list, dict)

    All nested attributes must at least be hashable!
    """
    if isinstance(obj, (set, tuple, list)):
        return tuple([get_hash(o) for o in obj])
    if not isinstance(obj, dict):
        return hash(obj)
    copied = copy.deepcopy(obj)
    for k, v in copied.items():
        copied[k] = get_hash(v)
    return hash(tuple(frozenset(sorted(copied.items()))))


def get_user():
    """
    Get the name of the user. We first try to import pwd, but fallback to
    extraction from the environment.
    """
    try:
        import pwd

        return pwd.getpwuid(os.getuid())[0]
    except Exception:
        return os.environ.get("USER")
