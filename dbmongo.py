import os

from pymongo import MongoClient  # pip install pymongo
from dotenv import load_dotenv  # pip install python-dotenv

# Load the environment variables
load_dotenv(".env")
MONGO_URI = os.getenv("MONGO_URI")

# Initialize a MongoDB client
client = MongoClient(MONGO_URI)

# This is how to connect to a database
db = client.users_db

# This is how to create a collection
users_collection = db.users

def insert_user(username, name, password):
    """Returns the user on a successful user creation, otherwise raises and error"""
    user = {"username": username, "name": name, "password": password}
    users_collection.insert_one(user)
    return user

def fetch_all_users():
    """Returns a list of all users"""
    return list(users_collection.find({}))

def get_user(username):
    """If not found, the function will return None"""
    return users_collection.find_one({"username": username})

def update_user(username, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    users_collection.update_one({"username": username}, {"$set": updates})

def delete_user(username):
    """Always returns None, even if the key does not exist"""
    users_collection.delete_one({"username": username})
