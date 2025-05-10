from pymongo.mongo_client import MongoClient

print("Initializing MongoDB client...")
client = MongoClient(
    host="asp2a-login-nus02",
    port=27017)
print(client)
print("Sending a ping to confirm a successful connection...")
client.admin.command('ping')
print("Pinged your deployment. You successfully connected to MongoDB!")
