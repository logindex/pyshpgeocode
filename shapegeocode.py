
import shapefile, sys


class geocoder:

	def __init__(self, shp_src, filter=None):
		"""
		create a new geocode using the specified shapefile
		"""
		self.shp_src = shp_src
		self._init_polygons(filter)

	def _init_polygons(self, filter=None):
		sf = shapefile.Reader(self.shp_src)
		recs = sf.records()
		self.polygons = []
		self.bboxes = []
		self.records = []
		for i in range(len(recs)):
			rec = recs[i]
			if filter and filter(rec) == False: continue
			shp = sf.shapeRecord(i).shape
			poly,bbox = _shape_to_polygon(shp)
			self.records.append(rec)
			self.polygons.append(poly)
			self.bboxes.append(bbox)


	def geocode(self, lat, lon, filter=None, max_dist=0.0):
		"""
		return shape record for latlon position
		"""
		
		for i in range(len(self.polygons)):
			rec = self.records[i]
			if filter and filter(rec) is False: continue
			bbox = self.bboxes[i]
			if _point_in_bbox(bbox, (lon, lat)):
				poly = self.polygons[i]
				for j in range(len(poly)):
					contour = poly[j]
					if _point_in_polygon(contour, (lon,lat)):
						return rec
		
		# no matching polygon found so far
		# so let's find the nearest polygon
		if max_dist > 0:	
			global_min_dist = sys.maxint
			globel_nearest_ll = None
			nearest_poly = -1
			
			for i in range(len(self.polygons)):
				min_dist = 9999999999999
				nearest_ll = None
				rec = self.records[i]
				if filter and filter(rec) is False: continue
				bbox = self.bboxes[i]
				if _point_in_bbox(_inflate_bbox(bbox, 1.2), (lon,lat)):
					poly = self.polygons[i]
					for j in range(len(poly)):
						contour = poly[i]
						for x,y in contour:
							dx = x - lon
							dy = y - lat
							dist = dx*dx + dy*dy
							if dist < min_dist:
								min_dist = dist
								nearest_ll = (x,y)
				if min_dist < global_min_dist:
					global_min_dist = min_dist
					nearest_poly = i
						
			if global_min_dist < max_dist:
				return self.records[nearest_poly]
		return None
		
		


def _shape_to_polygon(shp):
	parts = shp.parts
	parts.append(len(shp.points))
	poly = []
	xrange = (sys.maxint, sys.maxint*-1)
	yrange = (sys.maxint, sys.maxint*-1)
	for j in range(len(parts)-1):
		pts = []
		for k in range(parts[j], parts[j+1]):
			pt = shp.points[k]
			xrange = (min(xrange[0],pt[0]), max(xrange[1], pt[0]))
			yrange = (min(yrange[0],pt[1]), max(yrange[1], pt[1]))
			pts.append(pt)
		poly.append(pts)
	bbox = (xrange[0],yrange[0],xrange[1],yrange[1])
	return (poly, bbox)


def _point_in_bbox(bbox, p):
	return p[0] >= bbox[0] and p[0] <= bbox[2] and p[1] >= bbox[1] and p[1] <= bbox[3]


def _point_in_polygon(polygon, p):
	from math import atan2,pi
	twopi = pi*2
	n = len(polygon)
	angle = 0
	for i in range(n):
		x1,y1 = (polygon[i][0] - p[0], polygon[i][1] - p[1])
		x2,y2 = (polygon[(i+1)%n][0] - p[0], polygon[(i+1)%n][1] - p[1])
		theta1 = atan2(y1,x1)
		theta2 = atan2(y2,x2)
		self.atan2cnt += 2
		dtheta = theta2 - theta1
		while dtheta > pi:
			dtheta -= twopi
		while dtheta < -pi:
			dtheta += twopi
		angle += dtheta
	return abs(angle) >= pi

	
def _inflate_bbox(bbox, ratio):
	w = bbox[2]-bbox[0]
	h = bbox[3]-bbox[1]
	p = max(w,h) * (ratio-1.0)
	return (bbox[0]-p,bbox[1]-p,bbox[2]+p,bbox[3]+p)