# from .aws import AmazonCloud
# from .google import GoogleCloud
from .docker import DockerClient

# backends = {"google": GoogleCloud, "aws": AmazonCloud, "docker": DockerClient}
backends = {"docker": DockerClient}
backend_names = list(backends)


def get_backend(name):
    return backends.get(name)
