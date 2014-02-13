# loader.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, escape, g

from config import *
from mongokit import Connection, Document
import requests
from models import *
import re
import json

import time

connection = Connection(MONGODB_HOST, MONGODB_PORT)

connection.register([User])
connection.register([FloodClosure])
connection.register([BBCTravelItem])
connection.register([Route])

flood_match  = re.compile(r'flood', re.I|re.M)

def loader_bbc_all():
	pass

# def loader_bbc_oddities():
# 	collection = connection['ukflood'].BBCTravelItems
# 	for oddity in BBC_ODDITIES:
# 		u = BBC_TRAVEL + oddity + "/unplanned.json"
# 		try:
# 			req = requests.get(u)
# 			j = req.json()
# 		except:
# 			print "Apparently, %s doesn't have any processable data.. "% county
# 			continue
# 		items = 
def loader_bbc_trains():
	collection = connection['ukflood'].BBCTravelItems
	for operator in BBC_TRAIN_OPERATORS:
		u = BBC_TRAVEL + operator + "/unplanned.json"
		try:
			req = requests.get(u)
			j = req.json()
		except:
			print "Apparently, %s doesn't have any trains.. "% county
			continue
		items = j['items']['features']
		for item in items:
			bti = collection.BBCTravelItem()
			bti.latitude = float(item['geometry']['coordinates'][1])
			bti.longitude = float(item['geometry']['coordinates'][0])
			bti.owner = unicode(item['properties']['tpegMessage']['originator']['@originator_name']) + u" - Trains"
			bti.severity = unicode(item['properties']['tpegMessage']['public_transport_information']['@severity_factor'])
			bti.title = unicode(item['properties']['tpegMessage']['title'])
			bti.summary = unicode(item['properties']['tpegMessage']['summary']['$'])
			bti.root_cause = u'Unknown'
			bti.object_blob = unicode(json.dumps(item))
			mgt = item['properties']['tpegMessage']['public_transport_information']['@message_generation_time']
			start_time = item['properties']['tpegMessage']['public_transport_information']['@start_time']
			stop_time = item['properties']['tpegMessage']['public_transport_information']['@stop_time']
			bti.creation_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(mgt,"%Y-%m-%dT%H:%M:%SZ")))
			bti.start_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(start_time,"%Y-%m-%dT%H:%M:%SZ")))
			bti.stop_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(stop_time,"%Y-%m-%dT%H:%M:%SZ")))
			bti.save()
	return jsonify(result="Trains: Done")

def loader_bbc_roads():
	connection.ukflood.drop_collection("BBCTravelItems")
	collection = connection['ukflood'].BBCTravelItems
	for county in BBC_COUNTIES:
		u = BBC_TRAVEL + county + "/roads/unplanned.json"
		try:
			req = requests.get(u)
			j = req.json()
		except:
			print "Apparently, %s doesn't have any roads.. "% county
			continue
		items = j['items']['features']
		for item in items:
			bti = collection.BBCTravelItem()
			bti.latitude = float(item['geometry']['coordinates'][1])
			bti.longitude = float(item['geometry']['coordinates'][0])
			bti.owner = unicode(item['properties']['tpegMessage']['originator']['@originator_name'])
			bti.severity = unicode(item['properties']['tpegMessage']['road_traffic_message']['@severity_factor'])
			bti.title = unicode(item['properties']['tpegMessage']['title'])
			bti.summary = unicode(item['properties']['tpegMessage']['summary']['$'])
			if "obstructions" in item['properties']['tpegMessage']['road_traffic_message']:
				if 'object' in item['properties']['tpegMessage']['road_traffic_message']['obstructions']:
					bti.root_cause  = unicode(item['properties']['tpegMessage']['road_traffic_message']['obstructions']['object']['object_problem']['@object_problem'])
				else:
					bti.root_cause = u'Unknown'
			#elif "vehicles" not in item['properties']['tpegMessage']['road_traffic_message']['accidents']:
			#	bti.root_cause = u"Unknown"
			#elif "accidents" in item['properties']['tpegMessage']['road_traffic_message']:
			#	bti.root_cause  = unicode(item['properties']['tpegMessage']['road_traffic_message']['accidents']['vehicles']['vehicle_problem']['@vehicle_problem'])
			else:
				bti.root_cause = u"Unknown"

			bti.object_blob = unicode(json.dumps(item))	
			mgt = item['properties']['tpegMessage']['road_traffic_message']['@message_generation_time']
			start_time = item['properties']['tpegMessage']['road_traffic_message']['@start_time']
			stop_time = item['properties']['tpegMessage']['road_traffic_message']['@stop_time'] 	
			bti.creation_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(mgt,"%Y-%m-%dT%H:%M:%SZ")))
			bti.start_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(start_time,"%Y-%m-%dT%H:%M:%SZ")))
			bti.stop_time = datetime.datetime.fromtimestamp(time.mktime(time.strptime(stop_time,"%Y-%m-%dT%H:%M:%SZ")))
			if flood_match.search(bti.root_cause.lower()):
				bti.save()
	return jsonify(result="Done")



