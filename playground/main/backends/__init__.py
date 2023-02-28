from .aws import AmazonCloud
from .docker import DockerClient
from .google import GoogleCloud
from .podman import PodmanClient

# backends = {"aws": AmazonCloud}
backends = {
    "aws": AmazonCloud,
    "docker": DockerClient,
    "gcp": GoogleCloud,
    "google": GoogleCloud,
    "podman": PodmanClient,
}
backend_names = list(backends)


def get_backend(name):
    return backends.get(name)
