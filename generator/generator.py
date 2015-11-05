import math

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

def _e_dist(x1, y1, x2, y2):
	return math.sqrt((x2-x1)**2 + (y2-y1)**2)

# output: dict of all points in point eps-neighborhood (including point)
def _region_query(m, p, eps):
	neighbors = []
	for point in m:
		if _e_dist(p[0], p[1], point[0], point[1]) <= eps:
			neighbors.append(point)
			
	return neighbors

def _expand_cluster(m, p, neighbors, cluster, eps, min_points):
	# add point p to current cluster
#	p.append(cluster)
	
	for point in neighbors:
		if point[2] == 'NO':
			point[2] = 'YES'
			neighboring_points = _region_query(m, point, eps)
			if len(neighboring_points) >= min_points:
				for part in neighboring_points:
					neighbors.append(part)
					
		if point[3] == 'NONE':
			point[3] = cluster
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
			
# 	for n in m:
# 		print n
		
	o = []
	for n in m:
		tup = (n[0], n[1], n[3])
		o.append(tup)
		
 	o = sorted(set(o))
	print o
	for n in o:
		print n
		
	return m

def test_dbscan():
	m = test_data_parser('dataset1')
	eps = 4
	min_points = 6
	grouped_m = dbscan(m, eps, min_points)
