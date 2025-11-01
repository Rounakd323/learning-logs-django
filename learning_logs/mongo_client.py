from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Choose your database
db = client["learning_log"]

# Example collection
collection = db["test_collection"]
topics_collection = db["topics"]
entries_collection = db["entries"]
from pymongo import MongoClient

users_collection = db["users"]
topics_collection = db["topics"]
entries_collection = db["entries"]

activities_collection = db["activities"]