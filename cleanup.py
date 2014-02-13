import re
from haversine import distance as hdist
from haversine import RADIUS_OF_EARTH
import json
from bson.objectid import ObjectId
import datetime
import time
from config import *
from mongokit import Connection, Document

import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
file_handler = TimedRotatingFileHandler(filename="Cleanup.log", when='D', interval=1, utc=True,)
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
class Flag(Document):
	structure = {
		'owner': unicode,
		'flagID': ObjectId,
		'creation_date': datetime.datetime
		}
	use_dot_notation = True
	def __repr__(self):
		return "<Flag %s>" % (self.flagID)


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


		
connection.register([User])
connection.register([Flag])
connection.register([FloodClosure])
connection.register([BBCTravelItem])
def handleFlags():

	closures = connection['ukflood'].FloodClosures
	flags = connection['ukflood'].Flags
        all_flags = list(flags.find())
	print all_flags
	cleaned_up = []
        for flag in all_flags:
		print "Removing " + str(flag['flagID'])
		try:
			closures.remove({'_id': flag['flagID']})
			cleaned_up.append(str(flag['flagID']))
		except:
			continue
	
	connection.ukflood.drop_collection("Flags")
	return cleaned_up
	
if __name__ == '__main__':
       print handleFlags()

