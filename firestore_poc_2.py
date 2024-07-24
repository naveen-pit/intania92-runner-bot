import firebase_admin
from firebase_admin import firestore

# Application Default credentials are automatically created.
app = firebase_admin.initialize_app()
# name="intania92-runner-leaderboard-dev"
# db = firestore.client()
db = firestore.Client(database="intania92-runner-leaderboard-dev")

doc_ref = db.collection("users").document("alovelace")
doc_ref.set({"first": "Ada", "last": "Lovelace", "born": 1815})
