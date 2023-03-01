# Gallery

This is a small gallery of tutorials available. More coming soon!

 - [Flux Framework](https://github.com/rse-ops/flux-tutorials)

**Coming Soon**

We've completed a VSCode base tutorial template [rse-ops/rust-tutorials](https://github.com/rse-ops/rust-tutorials)
and are finishing up adding the site generation.

## Example

We provide an example local `tutorial.yaml` that has the following structure:

```yaml
title: "Flux Tutorial: 2022 for RADIUSS"

# Resources needed for the instance to run the container on
resources:
  memory: 4000 # GB
  cpus: 1

container:
  name: ghcr.io/rse-ops/flux-radiuss-aws-2022:jupyter-3.0.0
  env:
    - name: password
      optional: true

  # All ports provided
  # Tutorials will also expose 443 and 80 by default
  ports:
    - 8000:8000
  # Single port to reference for the main user interface
  expose: 8000

project:
  github: flux-framework/flux-core
notebooks:
  - name: 01-radiuss-aws-flux.ipynb
    title: Flux Jobs Tutorial
```

You can test it in our repository:

```bash
$ cd ./example
# ./tutorial.yaml is in the present working directory

# Deploy with docker, headless
$ playground deploy -o headless=True

# Stop the tutorial
$ playground stop
```
