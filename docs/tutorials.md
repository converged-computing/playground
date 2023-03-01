# Tutorials

A playground tutorial repository is a repository that is designed and structured
to have automated builds that can be deployed with the playground tool. On a high
level, you can request a notebook or other environment to try out
software. The repository can provide (optionally) automated builds for containers,
or just notebooks that use containers elsewhere.

A brief guide is provided here for how to create a repository, and for more information,
you can look at the [tutorial-actions](https://github.com/rse-ops/tutorial-actions).
For current tutorials, see the [gallery](gallery.md).

## What is a tutorial?

A tutorial is a lab notebook (or similar environment) that can be requested
by a user to try out software. By way of providing metadata and assets in a
predictibly organized version-controlled format, we can easily deploy
tutorials.

## What is a tutorial repository?

A tutorial repository provides:

1. An organized structure of named tutorials
2. Metadata to go along with each tutorial folder in a `tutorial.yaml`
3. A Dockerfile (optional) that provides an automated build for a tutorial.
4. Notebooks or other assets for the tutorials.
5. A web interface that displays tutorials available, and provides a static API.

## How do we do the automation above?

The [tutorial-actions](https://github.com/rse-ops/tutorial-actions) (described briefly below)
provide most of this functionality, and can be added to your repository to use.

### ⭐️ Automation ⭐️

If you want to deploy your own tutorials repository, you can use any of the ["-tutorials" repos](https://github.com/orgs/rse-ops/repositories?q=-tutorials&type=all&language=&sort=) in the rse-ops organization as a template! The design is outlined
here, and instructions described. Basically, you'll be adding workflows to your `.github/workflows` to do
each of the following.

#### Site and Contributor CI

Each workflow repository deploys its own site and project (repository) metadata.
The initial generation of this site (and continued generation of the metadata, nightly)
is determined by the [workflows/update-data.yaml](https://github.com/rse-ops/tutorial-actions/blob/main/workflows/update-data.yaml) action.
First, add a [contributor-ci.yaml](https://github.com/rse-ops/flux-tutorials/blob/main/contributor-ci.yaml) file to the root of your repository.
It should include (under repos) the GitHub identifier for the main project you
are demo-ing.

```yaml
member_orgs: []
orgs: []
outdir: _data/cci
repos:
- flux-framework/flux-core
```

In the example above, we are showcasing [https://github.com/flux-framework/flux-core](https://github.com/flux-framework/flux-core).
Then, you can finalize the generation and using the action by adding
the `workflows/update-data.yaml` example to your `.github/workflows` directory.

```yaml
name: Update Contributor CI Data
on:
  workflow_dispatch:
  push:
    branches:
      - main
  schedule:
    - cron:  '0 3 * * *'

jobs:
  extraction:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Repository
      uses: actions/checkout@v3

    - name: Update Tutorial Site
      uses: rse-ops/tutorial-actions/site@main
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
```

#### ✅️ Validation ✅️

The metadata that your site provides (where the site is generated and maintained via the action above)
must conform to a specific schema, and the container that it promises must be pull-able. To ensure
that your generated metadata is valid, you can use the the [validate](https://github.com/rse-ops/tutorial-actions/tree/main/validate)
action, and an example is provided in the [workflows/validate.yaml](https://github.com/rse-ops/tutorial-actions/blob/main/workflows/validate.yaml)
workflow. Add this to your `.github/workflows` to activate it in your tutorials repository. For validation, we build the site that displays the tutorials
and check the following:

1. Your tutorial names are all lowercase, with only special characters `-` allowed
2. A title, container, and project (with github name) are defined
3. The GitHub name only has one slash (no git@ or https, etc.)
4. The docker container needs to be pullable.

#### 🚧️ Container Builds 🚧️

Each workflow repository deploys any needed automated builds, each defined by a `Dockerfile`
in the root of a container directory. To support this build, we use [uptodate](https://github.com/vsoch/uptodate)
that requires an `uptodate.yaml` file in the root of a tutorial. As an example, here is how
to build a container with one build argument for a `22.04` version of ubuntu:

```
dockerbuild:

  build_args:
    ubuntu_version:
      key: ubuntu
      versions:
       - "22.04"
```

Although this workflow uses uptodate, you aren't require to - a Dockerfile with your own
custom build workflow would work too! As mentioned previously, the initial generation of this site (and continued generation of the metadata, nightly)
is determined by the [workflows/update-data.yaml](https://github.com/rse-ops/tutorial-actions/blob/main/workflows/update-data.yaml) action.
It's again helpful to look at examples in ["-tutorials" repos](https://github.com/orgs/rse-ops/repositories?q=-tutorials&type=all&language=&sort=) for how these files (alongside build args) are used. If you are comfortable with
Docker, you basically are defining the build args to use in your Dockerfile via
this file, and it can be a matrix.

### 🔍️ Details 🔎️

#### Repository Structure

Each tutorial is basically a notebook and a base container, where the base
container should have jupyter installed and your tutorial software. Each tutorial
should be put under a named group, under "tutorials":

```console
tutorials/

    latest/

      # This is also optional, but it's nice to show how to build/run the container locally
      README.md

      # This is optional, if a base container is elsewhere it can be referenced
      Dockerfile

      # Supporting materials can go in this top level directory
      # This material you don't want to share publicly (in a UI someday)
      presentation.pptx

      # Material in this directory can be linked/shared in the playground
      public/
          presentation.pdf

      # Numbered to present a logical ordering (like a table of contents)
      notebooks/
          01-getting-started.ipynb
          02-developer-tutorial.ipynb

      # Metadata about the tutorials and resources
      tutorial.yaml
    22.04/
        ...
```

And it's up to you how to organize! In the example above we use a latest and version,
however you could also namespace to cloud providers and dates, or even HPC conferences
that you present them at. Also note the contents under each. If a `Dockerfile`
is provided in the tutorial folder, this should build the base, and this is specified
in `container.yaml`. By default, the containers will build to `ghcr.io/<org>/<repository>/<tutorial>`.
For the tutorial here, we might see `ghcr.io/rse-ops/flux-tutorial:latest`.

#### Metadata

Each tutorial folder has a `tutorial.yaml` file that will be used to deploy
the tutorial and to generate the site (with metadata). Importantly, you should
provide the name of an associated project repository on GitHub that will provide
more metadata about the project, along with labels that map to instance preferences
for each. This is currently a limited set, and will be expanded.

```yaml
title: "Flux Tutorial: 2022 for RADIUSS"

resources:
  cpus: 1      # number of cores
  memory: 4000 # This should be a number in GB

container:
  name: ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0
  # This should be changed for a production deployment
  env:
    name: GLOBAL_PASSWORD
    optional: true
  # Note that ports 80 and 443 are automatically exposed, these should be extra
  ports:
    - 8000:8000

  # This is the main port to tell the user about
  expose: 8000
project:
  github: flux-framework/flux-core
notebooks:
  - name: 01-radiuss-aws-flux.ipynb
    title: Flux Jobs Tutorial
```

We currently ask for a GitHub identifier to retrieve metadata about the project.
Note that for the resources spec, we use [Cloud select](https://converged-computing.github.io/cloud-select/#/) to find a cost effective
instance, given that the tutorial runner is using a region and cloud that we have prices for.
The current assumption above is that tutorials are grouped based on similar resource needs using the same container.

#### Suggested Interactions

The following are suggested setups for your tutorials. You are free to choose
to do this however you like, however the assumption is that we will deploy
a container that has some service on a port.

#### Environment Variables

If you are running a notebook, it's generally expected that
you'll provide the user with a browser to open a notebook. This means
we need to authenticate, which can be done by way of the container user
as a username, and a custom password from the environment. You should
provide a default password in the container (primarily for development)
but also define it as an environment variable that can be controlled
by the deployment technology. As an example, with our config here,
the variable `GLOBAL_PASSWORD` is defined in our Dockerfile,
but also can be defined on deploy for a custom password.

##### Entrypoint Command

The start of your container should generally run a notebook to demonstrate your
software. It's also recommended to post a welcome message to inform the user
of any needed credentials. As an example, the notebook here sets the password
for Jupyterlab from the environment, and prints a message to the user in the terminal:

```dockerfile
# This allows the running user to set the password on the container start
ENV GLOBAL_PASSWORD=${GLOBAL_PASSWORD}
CMD /bin/bash /welcome.sh && \
    echo "c.DummyAuthenticator.password = \"${GLOBAL_PASSWORD}\"" >> /home/fluxuser/jupyterhub_config.py && \
    PATH=$HOME/.local/bin:$PATH \
    flux start --test-size=4 /home/fluxuser/.local/bin/jupyterhub -f /home/fluxuser/jupyterhub_config.py
```

And the welcome script will show:

```console
🌀️ Welcome to the Flux Framework RADIUSS Tutorial! 🌀️
If you are running this locally (and can see this message)
You can open your browser to https://127.0.0.1.
We use self-signed certificates, so you can proceed.
Your login information is:

🥑️ user: fluxuser
🥑️ password: playground

Have fun! ⭐️🦄️⭐️
```

If you have any questions, please [let us know](https://github.com/converged-computing/playground/issues).
