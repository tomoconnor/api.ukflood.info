from mongokit import Connection, Document
from bson.objectid import ObjectId

import datetime

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

class BBCTravelItem(Document):
	structure = {
		'latitude': float,
		'longitude': float,
		'owner': unicode,
		'severity': unicode,
		'title': unicode,
		'summary': unicode,
		'root_cause': unicode,
		'object_blob': unicode,
		'creation_time': datetime.datetime,
		'import_time': datetime.datetime,
		'start_time': datetime.datetime,
		'stop_time': datetime.datetime
		}
	use_dot_notation = True
	def __repr__(self):
		return "<BBCTravelItem (%s,%s)" % (self.latitude, self.longitude)

class Route(Document):
	structure = {
		'start_latitude': float,
		'start_longitude': float,
		'end_latitude': float,
		'end_longitude': float,
		'parent': ObjectId,
		'owner': unicode,
		'title': unicode,
		'summary': unicode,
		'root_cause': unicode,
		'object_blob': unicode,
		'creation_time': datetime.datetime,
		'import_time': datetime.datetime,
		'start_time': datetime.datetime,
		'stop_time': datetime.datetime
		}
	use_dot_notation = True
	def __repr__(self):
		return "<Route from (%s,%s) to (%s,%s)" % (self.start_latitude, self.start_longitude, self.end_latitude,self.end_longitude)

class Flag(Document):
	structure = {
		'owner': unicode,
		'flagID': ObjectId,
		'creation_date': datetime.datetime
		}
	use_dot_notation = True
	def __repr__(self):
		return "<Flag %s>" % (self.flagID)

