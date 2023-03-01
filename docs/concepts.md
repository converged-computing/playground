# Concepts

## Playground

A playground is an interactive environment to test out a piece of software.
It typically is delivered via a notebook, and provided in a container
that is pre-built with the software. There are two modes of operation:

 - **local** deploy a tutorial container defined in a tutorial.yaml file
 - **repository** deploy a tutorial from a tutorials repository with one or more to choose from!

This means that you could theoretically target a named tutorial in a repository, or a local tutorial.yaml file:

```bash
# This is the default, with the docker backend
$ playground deploy tutorial.yaml

# Meaning you can just do this given a tutorial.yaml in the present working directory
$ playground deploy

# Or target a named tutorial in a repository!
$ playground deploy rse-ops/rse-ops/flux-tutorials radiuss-aws-2022
```


## Backend

A backend is a cloud, local, or other means to deploy a tutorial. E.g,
you can run `playground deploy` with a local Docker backend to run the
tutorial on your local machine. Current desired backends include:

 - **Docker**: run the tutorial via a Docker container (local)
 - **AWS**: run the tutorial on an AWS EC2 instance
 - **GCP**: run the tutorial on Google Compute Engine
 - **Podman**: run the tutorial via a Podman container (local or HPC)

And coming soon or hopefully (when resources allow or when requested):

 - **Singularity**: run the tutorial via a Singularity container (e.g., for HPC)
 - **Azure**: run the tutorial on Azure cloud

## Tutorial


A tutorial is a repository that conforms to a repository design that exports
its own API and metadata for the tool here. You can see an example of this at [rse-ops/flux-tutorials](https://github.com/rse-ops/flux-tutorials/).
It can also be a local `tutorial.yaml` file. For more information about the tutorial, see [our tutorial guide](tutorials.md).
