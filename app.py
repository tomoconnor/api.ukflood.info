from flask import Flask, render_template, request, jsonify, session, redirect, url_for, escape, g
from flask.ext.mobility import Mobility
from flask_oauth import OAuth

from haversine import distance as hdist
from haversine import RADIUS_OF_EARTH
import json
from bson.objectid import ObjectId
import datetime
from config import *
from mongokit import Connection, Document


#import logging
#logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.INFO)
app = Flask(__name__)
Mobility(app)
app.debug= True
app.secret_key = SECRET_KEY

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

class User(Document):
	structure = {
	'screen_name': unicode,
	'oauth_token': unicode,
	'oauth_secret': unicode,
	'creation_date': datetime.datetime,
	'home_lat': float,
	'home_long': float,
	'email': unicode,
	'verified_reports': int
	}
	use_dot_notation = True
	def __repr__(self):
		return "<User %s>" % self.screen_name

connection.register([User])
connection.register([FloodClosure])

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
	return ['devopstom']	
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
	

@app.route("/api/config/radius_of_concern", methods=['POST'])
def api_config_radius():
	new_radius = float(request.form['new_value'])
	if new_radius == 0:
		session['radius_of_concern'] = RADIUS_OF_EARTH
	else:
		session['radius_of_concern'] = new_radius
	return jsonify(radius_of_concern = session['radius_of_concern'])	

@app.route("/")
def index():
        return render_template("layout.html")



if __name__ == '__main__':
        app.run(host='0.0.0.0', port=BIND_PORT)

