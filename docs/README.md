# User Guide

Welcome to playground tutorials!

> the fun cloud wrapper 🍬️ to deploy tutorial containers! 📦️

Playground is a small command line client to make it easy to deploy containerized
tutorials, whether they be in a notebook or VSCode. There are two modes of operation:

 - **local** deploy a tutorial defined in a tutorial.yaml file
 - **repository** deploy a tutorial from a tutorials repository with one or more to choose from!

## Quick Start

Install!

```bash
$ pip install playground-tutorials[all]
```

Either generate your own [tutorial.yaml](https://converged-computing.github.io/playground/#/tutorials?id=metadata) file and then run it!

```bash
# This is the default, with the docker backend
$ playground deploy ./tutorial.yaml

# Meaning you can just do this given a tutorial.yaml in the present working directory
$ playground deploy
```

or list tutorials in an [example repository](https://github.com/rse-ops/rse-ops/flux-tutorials) (shown below):

```bash
# Show me tutorials available
$ playground list rse-ops/flux-tutorials

# Inspect metadata...
$ playground show rse-ops/flux-tutorials radiuss-aws-2022

# Target the named tutorial to deploy!
$ playground deploy rse-ops/rse-ops/flux-tutorials radiuss-aws-2022
```
This means you can provide several tutorials deployable via GitHub (the second use case), or private
(or otherwise file-based) tutorials that are cloned first (the first case). More details are provided in our guides below!

## Guides

Check out any of the guides to get started!

 - [install](install.md): brief notes on installation steps
 - [concepts](concepts.md): concepts for a playground
 - [config](config.md): custom configuration (optional)
 - [playground](cli.md): is documentation for the playground client.
 - [tutorials](tutorials.md): instructions for making your own tutorial container.
 - [gallery.md](gallery.md): collection of tutorial containers available (will eventually have automated discovery)
