# Commands

The following commands are supported when using `playground`:

## list

List is used to list tutorials associated with a repository.
Any of the following formats will work:

```bash
$ playground list rse-ops/flux-tutorials
$ playground list github.com/rse-ops/flux-tutorials
$ playground list https://github.com/rse-ops/flux-tutorials
```
```console
$ playground list rse-ops/flux-tutorials
🍓 radiuss-aws-2022
```

If/when we have a server or some central registry, we could have a `list-tutorials`
option to show repositories that are available. Note that the convention
above (for shortened repository names) will work for any command.

## show

To see the full JSON metadata for a particular repository, use `show`:

```bash
$ playground show https://github.com/rse-ops/flux-tutorials
```
```console
{
  "radiuss-aws-2022": {
    "tutorial": {
      "title": "Flux Tutorial: 2022 for RADIUSS",
      "container": {
        "name": "ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0",
        "env": [
          {
            "name": "password",
            "optional": true
          }
        ],
        "ports": [
          "443:443"
        ]
      },
      "project": {
        "github": "flux-framework/flux-core"
      },
      "notebooks": [
        {
          "name": "01-radiuss-aws-flux.ipynb",
          "title": "Flux Jobs Tutorial"
        }
      ]
    }
  }
}
```

By default (the above) if you don't provide a second argument (a tutorial name) you'll see
all the tutorials provided by the repository. To ask for one:

```bash
$ playground show https://github.com/rse-ops/flux-tutorials radiuss-aws-2022
```

show is useful because it shows you the environment variables that you can define (with `--env`) when
you deploy, e.g., "password" discussed next.

## deploy

### docker

Deploy a playground tutorial from a GitHub repository.

```bash
$ playground deploy github.com/rse-ops/flux-tutorials radiuss-aws-2022
```

To define an environment variable (e.g., the password for a notebook for this tutorial) use `-e`.
Deploy can take any number of `--envar` arguments, each of which should be in the format `key:value`.

```bash
$ playground deploy --env password=newplayground github.com/rse-ops/flux-tutorials radiuss-aws-2022
```
Note that order is important - the flags need to come before the position arguments! Press control C when you want
to kill it from running. And that's it!

### gcp

To deploy an instance on GCP, you can also control the config of the instance via the
environment (given not defined for the tutorial). For a basic deployment:

```bash
$ playground deploy --backend gcp github.com/rse-ops/flux-tutorials radiuss-aws-2022
```
```console
sudo docker pull ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0
sudo docker run -t --rm -p 8000:8000 ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0
https://111.111.44.222:8000
```
Since it will be pulling and starting a potentially large container, give it a minute or two
before following the link! When you are ready to stop:

```bash
$ playground stop --backend gcp github.com/rse-ops/flux-tutorials radiuss-aws-2022
```

### aws

We also support an aws backend. This means creating a security group (and matching virtual cloud) for
the tutorials (with http/https access) and then launching a container to run the same start command.

```bash
$ playground deploy --backend aws github.com/rse-ops/flux-tutorials radiuss-aws-2022
```

And then to stop:

```bash
$ playground stop --backend aws github.com/rse-ops/flux-tutorials radiuss-aws-2022
```

For cloud or backend specific options and examples, see our [backends guide](backends.md)


## config

Config is a handle to see or edit playground settings.

### get

See a playground setting

```bash
$ playground config get backends
backends                       ['docker', 'google', 'aws']
```

Or set a value:

```bash
$ playground config set default_backend docker
```

Or remove/add a value to a list:

```bash
$ playground config remove backends docker
$ playground config add backends docker
```

Create user settings

```bash
$ playground config inituser
```

And edit!

```bash
$ playground config edit
```

## test

Finally, test is  useful to quickly test the functionality of a specific tutorial
and repository.

```bash
$ playground test github.com/rse-ops/flux-tutorials radiuss-aws-2022
```
```console
$ playground test github.com/rse-ops/flux-tutorials radiuss-aws-2022
Testing deploy...
jupyter-3.0.0: Pulling from rse-ops/flux-radiuss-aws-2022
Digest: sha256:35c19161f5cff609cfc23e6c39f9037ec1575f2f66794fd102772485df7e9a1c
Status: Image is up to date for ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0
ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0
/usr/bin/docker run -d --rm --name vanessaflux-tutorial-2022-for-radiuss -p 8000:8000 ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0
⠧ https://127.0.0.1:8000 is ready: response code 200
Ready: https://127.0.0.1:8000
Testing for successful return code...
Testing for successful HTTP response...
Testing stop...
vanessaflux-tutorial-2022-for-radiuss
All tests pass!
```
