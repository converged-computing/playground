# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

docker_template = """#!/bin/bash

sudo apt-get update && \
sudo apt install -y docker.io && \

sudo addgroup --system docker && \
sudo adduser $USER docker && \
sudo newgrp docker && \
"""
