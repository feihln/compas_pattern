from compas.datastructures import Network
from compas.datastructures.network.operations import network_polylines

from compas_pattern.cad.rhino.objects.surface import RhinoSurface
from compas_pattern.cad.rhino.objects.curve import RhinoCurve
from compas_rhino.utilities import delete_object

from compas.utilities import pairwise

try:
	import rhinoscriptsyntax as rs

except ImportError:
	import compas
	compas.raise_if_ironpython()

__author__     = ['Robin Oval']
__copyright__  = 'Copyright 2018, Block Research Group - ETH Zurich'
__license__    = 'MIT License'
__email__      = 'oval@arch.ethz.ch'

__all__ = [
	'surface_discrete_mapping'
]


def surface_discrete_mapping(srf_guid, discretisation, minimum_discretisation = 5, crv_guids = [], pt_guids = []):
	"""Map the boundaries of a Rhino NURBS surface to planar poylines dicretised within some discretisation using the surface UV parameterisation.
	Curve and point feautres on the surface can be included.

	Parameters
	----------
	srf_guid : guid
		A surface guid.
	crv_guids : list
		List of guids of curves on the surface.
	pt_guids : list
		List of guids of points on the surface.
	discretisation : float
		The discretisation of the surface boundaries.
	minimum_discretisation : int
		The minimum discretisation of the surface boundaries.

	Returns
	-------
	tuple
		Tuple of the mapped objects: outer boundary, inner boundaries, polyline_features, point_features.

	"""

	srf = RhinoSurface(srf_guid)

	# a boundary may be made of multiple boundary components and therefore checking for closeness and joining are necessary
	mapped_borders = []

	for i in [1, 2]:
		mapped_border = []

		for border in srf.borders(type = i):
			border = RhinoCurve(border)
			points = [srf.point_xyz_to_uv(pt) for pt in border.divide(max(int(border.length() / discretisation) + 1, minimum_discretisation))]
			
			if border.is_closed():
				points.append(points[0])
			
			mapped_border.append(points)
			rs.DeleteObject(border.guid)
		mapped_borders.append(mapped_border)

	outer_boundaries, inner_boundaries = [network_polylines(Network.from_lines([(u, v) for border in mapped_borders[i] for u, v in pairwise(border)])) for i in [0, 1]]
	
	# mapping of the curve features on the surface
	mapped_curves = []

	for crv_guid in crv_guids:

		curve = RhinoCurve(crv_guid)
		points = [srf.point_xyz_to_uv(pt) for pt in curve.divide(max(int(curve.length() / discretisation) + 1, minimum_discretisation))]
		
		if curve.is_closed():
			points.append(points[0])
		
		mapped_curves.append(points)

	polyline_features = network_polylines(Network.from_lines([(u, v) for curve in mapped_curves for u, v in pairwise(curve)]))

	# mapping of the point features onthe surface
	point_features = [srf.point_xyz_to_uv(rs.PointCoordinates(pt_guid)) for pt_guid in pt_guids]

	return outer_boundaries[0], inner_boundaries, polyline_features, point_features


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

	import compas
