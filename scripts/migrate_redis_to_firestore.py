"""Migration from redis to firestore."""

import redis

from running_bot.config import cfg
from running_bot.google_cloud import Firestore


def move_redis_to_firestore(redis_client: redis.Redis, firestore_client: Firestore, collection_name: str) -> None:
    """Migrate all string key type in redis to firestore database.

    Additional configs are required in .env
    - LINEBOT_REDIS_HOST="your_redis_host"
    - LINEBOT_REDIS_PASSWORD="your_redis_password"
    - LINEBOT_REDIS_PORT=50000
    """
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, count=100)  # type: ignore[misc]
        for key in keys:
            key_type = redis_client.type(key).decode("utf-8")  # type: ignore[union-attr]
            if key_type == "string":
                value = redis_client.get(key)
                if value is not None:
                    value = value.decode("utf-8")  # type: ignore[union-attr]
                firestore_client.set_value(
                    collection=collection_name, document=key.decode("utf-8"), value={"stats": value}
                )
        if cursor == 0:
            break


if __name__ == "__main__":
    redis_host = cfg.redis_host
    redis_password = cfg.redis_password.get_secret_value()
    redis_port = cfg.redis_port
    # Set up Redis connection
    redis_client = redis.StrictRedis(host=redis_host, password=redis_password, port=redis_port, db=0)

    firestore_client = Firestore(project=cfg.project_id, database=cfg.firestore_database)

    move_redis_to_firestore(
        redis_client, firestore_client=firestore_client, collection_name=cfg.firestore_leaderboard_collection
    )
