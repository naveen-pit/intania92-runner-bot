"""Test cloud interface functions."""
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from running_bot.cloud_interface import (
    get_image_queue,
    get_leaderboard,
    get_name,
    set_leaderboard,
    set_name,
    upsert_image_queue,
)


@pytest.fixture()
def firestore_client():
    return MagicMock()


def test_get_leaderboard(firestore_client):
    firestore_client.get_document.return_value = {"user1": 100, "user2": 200}
    chat_id = "test_chat_id"

    result = get_leaderboard(firestore_client, chat_id)

    firestore_client.get_document.assert_called_once_with(collection="leaderboard", document=chat_id)
    assert result == {"user1": 100, "user2": 200}


def test_set_leaderboard(firestore_client):
    chat_id = "test_chat_id"
    value = {"user1": 100, "user2": 200}

    set_leaderboard(firestore_client, chat_id, value)

    firestore_client.set_value.assert_called_once_with(collection="leaderboard", document=chat_id, value=value)


def test_get_name(firestore_client):
    firestore_client.get_document.return_value = {"name": "Alice"}
    user_id = "user_123"

    result = get_name(firestore_client, user_id)

    firestore_client.get_document.assert_called_once_with(collection="users", document=user_id)
    assert result == {"name": "Alice"}


def test_set_name(firestore_client):
    user_id = "user_123"
    name = "Alice"

    set_name(firestore_client, user_id, name)

    firestore_client.set_value.assert_called_once_with(collection="users", document=user_id, value={"name": name})


def test_get_image_queue(firestore_client):
    firestore_client.get_document.return_value = {"image1": "url1", "image2": "url2"}
    image_set_id = "image_set_123"

    result = get_image_queue(firestore_client, image_set_id)

    firestore_client.get_document.assert_called_once_with(collection="image_set_queue", document=image_set_id)
    assert result == {"image1": "url1", "image2": "url2"}


def test_upsert_image_queue(firestore_client):
    image_set_id = "image_set_123"
    key = "image1"
    value = "url1"

    upsert_image_queue(firestore_client, image_set_id, key, value)

    firestore_client.upsert_value.assert_called_once_with(
        collection="image_set_queue", document=image_set_id, value={key: value}, expiration_delta=timedelta(hours=1)
    )
