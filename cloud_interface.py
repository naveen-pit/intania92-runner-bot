"""Functions to retreive inputs."""
from constants import (
    FIRESTORE_DATABASE,
    FIRESTORE_LEADERBOARD_COLLECTION,
    LINE_ACCESS_TOKEN_KEY,
    LINE_ACCESS_TOKEN_VERSION,
    LINE_CHANNEL_SECRET_KEY,
    LINE_CHANNEL_SECRET_VERSION,
    PROJECT_ID,
)
from google_cloud import Firestore, Secret


def get_line_credentials() -> tuple[str, str]:
    line_channel_secret_name = (
        f"projects/{PROJECT_ID}/secrets/{LINE_CHANNEL_SECRET_KEY}/versions/{LINE_CHANNEL_SECRET_VERSION}"
    )
    line_access_token_name = (
        f"projects/{PROJECT_ID}/secrets/{LINE_ACCESS_TOKEN_KEY}/versions/{LINE_ACCESS_TOKEN_VERSION}"
    )
    secret = Secret()
    line_channel_secret = secret.get_secret(name=line_channel_secret_name)
    line_access_token = secret.get_secret(name=line_access_token_name)
    return line_channel_secret, line_access_token


def get_leaderboard(chat_id: str) -> dict | None:
    firestore_db = Firestore(project=PROJECT_ID, database=FIRESTORE_DATABASE)
    return firestore_db.get_document(collection=FIRESTORE_LEADERBOARD_COLLECTION, document=chat_id)


def set_leaderboard(chat_id: str, value: dict) -> None:
    firestore_db = Firestore(project=PROJECT_ID, database=FIRESTORE_DATABASE)
    firestore_db.set_value(collection=FIRESTORE_LEADERBOARD_COLLECTION, document=chat_id, value=value)