"""Test google cloud client."""
import datetime
from unittest.mock import MagicMock, patch

from google.cloud import firestore

from running_bot.google_cloud import Firestore, Secret


# Mock the SecretManagerServiceClient from google.cloud
@patch("running_bot.google_cloud.secretmanager.SecretManagerServiceClient")
def test_get_secret(mock_secret_manager):
    mock_client = MagicMock()
    mock_secret_manager.return_value = mock_client
    mock_client.access_secret_version.return_value.payload.data.decode.return_value = "secret_value"

    secret = Secret()
    name = "projects/project_id/secrets/secret_id/versions/latest"

    result = secret.get_secret(name)

    mock_client.access_secret_version.assert_called_once_with(request={"name": name})
    assert result == "secret_value"


# Mock the firestore.Client from google.cloud
@patch("running_bot.google_cloud.firestore.Client")
def test_set_value(mock_firestore_client):
    mock_client = MagicMock()
    mock_firestore_client.return_value = mock_client
    mock_collection = mock_client.collection.return_value
    mock_document = mock_collection.document.return_value

    firestore_client = Firestore(project="test_project", database="test_database")
    collection = "test_collection"
    document = "test_document"
    value = {"key": "value"}

    firestore_client.set_value(collection=collection, document=document, value=value)

    mock_collection.document.assert_called_once_with(document)
    mock_document.set.assert_called_once_with({"key": "value", "created_at": firestore.SERVER_TIMESTAMP})


@patch("running_bot.google_cloud.firestore.Client")
def test_upsert_value(mock_firestore_client):
    mock_client = MagicMock()
    mock_firestore_client.return_value = mock_client
    mock_collection = mock_client.collection.return_value
    mock_document = mock_collection.document.return_value

    firestore_client = Firestore(project="test_project", database="test_database")
    collection = "test_collection"
    document = "test_document"
    value = {"key": "value"}

    firestore_client.upsert_value(collection=collection, document=document, value=value)

    mock_collection.document.assert_called_once_with(document)
    mock_document.set.assert_called_once_with({"key": "value", "updated_at": firestore.SERVER_TIMESTAMP}, merge=True)


@patch("running_bot.google_cloud.firestore.Client")
def test_get_document(mock_firestore_client):
    mock_client = MagicMock()
    mock_firestore_client.return_value = mock_client
    mock_collection = mock_client.collection.return_value
    mock_document = mock_collection.document.return_value
    mock_document.get.return_value.exists = True
    mock_document.get.return_value.to_dict.return_value = {"key": "value"}

    firestore_client = Firestore(project="test_project", database="test_database")
    collection = "test_collection"
    document = "test_document"

    result = firestore_client.get_document(collection=collection, document=document)

    mock_collection.document.assert_called_once_with(document)
    mock_document.get.assert_called_once_with()
    assert result == {"key": "value"}


@patch("running_bot.google_cloud.firestore.Client")
def test_get_document_not_found(mock_firestore_client):
    mock_client = MagicMock()
    mock_firestore_client.return_value = mock_client
    mock_collection = mock_client.collection.return_value
    mock_document = mock_collection.document.return_value
    mock_document.get.return_value.exists = False

    firestore_client = Firestore(project="test_project", database="test_database")
    collection = "test_collection"
    document = "test_document"

    result = firestore_client.get_document(collection=collection, document=document)

    mock_collection.document.assert_called_once_with(document)
    mock_document.get.assert_called_once_with()
    assert result is None


@patch("running_bot.google_cloud.firestore.Client")
def test_set_value_with_expiration_delta(mock_firestore_client):
    mock_doc = MagicMock()
    mock_firestore_client.return_value.collection.return_value.document.return_value = mock_doc

    firestore_client = Firestore(project="project_id", database="database")
    expiration_delta = datetime.timedelta(hours=1)
    value = {"field": "value"}

    firestore_client.set_value(
        collection="test_collection", document="test_document", value=value, expiration_delta=expiration_delta
    )

    # Check if the set method was called with the correct value
    expected_expiration = datetime.datetime.now(datetime.UTC) + expiration_delta
    # Allow for some time difference
    assert "expired_at" in mock_doc.set.call_args[0][0]
    assert mock_doc.set.call_args[0][0]["expired_at"] >= expected_expiration - datetime.timedelta(seconds=10)
    assert mock_doc.set.call_args[0][0]["expired_at"] <= expected_expiration + datetime.timedelta(seconds=10)


@patch("running_bot.google_cloud.firestore.Client")
def test_upsert_value_with_expiration_delta(mock_firestore_client):
    mock_doc = MagicMock()
    mock_firestore_client.return_value.collection.return_value.document.return_value = mock_doc

    firestore_client = Firestore(project="project_id", database="database")
    expiration_delta = datetime.timedelta(hours=1)
    value = {"field": "value"}

    firestore_client.upsert_value(
        collection="test_collection", document="test_document", value=value, expiration_delta=expiration_delta
    )

    # Check if the upsert method was called with the correct value
    expected_expiration = datetime.datetime.now(datetime.UTC) + expiration_delta
    # Allow for some time difference
    assert "expired_at" in mock_doc.set.call_args[0][0]
    assert mock_doc.set.call_args[0][0]["expired_at"] >= expected_expiration - datetime.timedelta(seconds=10)
    assert mock_doc.set.call_args[0][0]["expired_at"] <= expected_expiration + datetime.timedelta(seconds=10)
