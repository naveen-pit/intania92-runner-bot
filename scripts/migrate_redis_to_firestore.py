"""Migration from redis to firestore."""
import os

import path  # noqa: F401
import redis

from constants import FIRESTORE_DATABASE, FIRESTORE_LEADERBOARD_COLLECTION, PROJECT_ID
from google_cloud import Firestore


def move_redis_to_firestore(redis_client: redis.Redis, firestore_client: Firestore, collection_name: str) -> None:
    cursor = 1
    while cursor != 0:
        cursor, keys = redis_client.scan(cursor=cursor, count=100)
        for key in keys:
            key_type = redis_client.type(key).decode("utf-8")
            if key_type == "string":
                value = redis_client.get(key)
                if value is not None:
                    value = value.decode("utf-8")
                firestore_client.set_value(
                    collection=collection_name, document=key.decode("utf-8"), value={"stats": value}
                )


if __name__ == "__main__":
    redis_host = os.environ["LINEBOT_REDIS_HOST"]
    redis_password = os.environ["LINEBOT_REDIS_PASSWORD"]
    redis_port = int(os.environ["LINEBOT_REDIS_PORT"])
    # Set up Redis connection
    redis_client = redis.StrictRedis(host=redis_host, password=redis_password, port=redis_port, db=0)

    firestore_client = Firestore(project=PROJECT_ID, database=FIRESTORE_DATABASE)

    move_redis_to_firestore(
        redis_client, firestore_client=firestore_client, collection_name=FIRESTORE_LEADERBOARD_COLLECTION
    )
