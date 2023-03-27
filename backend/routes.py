from . import app
import os
import json
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get("MONGODB_SERVICE")
mongodb_username = os.environ.get("MONGODB_USERNAME")
mongodb_password = os.environ.get("MONGODB_PASSWORD")
mongodb_port = os.environ.get("MONGODB_PORT")

print(f"The value of MONGODB_SERVICE is: {mongodb_service}")

if mongodb_service == None:
    app.logger.error("Missing MongoDB server in the MONGODB_SERVICE variable")
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)


def parse_json(data):
    return json.loads(json_util.dumps(data))


######################################################################
# RETURN HEALTH OF THE APP
######################################################################
@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200


######################################################################
# COUNT THE NUMBER OF DOCUMENTS IN THE SONGS COLLECTIONS
######################################################################
@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})

    return {"count": count}, 200


######################################################################
# GET ALL SONGS
######################################################################
@app.route("/song", methods=["GET"])
def songs():
    """
    Get all songs in the list
    """
    documents = list(db.songs.find({}))
    print(documents[0])

    return {"songs": parse_json(documents)}, 200


######################################################################
# GET A SONG BY ID
######################################################################
@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """
    Get a song by id
    """
    song = db.songs.find_one({"id": id})
    if not song:
        return {"message": f"song with id {id} not found"}, 404

    return parse_json(song), 200

######################################################################
# CREATE A SONG
######################################################################
@app.route("/song", methods=["POST"])
def create_song():
    """
    Create a new song
    """
    new_song = request.json

    song = db.songs.find_one({"id": new_song["id"]})

    if song:
        return {
            "Message": f"song with id {song['id']} already present"
            }, 302

    insert_id: InsertOneResult = db.songs.insert_one(new_song)

    return {"inserted id": parse_json(insert_id.inserted_id)}, 201

