from .aws import AmazonCloud
from .docker import DockerClient
from .google import GoogleCloud

# backends = {"aws": AmazonCloud}
backends = {
    "docker": DockerClient,
    "google": GoogleCloud,
    "gcp": GoogleCloud,
    "aws": AmazonCloud,
}
backend_names = list(backends)


def get_backend(name):
    return backends.get(name)
