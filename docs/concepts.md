# Concepts

## Playground

A playground is an interactive environment to test out a piece of software.
It typically is delivered via a notebook, and provided in a container
that is pre-built with the software.

## Backend

A backend is a cloud, local, or other means to deploy a tutorial. E.g,
you can run `playground deploy` with a local Docker backend to run the
tutorial on your local machine. Current desired backends include:

 - **Docker**: run the tutorial via a Docker container (local)
 - **AWS**: run the tutorial on an AWS EC2 instance
 - **GCP**: run the tutorial on Google Compute Engine

And coming soon or hopefully (when resources allow):

 - **Podman**: run the tutorial via a Podman container (local or HPC)
 - **Singularity**: run the tutorial via a Singularity container (e.g., for HPC)
 - **Azure**: run the tutorial on Azure cloud

## Tutorial

A tutorial is a repository that conforms to a repository design that exports
its own API and metadata for the tool here. You can see an example at [rse-ops/flux-tutorials](https://github.com/rse-ops/flux-tutorials/).

### Design

Each tutorial is basically a notebook and a base container, where the base container should have jupyter installed and your tutorial software. Each tutorial should be put under a named group, under "tutorials":

```yaml
tutorials/

    latest/
      # This is optional, if a base container is elsewhere it can be referenced
      Dockerfile

      # Supporting materials can go in this top level directory
      # This material you don't want to share publicly (in the UI)
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
And it's up to you how to organize! In the example above we use a latest and version, however you could also namespace to cloud providers and dates, or even HPC conferences that you present them at. Also note the contents under each. If a Dockerfile is provided in the tutorial folder, this should build the base, and this is specified in container.yaml. By default, the containers will build to ghcr.io/<org>/<repository>/<tutorial>. For the tutorial here, we might see ghcr.io/rse-ops/flux-tutorial:latest.
Metadata

Each tutorial folder has a tutorial.yaml file that will be used to deploy the tutorial and to generate the site (with metadata). Importantly, you should provide the name of an associated project repository on GitHub that will provide more metadata about the project, along with labels that map to instance preferences for each. This is currently a limited set, and will be expanded.

```yaml
title: Flux Tutorial Latest
container: ghcr.io/rse-ops/flux-tutorial:latest
project:
  github: flux-framework/flux-core
labels:
    memory: 8000
notebooks:
  - name: 01-getting-started.ipynb
    title: Getting Started
    tags: ['jobs', 'getting-started', 'aws']
  - name: 02-developer-tutorial.ipynb
    title: Developer Tutorial
    tags: ['developer', 'aws']
```
We currently ask for a GitHub identifier to retrieve metadata about the project. The current assumption above is that tutorials are grouped based on similar resource needs using the same container.

You can read a more complete guide for making your own tutorial repositories under [tutorials.md](tutorials.md)
