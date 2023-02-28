### docker

Deploy a playground tutorial from a GitHub repository.

```bash
$ playground deploy github.com/rse-ops/flux-tutorials radiuss-aws-2022
```

To define an environment variable (e.g., the password for a notebook for this tutorial) use `-e`.
# Backends

Playground currently supports the following backends:

 - [Docker (local)](#docker) (default)
 - [Google Cloud "gcp"](#gcp)
 - [Amazon Web Services "aws"](#aws)
 - [Podman (local)](#podman)


## docker

The docker backend is the default, meaning you run the container locally. Here are examples for
doing this, where the process is left streaming to your terminal to press Control +C to end the tutorial:

```bash
$ playground deploy rse-ops/flux-tutorials radiuss-aws-2022
```

In this case, there is no need for a `playground stop` because you can just kill the process.
However, deploy (for docker) supports an option to indicate you want a headless start.
This is useful for non-interactive use cases, or just testing.

```bash
$ playground deploy -o headless=True rse-ops/flux-tutorials radiuss-aws-2022
```

Check your container is running with `docker ps`.
After that, you can stop your tutorial like this:

```bash
$ playground stop rse-ops/flux-tutorials radiuss-aws-2022
```

And then again check `docker ps` to ensure it is stopped!
If you were using this function in Python, you would provide the option as a keyword argument to deploy:

```python
client.deploy("radiuss-aws-2022", headless=True)
client.stop("radiuss-aws-2022")
```

### gcp

To deploy an instance on GCP, you can also control the config of the instance via the
environment (given not defined for the tutorial). For a basic deployment:

```bash
# Do a basic deployment
$ playground deploy --backend gcp rse-ops/flux-tutorials radiuss-aws-2022

# Stop the tutorial
$ playground stop --backend gcp rse-ops/flux-tutorials radiuss-aws-2022
```

### aws

We also support an aws backend. This means creating a security group (and matching virtual cloud) for
the tutorials (with http/https access) and then launching a container to run the same start command.

```bash
# Start the tutorial
$ playground deploy --backend aws rse-ops/flux-tutorials radiuss-aws-2022

# Add --debug to see interface progress
$ playground --debug deploy --backend aws rse-ops/flux-tutorials radiuss-aws-2022

# And then to stop:
$ playground stop --backend aws rse-ops/flux-tutorials radiuss-aws-2022
```

## podman

The podman client is functionally equivalent to docker, except we use the Podman client instead!


```bash
# Start the tutorial (interactive)
$ playground deploy --backend podman rse-ops/flux-tutorials radiuss-aws-2022
# press Control+C to stop it

# Start the tutorial in headless mode
$ playground deploy --backend podman -o headless=True rse-ops/flux-tutorials radiuss-aws-2022

# Stop the headless tutorial
$ playground stop --backend podman rse-ops/flux-tutorials radiuss-aws-2022
```
