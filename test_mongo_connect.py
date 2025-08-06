from pymongo import MongoClient

client = MongoClient("mongodb://admin:adminpass@localhost:27017/?authSource=admin")
db = client["crawlingdb"]
print(db.list_collection_names())