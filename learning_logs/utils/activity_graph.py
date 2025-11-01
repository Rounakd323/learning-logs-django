class ActivityGraph:
    def __init__(self, activities_collection, username):
        self.collection = activities_collection
        self.username = username
    
    def add_activity(self, topic):
        self.collection.update_one(
            {"username": self.username, "topic": topic},
            {"$inc": {"count": 1}},
            upsert=True
        )
    
    def sorted_topics(self):
        return list(self.collection.find({"username": self.username}).sort("count", -1))

    def most_active(self):
        return self.collection.find_one({"username": self.username}, sort=[("count", -1)])

    def least_active(self):
        return self.collection.find_one({"username": self.username}, sort=[("count", 1)])
