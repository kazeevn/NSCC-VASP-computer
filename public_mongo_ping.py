from pymongo.mongo_client import MongoClient

uris = (
    r"mongodb+srv://kna-nscc-atomate2.idyxat9.mongodb.net",
    r"mongodb://ac-gpjtjri-shard-00-00.idyxat9.mongodb.net:27017,ac-gpjtjri-shard-00-01.idyxat9.mongodb.net:27017,ac-gpjtjri-shard-00-02.idyxat9.mongodb.net:27017/?replicaSet=atlas-q0vi0g-shard-0&ssl=true"
)

for uri in uris:
    print("Initializing MongoDB client...")
    print(uri)
    client = MongoClient(uri)
    print("Sending a ping to confirm a successful connection...")
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
