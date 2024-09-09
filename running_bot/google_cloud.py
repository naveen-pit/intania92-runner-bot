"""Google Cloud clients for services (BigQuery)."""

import datetime
from datetime import timedelta
from typing import Self

from google.cloud import firestore, secretmanager


class Secret:
    """Google Secret client."""

    def __init__(self: Self) -> None:
        self.client = secretmanager.SecretManagerServiceClient()

    def get_secret(self: Self, name: str) -> str:
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")


class Firestore:
    """Firestore client."""

    def __init__(self: Self, project: str | None, database: str | None) -> None:
        self.client = firestore.Client(project=project, database=database)

    def set_value(
        self: Self, collection: str, document: str, value: dict, expiration_delta: timedelta | None = None
    ) -> None:
        value["created_at"] = firestore.SERVER_TIMESTAMP  # Add create timestamp

        if expiration_delta:
            # Set the 'expired_at' based on `now()` + 'expiration_delta'
            value["expired_at"] = datetime.datetime.now(datetime.UTC) + expiration_delta

        self.client.collection(collection).document(document).set(value)

    def upsert_value(
        self: Self, collection: str, document: str, value: dict, expiration_delta: timedelta | None = None
    ) -> None:
        value["updated_at"] = firestore.SERVER_TIMESTAMP  # Add update timestamp

        if expiration_delta:
            # Set the 'expired_at' based on `now()` + 'expiration_delta'
            value["expired_at"] = datetime.datetime.now(datetime.UTC) + expiration_delta

        self.client.collection(collection).document(document).set(value, merge=True)

    def get_document(self: Self, collection: str, document: str) -> dict | None:
        doc_ref = self.client.collection(collection).document(document)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
