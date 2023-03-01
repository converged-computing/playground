# GitHub Action

We provide a GitHub action to make it easier to test local tutorial.yaml files, before they are
released. You can either test a local tutorial.yaml with a remote container (already built)
or one you've just built in your action.

## Variables

| Name | Description | Default | Required |
|------|-------------|---------|----------|
|source | repository or filename to test | unset | true |
| tutorial |name of tutorial | local | false |
| backend | backend tester to use | docker | false |
| branch | branch of converged-computing/playground to use | false | main |

## Example

Here is an annotated example that shows a few cases:

```yaml
name: Test Action
on:
  pull_request: []

jobs:
  test-local-tutorial:
    name: Test a local tutorial file
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Change working directory
        run: cd tutorials/name-of-tutorial

      # Make sure to build your container here, otherwise
      # it will be pulled (or attempted to pull) from a registry
      - name: Build Container
        run: docker build -t ghcr.io/my-org/name-of-tutorial:latest .

      - name: Test Tutorial
        uses: converged-computing/playground@main
        with:
          source: ./tutorial.yaml

  test-remote-tutorial:
    name: Test a remote tutorial
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3
      - name: Test Tutorial
        uses: converged-computing/playground@main
        with:
          source: my-org/tutorials
          tutorial: name-of-tutorial
```

For each of the above, if you don't install your own version of playground,
the action will install the "branch" specified for you.

You can see the testing example in [test-action.yaml](https://github.com/converged-computing/playground/tree/main/.github/workflows/test-action.yml).
