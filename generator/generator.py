from math import radians, sin, cos, asin, sqrt, pow, atan2, degrees
from myattributes import *
import xml.etree.ElementTree as ET

EARTH_RADIUS = 6378100.
EPSILON = 0.00002

FEET_TO_METERS = 0.3048
METERS_TO_FEET = 3.28084


# helper function that returns great circle distance between two
# points on the earth (input must be in decimal degrees)
def _haversine(lat_1, long_1, lat_2, long_2):
	
	# convert decimal degrees to radians 
	lat_1 = radians(lat_1)
	long_1 = radians(long_1)
	lat_2 = radians(lat_2)
	long_2 = radians(long_2)

	# haversine formula 
	d_long = long_2 - long_1 
	d_lat = lat_2 - lat_1 
	a = sin(d_lat/2)**2 + cos(lat_1) * cos(lat_2) * sin(d_long/2)**2
	c = 2 * asin(sqrt(a))  
	
	m = EARTH_RADIUS * c
	return m 

# function for parsing DBSCAN Test Data Generator
# http://people.cs.nctu.edu.tw/~rsliang/dbscan/testdatagen.html
def test_data_parser(file_name):

	# extension of input file, txt
	input_name = file_name + ".txt"

	# open file
	file = open(input_name, 'r')
	# empty list of rows
	rows = []
		
	for line in file:
		# empty row of attributes
		row = []
		
		current_row = line.split(' ')
		
		lat = current_row[1]
		lat = float(lat.replace('\n', ''))
		row.append(lat)
		lon = current_row[2]
		lon = float(lon.replace('\n', ''))
		row.append(lon)
		visited = 'NO'
		row.append(visited)
		cluster = 'NONE'
		row.append(cluster)

		rows.append(row)
		
	file.close()
	
	return rows   

def test_contact_parser(contact_list):
	rows = []
		
	for line in contact_list:
		# empty row of attributes
		row = []
		
				
		lat = float(line[2])
		row.append(lat)
		lon = float(line[3])
		row.append(lon)
		visited = 'NO'
		row.append(visited)
		cluster = 'NONE'
		row.append(cluster)

		rows.append(row)
	
	return rows   

def _e_dist(x1, y1, x2, y2):
	return sqrt((x2-x1)**2 + (y2-y1)**2)

# output: dict of all points in point eps-neighborhood (including point)
def _region_query(m, p, eps):
# 	min_dist = 10
	neighbors = []
	for point in m:
		distance = _haversine(p[0], p[1], point[0], point[1])
		if distance <= eps:# and distance > min_dist:
#		if _e_dist(p[0], p[1], point[0], point[1]) <= eps:
			neighbors.append(point)
			
	return neighbors

def _expand_cluster(m, p, neighbors, cluster, eps, min_points):
	
	for point in neighbors:
		if point[2] == 'NO':
			point[2] = 'YES'
			neighboring_points = _region_query(m, point, eps)
			if len(neighboring_points) >= min_points:
				for part in neighboring_points:
					neighbors.append(part)
					
		if point[3] == 'NONE':
			point[3] = cluster
			
def convex_hull(points):
	"""Computes the convex hull of a set of 2D points.

	Input: an iterable sequence of (x, y) pairs representing the points.
	Output: a list of vertices of the convex hull in counter-clockwise order,
	  starting from the vertex with the lexicographically smallest coordinates.
	Implements Andrew's monotone chain algorithm. O(n log n) complexity.
	"""

	# Sort the points lexicographically (tuples are compared lexicographically).
	# Remove duplicates to detect the case we have just one unique point.
	points = sorted(set(points))

	# Boring case: no points or a single point, possibly repeated multiple times.
	if len(points) <= 1:
		return points

	# 2D cross product of OA and OB vectors, i.e. z-component of their 3D cross product.
	# Returns a positive value, if OAB makes a counter-clockwise turn,
	# negative for clockwise turn, and zero if the points are collinear.
	def cross(o, a, b):
		return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

	# Build lower hull 
	lower = []
	for p in points:
		while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
			lower.pop()
		lower.append(p)

	# Build upper hull
	upper = []
	for p in reversed(points):
		while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
			upper.pop()
		upper.append(p)

	# Concatenation of the lower and upper hulls gives the convex hull.
	# Last point of each list is omitted because it is repeated at the beginning of the other list. 
	return lower[:-1] + upper[:-1]

# function for parsing contact XML file
def contact_parser(input_name):  
	# list to hold targets
	contacts = []
	
	message = ET.ElementTree(file = input_name)
	
	for tContact in message.iter(tag = XML_contact):
		# list to hold contact attributes
		contact = []
		
		for attribute in tContact.iter():
			
			if attribute.tag == XML_contact:
				# add ID to contact attribute list
				contact.append(str(attribute.attrib[XML_contact_id]))
				
			if attribute.tag == XML_contact_crn:
				# add CRN to contact attribute list
				contact.append(attribute.text)
				
			if attribute.tag == XML_contact_lat:
				#TODO: Add attribute units check
				contact.append(float(attribute.text))

			if attribute.tag == XML_contact_lon:
				#TODO: Add attribute units check
				contact.append(float(attribute.text))
#				print attribute.attrib['units']
				
			if attribute.tag == XML_contact_kind:
				contact.append(attribute.text)

			if attribute.tag == XML_contact_depth:
				if attribute.attrib[XML_contact_depth_units] == 'ft':
					depth = float(attribute.text) * FEET_TO_METERS
					contact.append(depth)
					
				# otherwise assume case depth is in meters
				else:
					contact.append(float(attribute.text))
		
		contacts.append(contact)		
	
	return contacts

"""
Groups like points together into clusters

Input:          m = dict containing (lat, lon, visted, cluster)
	          eps = distance in meters
	   min_points = minimum points related to form cluster
	   
Output: updated dict with cluster membership

Python implementation of DBSCAN algorithm described in 
en.wikipedia.org/wiki/DBSCAN
"""
def dbscan(m, eps, min_points):
	cluster_id = 0
	
	for point in m:
		# has this point been seen before
		if point[2] == 'YES':
			continue

		# mark point as seen
		point[2] = 'YES'
		
		# check for neighboring points
		neighboring_points = _region_query(m, point, eps)
		if len(neighboring_points) < min_points:
			point[3] = 0
			
		else:
			cluster_id = cluster_id + 1
			_expand_cluster(m, point, neighboring_points, cluster_id, eps, min_points)
			
#  	for n in m:
#  		print n
		
	o = []
	for n in m:
		tup = (n[0], n[1], n[3])
		o.append(tup)
# 		
# 	o = sorted(set(o))
# 
	count = cluster_id
	print len(o)
# 	for n in o:
# 		print n
# 	
	
	while count > 0:
#		print 'here'
		cluster = []
		for n in o:
			if n[2] == 0:
				continue
			if n[2] == count:
				tup = (n[0], n[1])
				cluster.append(tup)
# 		print cluster
# 		print count, len(cluster)
		cluster = convex_hull(cluster)
		print cluster
		print count, len(cluster)

		count = count - 1
		
		
	return m

def test_dbscan():
	m = contact_parser('CONTACTS.XML')
# 	for n in m:
# 		print n
	m = test_contact_parser(m)
#	o = test_data_parser('dataset1')
	eps = 300
	min_points = 3
	grouped_m = dbscan(m, eps, min_points)
