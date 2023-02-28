# Config

Playground comes with a config command you can use to adjust settings and defaults.

```bash
$ playground config --help
usage: playground config [-h] [--central] [params ...]

update configuration settings. Use set or get to see or set information.

positional arguments:
  params      Set or get a config value, edit the config, add or remove a list variable, or create a user-specific config.
              playground config set key value
              playground config set key:subkey value
              playground config get key
              playground edit
              playground config inituser
              playground config remove backend aws
              playground config add backend aws

optional arguments:
  -h, --help  show this help message and exit
  --central   make edits to the central config file.
```

## User Settings

By defaults, settings are stored in `settings.yml' in the main playground
install directory. To create your own copy to customize (and take precedence over the default)
you can do:

```bash
$ playground config inituser
```

To create your user settings in `~/.playground/settings.yml`. You can edit this file manually,
or via the commands shown above or:

```bash
$ playground config edit
```

## Settings

The following settings are supported.

| Name | Description | Type | Default |
|------|-------------|------|---------|
|backends | list of backends supported | list | `[docker, google, aws]` |
|config_editor | default editor for editing the settings.yml | string | vim |
| default_backend | default backend for running tutorials | string | docker |
| disable_cloud_select | Disable using cloud select to select instance by price | boolean | false |
| google | block for google cloud settings | object | |
| google.zone | default google cloud zone | string | us-central1-a |
| google.instance | default google compute engine machine type | string | n2-standard-2 |
| aws | block for amazon web services settings | object | |
| aws.zone | default amazon web services zone | string | us-east-1 |
| aws.instance | default amazon web services instance type | string | t2.medium |
