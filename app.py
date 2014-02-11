from flask import Flask, render_template, request, jsonify, session, redirect, url_for, escape
import json
from bson.objectid import ObjectId
import datetime
from config import *
from mongokit import Connection, Document


#import logging
#logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.INFO)
app = Flask(__name__)
app.debug= True
app.secret_key = SECRET_KEY

connection = Connection(MONGODB_HOST, MONGODB_PORT)


class FloodClosure(Document):
	structure = {
		'owner': unicode,
		'latitude': float,
		'longitude': float,
		'creation_date': datetime.datetime
		}
	use_dot_notation = True
	def __repr__(self):
		return "<FloodClosure (%s,%s)>" % (self.latitude, self.longitude)

connection.register([FloodClosure])


@app.route("/api/marker/new", methods=['POST'])
def api_marker_new():
	if request.method == 'POST':
		latitude = request.form['lat']
		longitude = request.form['long']
		collection = connection['ukflood'].FloodClosures
		fc = collection.FloodClosure()
		fc.owner = u'devopstom'
		fc.latitude = float(latitude)
		fc.longitude = float(longitude)
		fc.creation_date = datetime.datetime.now()
		fc.save()
		return jsonify(message="Flooded Area added")
	else:
		return jsonify(result=0)

@app.route("/api/marker/list")
def api_marker_list():
	collection = connection['ukflood'].FloodClosures
	all_points = list(collection.find())
	for point in all_points:
		if '_id' in point:
			point['_id'] = str(point['_id'])
	return jsonify(pins=all_points)

@app.route("/")
def index():
        return render_template("layout.html")



if __name__ == '__main__':
        app.run(host='0.0.0.0', port=BIND_PORT)

