import compas

try:
	import rhinoscriptsyntax as rs

except ImportError:
		compas.raise_if_ironpython()

from compas.geometry import Polyline

from compas_rhino.geometry import RhinoMesh
from compas_pattern.cad.rhino.objects.surface import RhinoSurface
from compas_pattern.cad.rhino.objects.surface import RhinoCurve
from compas_rhino.geometry import RhinoPoint

from compas.geometry import distance_point_point
from compas.geometry import closest_point_in_cloud

from compas_rhino.helpers import mesh_draw_vertices
from compas_rhino.helpers import mesh_select_vertices

from compas_pattern.cad.rhino.draw import draw_mesh

from compas_pattern.utilities.lists import list_split

__all__ = [
	'automated_smoothing_constraints',
	'automated_smoothing_surface_constraints',
	'customized_smoothing_constraints',
	'display_smoothing_constraints'
]


def automated_smoothing_surface_constraints(mesh, surface):
	"""Apply automatically surface-related constraints to the vertices of a mesh to smooth: kinks, boundaries and surface.

	Parameters
	----------
	mesh : Mesh
		The mesh to apply the constraints to for smoothing.
	surface : RhinoSurface
		A RhinoSurface object on which to constrain mesh vertices.

	Returns
	-------
	constraints : dict
		A dictionary of mesh constraints for smoothing as vertex keys pointing to point, curve or surface objects.

	"""

	constraints = {}

	points = [rs.AddPoint(point) for point in surface.kinks()]
	curves = surface.borders(type = 0)

	constraints.update({vkey: surface.guid for vkey in mesh.vertices()})

	for vkey in mesh.vertices_on_boundary():
		xyz = mesh.vertex_coordinates(vkey)
		projections = {curve: distance_point_point(xyz, RhinoCurve(curve).closest_point(xyz)) for curve in curves}
		constraints.update({vkey: min(projections, key = projections.get)})

	key_to_index = {i: vkey for i, vkey in enumerate(mesh.vertices_on_boundary())}
	vertex_coordinates = tuple(mesh.vertex_coordinates(vkey) for vkey in mesh.vertices_on_boundary())
	constraints.update({key_to_index[closest_point_in_cloud(rs.PointCoordinates(point), vertex_coordinates)[2]]: point for point in points})
	
	return constraints


def automated_smoothing_constraints(mesh, points = None, curves = None, surface = None):
	"""Apply automatically point, curve and surface constraints to the vertices of a mesh to smooth.

	Parameters
	----------
	mesh : Mesh
		The mesh to apply the constraints to for smoothing.
	points : list
		List of XYZ coordinates on which to constrain mesh vertices. Default is None.
	curves : list
		List of RhinoCurve objects on which to constrain mesh vertices. Default is None.
	surface : RhinoSurface
		A RhinoSurface object on which to constrain mesh vertices. Default is None.

	Returns
	-------
	constraints : dict
		A dictionary of mesh constraints for smoothing as vertex keys pointing to point, curve or surface objects.

	"""

	constraints = {}
	constrained_vertices = {}

	vertices = list(mesh.vertices())
	vertex_coordinates = [mesh.vertex_coordinates(vkey) for vkey in mesh.vertices()]
	
	if points is not None and len(points) != 0:
		constrained_vertices.update({vertices[closest_point_in_cloud(rs.PointCoordinates(point), vertex_coordinates)[2]]: point for point in points})
	
	if surface is not None:
		constraints.update({vkey: surface for vkey in mesh.vertices()})
	
	if curves is not None and len(curves) != 0:
		boundaries = [split_boundary for boundary in mesh.boundaries() for split_boundary in list_split(boundary, [boundary.index(vkey) for vkey in constrained_vertices.keys() if vkey in boundary])]
		boundary_midpoints = [Polyline([mesh.vertex_coordinates(vkey) for vkey in boundary]).point(t = .5) for boundary in boundaries]
		curve_midpoints = [rs.EvaluateCurve(curve, rs.CurveParameter(curve, .5)) for curve in curves]
		midpoint_map = {i: closest_point_in_cloud(boundary_midpoint, curve_midpoints)[2] for i, boundary_midpoint in enumerate(boundary_midpoints)}
		constraints.update({vkey: curves[midpoint_map[i]] for i, boundary in enumerate(boundaries) for vkey in boundary})
	
	if points is not None:
		constraints.update(constrained_vertices)

	return constraints


def customized_smoothing_constraints(mesh, constraints):
	"""Add custom point, curve and surface constraints to the vertices of a mesh to smooth.

	Parameters
	----------
	mesh : Mesh
		The mesh to apply the constraints to for smoothing.
	constraints : dict
		A dictionary of mesh constraints for smoothing as vertex keys pointing to point, curve or surface objects.

	Returns
	-------
	constraints : dict
		The updated dictionary of mesh constraints for smoothing as vertex keys pointing to point, curve or surface objects.

	"""

	while True:

		guids = display_smoothing_constraints(mesh, constraints)
		vkeys = mesh_select_vertices(mesh)
		if len(vkeys) == 2 and rs.GetString('get all polyedge?', strings = ['True', 'False']) == 'True':
			u, v = vkeys
			vkeys = mesh.polyedge(u, v)
		
		if vkeys is None:
			break
	
		constraint = rs.GetString('edit smoothing constraints?', strings = ['point', 'curve', 'surface', 'exit'])

		rs.DeleteObjects(guids)

		if constraint is None or constraint == 'exit':
			break

		elif constraint == 'point':
			point = RhinoPoint.from_selection()
			constraints.update({vkey: point.guid for vkey in vkeys})

		elif constraint == 'curve':
			curve = RhinoCurve.from_selection()
			constraints.update({vkey: curve.guid for vkey in vkeys})

		elif constraint == 'surface':
			surface = RhinoSurface.from_selection()
			constraints.update({vkey: surface.guid for vkey in vkeys})

	return constraints


def display_smoothing_constraints(mesh, constraints):
	"""Display current state of constraints on the vertices of a mesh to smooth.

	Parameters
	----------
	mesh : Mesh
		The mesh to apply the constraints to for smoothing.
	constraints : dict
		A dictionary of mesh constraints for smoothing as vertex keys pointing to point, curve or surface objects.

	Returns
	-------
	guid
		Guid of Rhino points coloured according to the type of constraint applied.

	"""
	
	#color = {vkey: (255, 0, 0) if vkey in constraints and rs.ObjectType(constraints[vkey]) == 1
	#			  else (0, 255, 0) if vkey in constraints and rs.ObjectType(constraints[vkey]) == 4
	#			  else (0, 0, 255) if vkey in constraints and rs.ObjectType(constraints[vkey]) == 8
	#			  else (0, 0, 0) for vkey in mesh.vertices()}

	guids_index = {guid: i for i, guid in enumerate(list(set(constraints.values())))}
	n = len(guids_index.keys())
	color = {}
	for vkey in mesh.vertices():
		if vkey in constraints:
			k = float(guids_index[constraints[vkey]]) / float((n - 1))
			color[vkey] = (int(255.0 * k), int(255.0 * (1.0 - k)), 0)
		else:
			color[vkey] = (0, 0, 0)

	return mesh_draw_vertices(mesh, color = color)


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    import compas
