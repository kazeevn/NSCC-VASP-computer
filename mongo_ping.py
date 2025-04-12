from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

#password = "wLAPjXSfUlTTdvP7"
#uri = "mongodb://kna:wLAPjXSfUlTTdvP7@localhost/?appName=KNA-NSCC-atomate2"
#uri = f"mongodb://kna:{password}@ac-gpjtjri-shard-00-00.idyxat9.mongodb.net:27017,ac-gpjtjri-shard-00-01.idyxat9.mongodb.net:27017,ac-gpjtjri-shard-00-02.idyxat9.mongodb.net:27017/?replicaSet=atlas-q0vi0g-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority&appName=KNA-NSCC-atomate2"
#uri = f"mongodb://kna:{password}@localhost:27018,localhost:27019,localhost:27020/?replicaSet=atlas-q0vi0g-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority&appName=KNA-NSCC-atomate2"
#uri = "mongodb+srv://kna:wLAPjXSfUlTTdvP7@kna-nscc-atomate2.idyxat9.mongodb.net/?appName=KNA-NSCC-atomate2"
#uri = r"mongodb://nscc-atomate2-kna-db-user:izUdNsZhU0lrYdTJHk9e80sGS@asp2a-login-nus02:17017/nscc-atomate2-kna-db?directConnection=true&serverSelectionTimeoutMS=10000"

uri = rf"mongodb://nscc-atomate2-kna-db-user:izUdNsZhU0lrYdTJHk9e80sGS@localhost:{os.getenv("JOBFLOW_JOB_STORE__DOCS_STORE__PORT")}/nscc-atomate2-kna-db?directConnection=true&serverSelectionTimeoutMS=5000"

print("Initializing MongoDB client...")
client = MongoClient(uri, server_api=ServerApi('1'))

print("Sending a ping to confirm a successful connection...")
client.admin.command('ping')
print("Pinged your deployment. You successfully connected to MongoDB!")