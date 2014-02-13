from flask import Flask, render_template, request, jsonify, session, redirect, url_for, escape, g
import re
from flask.ext.mobility import Mobility
from flask_oauth import OAuth

from haversine import distance as hdist
from haversine import RADIUS_OF_EARTH
import json
from bson.objectid import ObjectId
import datetime
import time
from config import *
from models import *
from loader import *

from mongokit import Connection, Document

import requests

app = Flask(__name__)
Mobility(app)

app.debug=False
app.debug=True

import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
if app.debug:
	file_handler = TimedRotatingFileHandler(filename=DEV_LOGFILE, when='D', interval=1, utc=True,)
else:
	file_handler = TimedRotatingFileHandler(filename=PRODUCTION_LOGFILE, when='D', interval=1, utc=True,)
file_handler.setFormatter(Formatter('''
	Message type:       %(levelname)s
	Location:           %(pathname)s:%(lineno)d
	Module:             %(module)s
	Function:           %(funcName)s
	Time:               %(asctime)s
	
	Message:
	
	%(message)s
	'''))

file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)

app.secret_key = SECRET_KEY
flood_match  = re.compile(r'flood', re.I|re.M)
connection = Connection(MONGODB_HOST, MONGODB_PORT)

oauth = OAuth()

twitter = oauth.remote_app(
	'twitter',
	base_url='https://api.twitter.com/1/',
	request_token_url='https://api.twitter.com/oauth/request_token',
	access_token_url='https://api.twitter.com/oauth/access_token',
	authorize_url='https://api.twitter.com/oauth/authenticate',
	consumer_key=CONSUMER_KEY,
	consumer_secret=CONSUMER_SECRET
)
def flash(message):
	print "FLASH ", message


		
connection.register([User])
connection.register([FloodClosure])
connection.register([BBCTravelItem])
connection.register([Route])

@app.context_processor
def inject_values():
		return dict(
		active_users = get_active_users(),
		radius_of_concern = 50
		)


@twitter.tokengetter
def get_twitter_token(token=None):
	collection = connection['ukflood'].Users
	u = collection.find_one({'oauth_token':token})
	if u is None:
		return None
	else:
		return u['oauth_token'], u['oauth_secret']
#	user = g.user
#	if user is not None:
#		return user['oauth_token'], user['oauth_secret']

@app.before_request
def before_request():
	#g.user = None
	if "user_id" in session:
		collection = connection['ukflood'].Users
		g.user = collection.find_one({'screen_name':session['user_id']})

@app.route("/login")
def login():
	return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route("/logout")
def logout():
	session.pop('user_id',None)
	flash("You were signed out")
	return redirect(url_for('index'))

@app.route("/oauth-authorized")
@twitter.authorized_handler
def oauth_authorized(resp):
	next_url = request.args.get('next') or url_for('index')
	if resp is None:
		flash(u'You denied the request to sign in.')
		return redirect(next_url)
	collection = connection['ukflood'].Users
	u = collection.User()
	session['twitter_token'] = (
		resp['oauth_token'],
		resp['oauth_token_secret']
	)
	session['user_id'] = resp['screen_name']
	if collection.find_one({'screen_name':resp['screen_name']}):
		flash('%s has signed in' % resp['screen_name'].capitalize())
		return redirect(next_url)
	else:
		u.screen_name = resp['screen_name']
		u.oauth_token = resp['oauth_token']
		u.oauth_secret = resp['oauth_token_secret']
		u.creation_date = datetime.datetime.now()
		u.verified_reports = 0
		u.save()
		flash('%s has signed in' % resp['screen_name'].capitalize())
		return redirect(next_url)

def get_active_users():
	collection = connection['ukflood'].Users
	u = collection.find(fields={'screen_name':True})
	return list(u)
