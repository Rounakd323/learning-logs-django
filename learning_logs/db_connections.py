import pymongo

# Connection URL
MONGO_URI = "mongodb://localhost:27017/"

# Database name
DB_NAME = "learning_log"

# Create client and DB connection
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
