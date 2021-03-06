import itertools

from compas.datastructures.mesh import Mesh

from compas.geometry import circle_from_points
from compas.geometry import circle_from_points_xy
from compas.geometry import angle_points
from compas.geometry import bestfit_plane

from compas.utilities import geometric_key
from compas.utilities import pairwise

__author__     = ['Robin Oval']
__copyright__  = 'Copyright 2017, Block Research Group - ETH Zurich'
__license__    = 'MIT License'
__email__      = 'oval@arch.ethz.ch'

__all__ = [

]

class Mesh(Mesh):

	def __init__(self):
		super(Mesh, self).__init__()


	@classmethod
	def from_polylines(cls, boundary_polylines, other_polylines):
		"""Construct mesh from polylines.

		Based on construction from_lines,
		with removal of vertices that are not polyline extremities
		and of faces that represent boundaries.

		This specific method is useful to get the mesh connectivity from a set of (discretised) curves,
		that could overlap and yield a wrong connectivity if using from_lines based on the polyline extremities only.

		Parameters
		----------
		boundary_polylines : list
			List of polylines representing boundaries as lists of vertex coordinates.
		other_polylines : list
			List of the other polylines as lists of vertex coordinates.

		Returns
		-------
		Mesh
			A mesh object.
		"""

		corner_vertices = [geometric_key(xyz) for polyline in boundary_polylines + other_polylines for xyz in [polyline[0], polyline[-1]]]
		boundary_vertices = [geometric_key(xyz) for polyline in boundary_polylines for xyz in polyline]

		mesh = cls.from_lines([(u, v) for polyline in boundary_polylines + other_polylines for u, v in pairwise(polyline)])

		# remove the vertices that are not from the polyline extremities and the faces with all their vertices on the boundary
		vertex_keys = [vkey for vkey in mesh.vertices() if geometric_key(mesh.vertex_coordinates(vkey)) in corner_vertices]
		vertex_map = {vkey: i for i, vkey in enumerate(vertex_keys)}
		vertices = [mesh.vertex_coordinates(vkey) for vkey in vertex_keys]
		faces = [[vertex_map[vkey] for vkey in mesh.face_vertices(fkey) if geometric_key(mesh.vertex_coordinates(vkey)) in corner_vertices] for fkey in mesh.faces() if sum([geometric_key(mesh.vertex_coordinates(vkey)) not in boundary_vertices for vkey in mesh.face_vertices(fkey)])]

		mesh.cull_vertices()

		return cls.from_vertices_and_faces(vertices, faces)

	def to_vertices_and_faces(self, keep_keys=True):

		if keep_keys:
			vertices = {vkey: self.vertex_coordinates(vkey) for vkey in self.vertices()}
			faces = {fkey: self.face_vertices(fkey) for fkey in self.faces()}
		else:
			key_index = self.key_index()
			vertices = [self.vertex_coordinates(key) for key in self.vertices()]
			faces = [[key_index[key] for key in self.face_vertices(fkey)] for fkey in self.faces()]
		return vertices, faces

	# --------------------------------------------------------------------------
	# global
	# --------------------------------------------------------------------------


	# --------------------------------------------------------------------------
	# local
	# --------------------------------------------------------------------------

	

	# def delete_face(self, fkey):
	# 	"""Delete a face from the mesh object.

	# 	Parameters
	# 	----------
	# 	fkey : hashable
	# 		The identifier of the face.

	# 	Examples
	# 	--------
	# 	.. plot::
	# 		:include-source:

	# 		import compas
	# 		from compas.datastructures import Mesh
	# 		from compas.plotters import MeshPlotter

	# 		mesh = Mesh.from_obj(compas.get('faces.obj'))

	# 		mesh.delete_face(12)

	# 		plotter = MeshPlotter(mesh)
	# 		plotter.draw_vertices()
	# 		plotter.draw_faces()
	# 		plotter.show()

	# 	"""

	# 	for u, v in self.face_halfedges(fkey):
	# 		self.halfedge[u][v] = None
	# 		# additionnal check u in self.halfedge[v]
	# 		if u in self.halfedge[v] and self.halfedge[v][u] is None:
	# 			del self.halfedge[u][v]
	# 			del self.halfedge[v][u]
	# 	del self.face[fkey]

	def is_vertex_kink(self, vkey, threshold_angle):
		"""Return whether there is a kink at a boundary vertex according to a threshold angle.

		Parameters
		----------
		vkey : Key
			The boundary vertex key.
		threshold_angle : float
			Threshold angle in rad.

		Returns
		-------
		bool
			True if the boundary angle is a kink, i.e. is larger than the threshold angle. False otherwise.

		"""	
		
		# check if vertex is on boundary
		if not self.is_vertex_on_boundary(vkey):
			return False

		# get the two adjacent boundary vertices (exactly two for manifold meshes)
		ukey, wkey = [nbr for nbr in self.vertex_neighbors(vkey) if self.is_edge_on_boundary(vkey, nbr)]
		# compare boundary angle with threshold angle
		return angle_points(self.vertex_coordinates(ukey), self.vertex_coordinates(vkey), self.vertex_coordinates(wkey)) > threshold_angle

	def kinks(self, threshold_angle):
		"""Return the boundary vertices with kinks.

		Parameters
		----------
		threshold_angle : float
			Threshold angle in rad.

		Returns
		-------
		list
			The list of the boundary vertices at kink angles higher than the threshold value.

		"""

		return [vkey for vkey in self.vertices_on_boundary() if self.is_vertex_kink(vkey, threshold_angle)]

	# --------------------------------------------------------------------------
	# modifications
	# --------------------------------------------------------------------------