@app.route("/api/marker/new", methods=['POST'])
def api_marker_new():
	if request.method == 'POST':
		latitude = request.form['lat']
		longitude = request.form['long']
		collection = connection['ukflood'].FloodClosures
		fc = collection.FloodClosure()
		if 'user_id' in session:
			fc.owner = session['user_id']
		else:
			fc.owner = u"Anonymous"
		fc.latitude = float(latitude)
		fc.longitude = float(longitude)
		fc.creation_date = datetime.datetime.now()
		fc.save()
		marker = fc
		marker['_id'] = str(marker['_id'])
		return jsonify(message="Flooded Area added", new_id=str(fc._id), marker=marker)
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

@app.route("/api/marker/radius")
def api_marker_radius():
	radius = float(request.args.get('radius'))
	my_latitude = float(request.args.get('my_latitude'))
	my_longitude = float(request.args.get('my_longitude'))
	
	collection = connection['ukflood'].FloodClosures
	all_points = list(collection.find())
	relevant_points = []
	for point in all_points:
		if '_id' in point:
			point['_id'] = str(point['_id'])
		distance_from_user = hdist((point['latitude'], point['longitude']), (my_latitude, my_longitude))
		if distance_from_user <= radius:
			relevant_points.append(point)	
	return jsonify(pins=relevant_points)	
	
@app.route("/api/bbc/radius")
def api_bbc_radius():
	radius = float(request.args.get('radius'))
	my_latitude = float(request.args.get('my_latitude'))
	my_longitude = float(request.args.get('my_longitude'))
	
	collection = connection['ukflood'].BBCTravelItems
	all_points = list(collection.find())
	relevant_points = []
	for point in all_points:
		if '_id' in point:
			point['_id'] = str(point['_id'])
		distance_from_user = hdist((point['latitude'], point['longitude']), (my_latitude, my_longitude))
		if distance_from_user <= radius:
			relevant_points.append(point)	
	return jsonify(pins=relevant_points)	
	

@app.route("/api/config/radius_of_concern", methods=['POST'])
def api_config_radius():
	new_radius = float(request.form['new_value'])
	if new_radius == 0:
		session['radius_of_concern'] = RADIUS_OF_EARTH
	else:
		session['radius_of_concern'] = new_radius
	return jsonify(radius_of_concern = session['radius_of_concern'])	

@app.route("/api/marker/user")
def api_marker_user():
	if 'user_id' not in session:
		return jsonify(pins=[])
	else:
		username = session['user_id']
		collection = connection['ukflood'].FloodClosures
		all_my_points = list(collection.find({'owner':username}))
		for point in all_my_points:
			if '_id' in point:
				point['_id'] = str(point['_id'])
		return jsonify(pins=all_my_points)

@app.route("/api/marker/delete", methods=['POST'])
def delete_marker():
	if request.method == "POST":
		id_to_delete = request.form['this_id']
		requesting_user = request.form['requested_by']
		if session['user_id'] == requesting_user:
			collection = connection['ukflood'].FloodClosures
			obj_id = ObjectId(id_to_delete)
			try:
				collection.remove({'_id':obj_id})
				msg = requesting_user.title() + " deleted item with id " + id_to_delete
			except Exception, e:
				msg = "Object could not be deleted. " + e.message
			return jsonify(message=msg)
		else:
			msg = "You can only delete your own pins"
			return jsonify(message=msg), 403




@app.route("/")
def index():
        return render_template("layout.html")

@app.route("/bbc")
def bbc_view():
        return render_template("bbc.html")

@app.route("/cleanup")
def cleanup_view():
	return render_template("cleanup.html")

@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

@app.errorhandler(500)
def ISR(e):
	return render_template("500.html"),500

@app.route("/api/bbc/roads/load")
def api_bbc_roads_load():
	return loader_bbc_roads()

@app.route("/api/bbc/trains/load")
def api_bbc_trains_load():
	return loader_bbc_trains()
		
if __name__ == '__main__':
        app.run(host=BIND_HOST, port=BIND_PORT)

