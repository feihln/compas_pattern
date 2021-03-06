from math import floor
from operator import itemgetter

from compas_pattern.datastructures.mesh.mesh import Mesh
from compas_pattern.datastructures.network.network import Network

from compas_pattern.datastructures.network.coloring import is_network_two_colorable

from compas.geometry import centroid_points

from compas.utilities import pairwise
from compas.utilities import geometric_key
from compas_pattern.utilities.lists import list_split

__author__     = ['Robin Oval']
__copyright__  = 'Copyright 2018, Block Research Group - ETH Zurich'
__license__    = 'MIT License'
__email__      = 'oval@arch.ethz.ch'

__all__ = [
	'QuadMesh',
]

class QuadMesh(Mesh):

	def __init__(self):
		super(QuadMesh, self).__init__()
		self.strip = {}

	def not_none_edges(self):
		"""Returns the edges oriented inwards.

		Parameters
		----------

		Returns
		-------
		(w, x) : tuple
			The opposite edge.

		"""

		return [(u, v) if v in self.halfedge[u] and self.halfedge[u][v] is not None else (v, u) for u, v in self.edges()]


	def face_opposite_edge(self, u, v):
		"""Returns the opposite edge in the quad face.

		Parameters
		----------
		u : int
			The identifier of the edge start.
		v : int
			The identifier of the edge end.

		Returns
		-------
		(w, x) : tuple
			The opposite edge.

		"""

		fkey = self.halfedge[u][v]
		w = self.face_vertex_descendant(fkey, v)
		x = self.face_vertex_descendant(fkey, w)

		return (w, x)

	def vertex_opposite_vertex(self, u, v):
		"""Returns the opposite vertex to u accross vertex v.

		Parameters
		----------
		u : hashable
			A vertex key.
		v : hashable
			A vertex key.

		Returns
		-------
		hashable, None
			The opposite vertex.
			None if v is a singularity or if (u, v) leads outwards.

		"""

		if self.is_vertex_singular(v):
			return None

		elif self.is_vertex_on_boundary(v):
			
			if not self.is_vertex_on_boundary(u):
				return None
			
			else:
				return [nbr for nbr in self.vertex_neighbors(v) if nbr != u and self.is_vertex_on_boundary(nbr)][0]
		
		else:
			nbrs = self.vertex_neighbors(v, ordered = True)
			return nbrs[nbrs.index(u) - 2]
		
	# --------------------------------------------------------------------------
	# singularities
	# --------------------------------------------------------------------------

	def singularities(self):
		"""Returns all the singularity indices in the quad mesh.

		Returns
		-------
		list
			The list of vertex indices that are quad mesh singularities.

		"""
		return [vkey for vkey in self.vertices() if self.is_vertex_singular(vkey)]

	def is_vertex_singular(self, vkey):
		"""Output whether a vertex is quad mesh singularity.

		Parameters
		----------
		vkey : int
			The vertex key.

		Returns
		-------
		bool
			True if the vertex is a quad mesh singularity. False otherwise.

		"""

		if (self.is_vertex_on_boundary(vkey) and self.vertex_degree(vkey) != 3) or (not self.is_vertex_on_boundary(vkey) and self.vertex_degree(vkey) != 4):
			return True

		else:
			return False

	def vertex_index(self, vkey):
		"""Compute vertex index.

		Parameters
		----------
		vkey : int
			The vertex key.

		Returns
		-------
		int
			Vertex index.

		"""

		if self.vertex_degree(vkey) == 0:
			return 0

		regular_valency = 4 if not self.is_vertex_on_boundary(vkey) else 3

		return (regular_valency - self.vertex_degree(vkey)) / 4


	def polyedge(self, u0, v0):
		"""Returns all the edges in the polyedge of the input edge.

		Parameters
		----------
		u : int
			The identifier of the edge start.
		v : int
			The identifier of the edge end.

		Returns
		-------
		polyedge : list
			The list of the vertices in polyedge.
		"""


		polyedge = [u0, v0]

		while len(polyedge) <= self.number_of_vertices():

			# end if closed loop
			if polyedge[0] == polyedge[-1]:
				break

			# get next vertex accros four-valent vertex
			w = self.vertex_opposite_vertex(*polyedge[-2 :])

			# flip if end of first extremity
			if w is None:
				polyedge = list(reversed(polyedge))
				# stop if end of second extremity
				w = self.vertex_opposite_vertex(*polyedge[-2 :])
				if w is None:
					break

			# add next vertex
			polyedge.append(w)

		return polyedge

	def polyedges(self):
		"""Collect the polyedges accross four-valent vertices between boundaries and/or singularities.

		Parameters
		----------

		Returns
		-------
		polyedges : list
			List of quad polyedges as list of vertices.

		"""

		polyedges = []

		edges = list(self.edges())

		while len(edges) > 0:

			# collect new polyedge
			u0, v0 = edges.pop()
			polyedges.append(self.polyedge(u0, v0))

			# remove collected edges
			for u, v in pairwise(polyedges[-1]):
				if (u, v) in edges:
					edges.remove((u, v))
				elif (v, u) in edges:
					edges.remove((v, u))

		return polyedges

	def polylines(self):
		"""Return the polylines of the quad mesh.

		Returns
		-------
		list
			The polylines.

		"""

		return [[self.vertex_coordinates(vkey) for vkey in polyedge] for polyedge in self.polyedges()]

	def singularity_polyedges(self):
		"""Collect the polyedges connected to singularities.

		Returns
		-------
		list
			The polyedges connected to singularities.

		"""

		# keep only polyedges connected to singularities or along the boundary		
		polyedges = [polyedge for polyedge in self.polyedges() if self.is_vertex_singular(polyedge[0]) or self.is_vertex_singular(polyedge[-1]) or self.is_edge_on_boundary(polyedge[0], polyedge[1])]									

		# get intersections between polyedges for split
		vertices = [vkey for polyedge in polyedges for vkey in set(polyedge)]
		split_vertices = [vkey for vkey in self.vertices() if vertices.count(vkey) > 1]
		
		# split singularity polyedges
		return [split_polyedge for polyedge in polyedges for split_polyedge in list_split(polyedge, [polyedge.index(vkey) for vkey in split_vertices if vkey in polyedge])]

	def singularity_polylines(self):
		"""Return the polylines connected to singularities.

		Returns
		-------
		list
			The polylines connected to singularities.

		"""
		return [[self.vertex_coordinates(vkey) for vkey in polyedge] for polyedge in self.singularity_polyedges()]

	def singularity_polyedge_decomposition(self):
		"""Returns a quad patch decomposition of the mesh based on the singularity polyedges, including boundaries and additionnal splits on the boundaries.

		Returns
		-------
		list
			The polyedges forming the decomposition.

		"""
		polyedges = [polyedge for polyedge in self.polyedges() if (self.is_vertex_singular(polyedge[0]) or self.is_vertex_singular(polyedge[-1])) and not self.is_edge_on_boundary(polyedge[0], polyedge[1])]									

		# split boundaries
		all_splits = self.singularities()
		for boundary in self.boundaries():
			splits = [vkey for vkey in boundary if vkey in all_splits]
			new_splits = []

			if len(splits) == 0:
				new_splits += [vkey for vkey in list(itemgetter(0, int(floor(len(boundary) / 3)), int(floor(len(boundary) * 2 / 3)))(boundary))]
				
			elif len(splits) == 1:
				i = boundary.index(splits[0])
				new_splits += list(itemgetter(i - int(floor(len(boundary) * 2 / 3)), i - int(floor(len(boundary) / 3)))(boundary))
			
			elif len(splits) == 2:
				one, two = list_split(boundary, [boundary.index(vkey) for vkey in splits])
				half = one if len(one) > len(two) else two
				new_splits.append(half[int(floor(len(half) / 2))])	

			for vkey in new_splits:
				for nbr in self.vertex_neighbors(vkey):
					if not self.is_edge_on_boundary(vkey, nbr):
						new_polyedge = self.polyedge(vkey, nbr)
						polyedges.append(new_polyedge)
						all_splits = list(set(all_splits + new_polyedge))
						break

		# add boundaries
		polyedges += [polyedge for polyedge in self.polyedges() if self.is_edge_on_boundary(polyedge[0], polyedge[1])]

		# get intersections between polyedges for split
		vertices = [vkey for polyedge in polyedges for vkey in set(polyedge)]
		split_vertices = [vkey for vkey in self.vertices() if vertices.count(vkey) > 1]
		
		# split singularity polyedges
		return [split_polyedge for polyedge in polyedges for split_polyedge in list_split(polyedge, [polyedge.index(vkey) for vkey in split_vertices if vkey in polyedge])]

	# --------------------------------------------------------------------------
	# strip topology
	# --------------------------------------------------------------------------

	def number_of_strips(self):
		"""Count the number of strips in the mesh."""
		return len(list(self.strips()))

	def strips(self):
		"""Iterate over the faces of the mesh.

		Yields
		------
		hashable
			The next strip identifier (*key*).
		"""

		for skey in self.strip:
				yield skey

	def collect_strip(self, u0, v0):
		"""Returns all the edges in the strip of the input edge.

		Parameters
		----------
		u : int
			The identifier of the edge start.
		v : int
			The identifier of the edge end.

		Returns
		-------
		strip : list
			The list of the edges in strip.
		"""

		if self.halfedge[u0][v0] is None:
			u0, v0 = v0, u0
			
		edges = [(u0, v0)]

		count = self.number_of_edges()
		while count > 0:
			count -= 1

			u, v = edges[-1]
			w, x = self.face_opposite_edge(u, v)
			
			if (x, w) == edges[0]:
				break
			
			edges.append((x, w))

			if w not in self.halfedge[x] or self.halfedge[x][w] is None:	
				edges = [(v, u) for u, v in reversed(edges)]
				u, v = edges[-1]
				if v not in self.halfedge[u] or self.halfedge[u][v] is None:
					break

		return edges

	def collect_strips(self):
		"""Collect the strip data.

		Returns
		-------
		strip : int
			The number of strips.

		"""

		self.strip = {}

		edges = list(self.not_none_edges())

		strip = -1
		while len(edges) > 0:
			strip += 1

			u0, v0 = edges.pop()
			strip_edges = self.collect_strip(u0, v0)
			self.strip.update({strip: strip_edges})

			for u, v in strip_edges:
				if (u, v) in edges:
					edges.remove((u, v))
				elif (v, u) in edges:
					edges.remove((v, u))

		return strip

	def is_strip_closed(self, skey):
		"""Output whether a strip is closed.

		Parameters
		----------
		skey : hashable
			A strip key.

		Returns
		-------
		bool
			True if the strip is closed. False otherwise.

		"""

		return not self.is_edge_on_boundary(*self.strip[skey][0])

	def strip_edges(self, skey):
		"""Return the edges of a strip.

		Parameters
		----------
		skey : hashable
			A strip key.
		Returns
		-------
		list
			The edges of the strip.

		"""

		return self.strip[skey]


	def edge_strip(self, edge):
		"""Return the strip of an edge.

		Parameters
		----------
		edge : tuple
			An edge as two vertex keys.

		Returns
		-------
		strip
			The strip of the edge.
		"""

		for strip, edges in self.strip.items():
			if edge in edges or tuple(reversed(edge)) in edges:
				return strip

	def strip_faces(self, skey):
		"""Return the faces of a strip.

		Parameters
		----------
		skey : hashable
			A strip key.
		
		Returns
		-------
		list
			The faces of the strip.

		"""

		return [self.halfedge[u][v] for u, v in self.strip_edges(skey) if self.halfedge[u][v] is not None]

	def face_strips(self, fkey):
		"""Return the two strips of a face.

		Parameters
		----------
		fkey : hashable

		Returns
		-------
		list
			The two strips of the face.
		"""

		return [self.edge_strip((u, v)) for u, v in list(self.face_halfedges(fkey))[:2]]

	def substitute_vertex_in_strips(self, old_vkey, new_vkey, strips = None):
		"""Substitute a vertex by another one.

		Parameters
		----------
		old_vkey : hashable
			The old vertex key.
		new_vkey : hashable
			The new vertex key.
		strips : list
			List of specific strip keys. Per default None, i.e. all.

		"""

		if strips is None:
			strips = list(self.strips())
		self.strip.update({skey: [tuple([new_vkey if vkey == old_vkey else vkey for vkey in list(edge)]) for edge in self.strip[skey]] for skey in strips})

	def delete_face_in_strips(self, fkey):
		"""Delete face in strips.

		Parameters
		----------
		old_vkey : hashable
			The old vertex key.
		new_vkey : hashable
			The new vertex key.

		"""

		self.strip = {skey: [(u, v) for u, v in self.strip[skey] if self.halfedge[u][v] != fkey] for skey in self.strips()}

	def strip_connectivity(self):
		"""Compute the network showing the connecitivty of the strips: a network vertex is a quad mesh strip and a network edge is a quad mesh face.

		Returns
		-------
		Network
			A network encoding the connecitivity of the quad mesh strips.

		"""

		vertices = {skey: centroid_points(self.strip_edge_polyline(skey)) for skey in self.strips()}
		edges = [tuple(self.face_strips(fkey)) for fkey in self.faces()]

		return Network.from_vertices_and_edges(vertices, edges)

	def sort_two_colourable_strips(self):
		"""If the strip are two colourable without overlaps, dispatch them in two lists, one per colour.

		Returns
		-------
		red_strips, blue_strips : tuple, None
			A tuple of two lists of strips that do not overlap each other. None if the strips are not two-colourable.

		"""

		strip_connectivity = self.strip_connectivity()
		key_to_colour = is_network_two_colorable(strip_connectivity)

		if key_to_colour is None:
			return None

		else:
			red_strips = [key for key, colour in key_to_colour.items() if colour == 0]
			blue_strips = [key for key, colour in key_to_colour.items() if colour == 1]
			return red_strips, blue_strips

	# --------------------------------------------------------------------------
	# strip geometry
	# --------------------------------------------------------------------------

	def strip_edge_polyline(self, skey):
		"""Return the strip polyline connecting edge midpoints.

		Parameters
		----------
		skey : hashable
			A strip key.

		Returns
		-------
		list
			The edge midpoint polyline.

		"""

		polyline = [self.edge_midpoint(u, v) for u, v in self.strip_edges(skey)]
		
		if self.is_strip_closed(skey):
			return polyline + polyline[: 1]
		
		else:
			return polyline

	def strip_face_polyline(self, skey):
		"""Return the strip polyline connecting face centroids.

		Parameters
		----------
		skey : hashable
			A strip key.
			
		Returns
		-------
		list
			The face centroid polyline.

		"""

		polyline = [self.face_centroid(fkey) for fkey in self.strip_faces(skey)]

		if self.is_strip_closed(skey):
			return polyline + polyline[: 1]
		
		else:
			return polyline

	def strip_contour_polyedges(self, skey):
		"""Return the two contour polyedges of a strip.

		Parameters
		----------
		skey : hashable
			A strip key.
			
		Returns
		-------
		tuple
			The pair of polyedges contouring the strip.

		"""

		strip_edges = self.strip_edges(skey)

		starts = [edge[0] for edge in strip_edges]
		ends = [edge[1] for edge in strip_edges]

		if self.is_strip_closed(skey):
			starts += starts[:1]
			ends += ends[:1]

		return (starts, ends)	

	def strip_contour_polylines(self, skey):
		"""Return the two contour polylines of a strip.

		Parameters
		----------
		skey : hashable
			A strip key.
			
		Returns
		-------
		tuple
			The pair of polylines contouring the strip.

		"""

		starts, ends = self.strip_contour_polyedges(skey)
		return ([self.vertex_coordinates(vkey) for vkey in starts], [self.vertex_coordinates(vkey) for vkey in ends])	

# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

	import compas

	mesh = QuadMesh.from_obj(compas.get('faces.obj'))

	#mesh.delete_face(13)

	print mesh.singularity_polyedges()
	
	mesh.collect_strips()

	for skey in mesh.strips():
		print mesh.strip_face_polyline(skey)

	mesh.strip_connectivity()


