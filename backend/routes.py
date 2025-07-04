from . import app
import os
import json
import pymongo
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
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
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
# INSERT CODE HERE
######################################################################
@app.route('/health')
def health():
    """
    Health check endpoint
    """
    return jsonify(status="OK"), 200

@app.route('/count')
def count():
    """
    Returns songs list length
    """
    return jsonify(count=len(songs_list))

@app.route('/song')
def get_songs():
    """
    Returns documents in songs collection
    """
    songs_in_collection = json.loads(json_util.dumps(list(db.songs.find({}))))

    if songs_in_collection:
        return jsonify(songs=songs_in_collection), 200
    
    return jsonify(message="Empty collection"), 400


@app.route('/song/<int:song_id>')
def get_song_by_id(song_id):
    """
    Returns one song in songs collection
    """
    res = db.songs.find_one({"id": song_id})
    song = parse_json(res)

    if song:
        return song, 200
    
    return jsonify(message=f"Song {song_id} not found"), 404

@app.route('/song', methods = ['POST'])
def create_song():
    """
    Adds a new song
    """
    new_song = parse_json(request.get_json())
    if new_song:
        found_res = parse_json(db.songs.find({"id": new_song["id"]}))
        if found_res:
            return jsonify(Message=f"song with id {new_song['id']} already present"), 302

        res = db.songs.insert_one(new_song)
        return {"inserted id": parse_json(res.inserted_id) }, 201
    
    return jsonify(Message="Uknown error"), 400

@app.route('/song/<int:song_id>', methods = ['PUT'])
def update_song(song_id):
    """
    Updates existing song
    """
    new_song = parse_json(request.get_json())
    print(new_song)
    if new_song:
        found_res = parse_json(db.songs.find_one({"id": song_id}))
        if found_res:
            res = db.songs.update_one({"id": song_id}, {'$set': new_song})
            # if nothing changed notify
            if res.modified_count == 0:
                return jsonify(message = "song found, but nothing updated"), 200

            return parse_json(db.songs.find_one(res.upserted_id)), 201

        return jsonify(message="song not found"), 404
    
    return jsonify(Message="Uknown error"), 400

@app.route('/song/<int:song_id>', methods = ['DELETE'])
def delete_song(song_id):
    """
    Deletes song with song_id
    """
    found_res = parse_json(db.songs.find_one({"id": song_id}))
    if not found_res:
        return jsonify(message = "song not found"), 404
    result = db.songs.delete_one({"id": song_id})
    if result.deleted_count:
        return {}, 204
    
    return jsonify(Message="nothing to delete"), 400