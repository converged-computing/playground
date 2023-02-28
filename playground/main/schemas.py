# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

## ContainerConfig Schema

import playground.main.backends as backends

schema_url = "http://json-schema.org/draft-07/schema"

# This is also for latest, and a list of tags

# The simplest form of aliases is key/value pairs
keyvals = {
    "type": "object",
    "patternProperties": {
        "\\w[\\w-]*": {"type": "string"},
    },
}

envars = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "optional": {"type": "boolean", "default": True},
    },
    "required": ["name"],
}

backend_properties = {"zone": {"type": "string"}, "instance": {"type": "string"}}
tutorial_resources = {
    "type": "object",
    "properties": {
        "memory": {"type": "number"},
        "cpus": {"type": "number"},
    },
}
tutorial_container = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "env": {"type": "array", "items": envars},
        "ports": {"type": "array", "items": {"type": "string"}},
        "expose": {"type": ["string", "number"]},
        "https": {"type": "boolean", "default": True},
    },
    "required": ["name"],
}

# Currently just supporting GitHub, could extend to others.
project = {
    "type": "object",
    "properties": {"github": {"type": "string"}},
    "required": ["github"],
}


notebook = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "title": {"type": "string"}},
    "required": ["name", "title"],
}
tutorial_properties = {
    "tutorial": {
        "type": "object",
        "properties": {
            "title": {"type", "string"},
            "container": tutorial_container,
            "resources": tutorial_resources,
            "project": project,
            "notebooks": {"type": "array", "items": notebook},
        },
        "additionalProperties": False,
        "required": ["title", "container", "project", "notebooks"],
    },
}

tutorials = {
    "$schema": schema_url,
    "title": "Tutorials Schema",
    "type": "object",
    "patternProperties": {
        "\\w[\\w-]*": tutorial_properties,
    },
}


# Currently all of these are required
settings_properties = {
    "default_backend": {"type": "string"},
    "config_editor": {"type": "string"},
    "disable_cloud_select": {"type": "boolean"},
    "aws": {
        "type": "object",
        "properties": backend_properties,
        "additionalProperties": False,
        "required": ["zone"],
    },
    "google": {"type": "object", "properties": backend_properties},
    "backends": {
        "type": "array",
        "items": {"type": "string", "enum": backends.backend_names},
    },
}

settings = {
    "$schema": schema_url,
    "title": "Settings Schema",
    "type": "object",
    "required": [
        "disable_cloud_select",
        "backends",
        "google",
        "aws",
    ],
    "properties": settings_properties,
    "additionalProperties": False,
}
