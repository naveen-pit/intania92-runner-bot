"""Functions to retrieve inputs."""

from datetime import timedelta

from .config import cfg
from .google_cloud import Firestore


def get_leaderboard(firestore_client: Firestore, chat_id: str) -> dict | None:
    return firestore_client.get_document(collection=cfg.firestore_leaderboard_collection, document=chat_id)


def set_leaderboard(firestore_client: Firestore, chat_id: str, value: dict) -> None:
    firestore_client.set_value(collection=cfg.firestore_leaderboard_collection, document=chat_id, value=value)


def get_name(firestore_client: Firestore, user_id: str) -> dict | None:
    return firestore_client.get_document(collection=cfg.firestore_user_collection, document=user_id)


def set_name(firestore_client: Firestore, user_id: str, name: str) -> None:
    firestore_client.set_value(collection=cfg.firestore_user_collection, document=user_id, value={"name": name})


def get_image_queue(firestore_client: Firestore, image_set_id: str) -> dict | None:
    return firestore_client.get_document(collection=cfg.firestore_image_set_queue_collection, document=image_set_id)


def upsert_image_queue(firestore_client: Firestore, image_set_id: str, key: str, value: str) -> None:
    firestore_client.upsert_value(
        collection=cfg.firestore_image_set_queue_collection,
        document=image_set_id,
        value={key: value},
        expiration_delta=timedelta(hours=1),
    )