def mesh_insert_vertex_on_edge(mesh, u, v, vkey=None):
	"""Insert an existing vertex on an edge.

	Parameters
	----------
	u: hashable
		The first edge vertex.
	v: hashable
		The second edge vertex.
	vkey: hashable, optional
		The vertex key to insert.
		Default is add a new vertex at mid-edge.

	"""

	# add new vertex if there is none
	if vkey is None:
		mesh.add_vertex(attr_dict = {attr: xyz for attr, xyz in zip(['x', 'y', 'z'], mesh.edge_midpoint(u, v))})

	# insert vertex
	for fkey, halfedge in zip(mesh.edge_faces(u, v), [(u, v), (v, u)]):
		if fkey is not None:
			face_vertices = mesh.face_vertices(fkey)[:]
			face_vertices.insert(face_vertices.index(halfedge[-1]), vkey)
			mesh.delete_face(fkey)
			mesh.add_face(face_vertices, fkey)


def mesh_substitute_vertex_in_faces(mesh, old_vkey, new_vkey, fkeys=None):
	"""Substitute in a mesh a vertex by another one.
	In all faces by default or in a given set of faces.

	Parameters
	----------
	old_vkey : hashable
		The old vertex key.
	new_vkey : hashable
		The new vertex key.
	fkeys : list, optional
		List of face keys where to subsitute the old vertex by the new one.
		Default is to subsitute in all faces.

	"""

	# apply to all faces if there is none chosen
	if fkeys is None:
		fkeys = mesh.faces()

	# substitute vertices
	for fkey in fkeys:
		face_vertices = [new_vkey if key == old_vkey else key for key in mesh.face_vertices(fkey)]
		mesh.delete_face(fkey)
		mesh.add_face(face_vertices, fkey)

def mesh_move_vertex(mesh, vector, vkey):
	"""Move a mesh vertex by a vector.

	Parameters
	----------
	mesh : Mesh
		A mesh.
	vkey : hashable
		A vrtex key.
	vector : list
		An XYZ vector.

	"""

	mesh.vertex[vkey]['x'] += vector[0]
	mesh.vertex[vkey]['y'] += vector[1]
	mesh.vertex[vkey]['z'] += vector[2]

	return mesh.vertex_coordinates(vkey)

def mesh_move(mesh, vector):
	"""Move a mesh by a vector.

	Parameters
	----------
	mesh : Mesh
		A mesh.
	vector : list
		An XYZ vector.

	"""

	for vkey in mesh.vertices():
		mesh_move_vertex(mesh, vector, vkey)

# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

	import compas

	mesh = Mesh.from_obj(compas.get('faces.obj'))
