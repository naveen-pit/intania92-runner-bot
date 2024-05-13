"""Google Cloud clients for services (BigQuery)."""

from typing import Self

from google.cloud import secretmanager


class Secret:
    """Google Secret client."""

    def __init__(self: Self) -> None:
        self.client = secretmanager.SecretManagerServiceClient()

    def get_secret(self: Self, name: str) -> str:
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
