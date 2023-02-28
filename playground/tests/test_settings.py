#!/usr/bin/python

# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import os

import pytest

from playground.main.settings import Settings

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)

from .helpers import get_settings  # noqa


def test_invalid_properties(tmp_path):
    """
    Test invalid setting property
    """
    settings = Settings(get_settings(tmp_path))
    assert settings.config_editor == "vim"
    settings.set("config_editor", "code")
    with pytest.raises(SystemExit):
        settings.set("invalid_key", "invalid_value")
    assert settings.config_editor == "code"


def test_set_get(tmp_path):
    """
    Test variable set/get
    """
    settings = Settings(get_settings(tmp_path))
    zone = settings.get("google:zone")
    assert isinstance(zone, str)
    assert "us-central1-a" == zone

    # Just check the first in the list
    assert settings.google["zone"] == zone
    assert settings.get("google:zone") == zone
    assert settings.get("google")["zone"] == zone
