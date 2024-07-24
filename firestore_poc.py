from google.cloud import firestore


# Add a new document
db = firestore.Client(project="api-project-705977966204", database="intania92-runner-leaderboard-dev")
# doc_ref = db.collection(u'leaderboard').document(u'blovelace')
# doc_ref.set({
#     u'first': u'Ada',
#     u'last': u'Lovelace',
#     u'born': 1815
# })

# # Then query for documents
# users_ref = db.collection(u'leaderboard')

# for doc in users_ref.stream():
#     print(u'{} => {}'.format(doc.id, doc.to_dict()))

doc_ref = db.collection("leaderboard").document("blovelace")

doc = doc_ref.get()
if doc.exists:
    print(f"Document data: {doc.to_dict()}")
else:
    print("No such document!")
