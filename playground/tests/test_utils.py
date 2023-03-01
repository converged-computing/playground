#!/usr/bin/python

# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import json
import os
import shutil

import pytest

import playground.utils as utils


def test_write_read_files(tmp_path):
    """
    test_write_read_files will test the functions write_file and read_file
    """
    print("Testing utils.write_file...")

    tmpfile = str(tmp_path / "written_file.txt")
    assert not os.path.exists(tmpfile)
    utils.write_file(tmpfile, "hello!")
    assert os.path.exists(tmpfile)

    print("Testing utils.read_file...")
    content = utils.read_file(tmpfile)
    assert content == "hello!"


def test_write_bad_json(tmp_path):
    bad_json = {"Wakkawakkawakka'}": [{True}, "2", 3]}
    tmpfile = str(tmp_path / "json_file.txt")
    assert not os.path.exists(tmpfile)
    with pytest.raises(TypeError):
        utils.write_json(bad_json, tmpfile)


def test_write_json(tmp_path):

    good_json = {"Wakkawakkawakka": [True, "2", 3]}
    tmpfile = str(tmp_path / "good_json_file.txt")

    assert not os.path.exists(tmpfile)
    utils.write_json(good_json, tmpfile)
    with open(tmpfile, "r") as f:
        content = json.loads(f.read())
    assert isinstance(content, dict)
    assert "Wakkawakkawakka" in content
    content = utils.read_json(tmpfile)
    assert "Wakkawakkawakka" in content


def test_check_install():
    """
    check install is used to check if a particular software is installed.
    If no command is provided, singularity is assumed to be the test case
    """
    print("Testing utils.check_install")

    is_installed = utils.check_install("echo")
    assert is_installed
    is_not_installed = utils.check_install("fakesoftwarename")
    assert not is_not_installed


def test_get_installdir():
    """
    Get install directory should return the base of where playground
    is installed
    """
    print("Testing utils.get_installdir")

    whereami = utils.get_installdir()
    print(whereami)
    assert whereami.endswith("playground")


def test_run_command():
    print("Testing utils.run_command")
    result = utils.run_command(["echo", "hello"])
    assert result["message"] == "hello\n"
    assert result["return_code"] == 0


def test_get_file_hash():
    print("Testing utils.get_file_hash")
    here = os.path.dirname(os.path.abspath(__file__))
    testdata = os.path.join(here, "testdata", "hashtest.txt")
    assert (
        utils.get_file_hash(testdata)
        == "6bb92117bded3da774363713657a629a9f38eac2e57cd47e1dcda21d3445c67d"
    )
    assert utils.get_file_hash(testdata, "md5") == "e5d376ca96081dd561ff303c3a631fd5"


def test_copyfile(tmp_path):
    print("Testing utils.copyfile")
    original = str(tmp_path / "location1.txt")
    dest = str(tmp_path / "location2.txt")
    print(original)
    print(dest)
    utils.write_file(original, "CONTENT IN FILE")
    utils.copyfile(original, dest)
    assert os.path.exists(original)
    assert os.path.exists(dest)


def test_get_tmpdir_tmpfile():
    print("Testing utils.get_tmpdir, get_tmpfile")
    tmpdir = utils.get_tmpdir()
    assert os.path.exists(tmpdir)
    assert os.path.basename(tmpdir).startswith("playground")
    shutil.rmtree(tmpdir)
    tmpdir = utils.get_tmpdir(prefix="name")
    assert os.path.basename(tmpdir).startswith("name")
    shutil.rmtree(tmpdir)
    tmpfile = utils.get_tmpfile()
    assert "playground" in tmpfile
    os.remove(tmpfile)
    tmpfile = utils.get_tmpfile(prefix="pancakes")
    assert "pancakes" in tmpfile
    os.remove(tmpfile)


def test_mkdir_p(tmp_path):
    print("Testing utils.mkdir_p")
    dirname = str(tmp_path / "input")
    result = os.path.join(dirname, "level1", "level2", "level3")
    utils.mkdir_p(result)
    utils.mkdirp([result])
    assert os.path.exists(result)


def test_print_json():
    print("Testing utils.print_json")
    result = utils.print_json({1: 1})
    assert result == '{\n    "1": 1\n}'
