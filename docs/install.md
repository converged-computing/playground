# Installation

You can typically create an environment

```bash
$ python -m venv env
$ source env/bin/activate
```

You can install with no backends (defaults to just docker) or podman)
or specific ones:

```bash
# No backends
$ pip install playground-python

# All backends
$ pip install playground-python[all]

# Google Cloud
$ pip install playground-python[google]

# Amazon web services
$ pip install playground-python[aws]
```

or install from the repository:

```bash
$ git clone https://github.com/converged-computing/playground
$ cd playground
$ pip install .
```

To do a development install (from your local tree):

```bash
$ pip install -e .
```

This should place an executable, `playground` in your path.


## Podman

If you want to use Podman containers, you'll need podman!
There are notes on installing Podman [here](https://podman.io/getting-started/installation)
but in practice I found them not super great. What I ultimately had to do for Ubuntu 20.04 to run a container is:

```bash
sudo apt-get -y update
sudo apt-get install -y podman
sudo usermod --add-subuids 10000-75535 $USER
sudo usermod --add-subgids 10000-75535 $USER
podman system migrate
```

and then test with

```bash
podman run busybox
```
