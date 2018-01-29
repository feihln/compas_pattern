import rhinoscriptsyntax as rs

import compas_rhino as rhino

from compas.datastructures.mesh import Mesh

from compas_pattern.topology.grammar_rules import quad_mix_1
from compas_pattern.topology.grammar_rules import penta_quad_1
from compas_pattern.topology.grammar_rules import hexa_quad_1

from compas_pattern.topology.face_strip_operations import face_strip_collapse

# mesh selection
guid = rs.GetObject('get mesh')
mesh = rhino.mesh_from_guid(Mesh, guid)

## mesh element selection
#artist = rhino.MeshArtist(mesh, layer='mesh_artist')
#artist.clear_layer()
#
#artist.draw_vertices()
#artist.draw_vertexlabels()
#artist.redraw()
#ukey = rhino.mesh_select_vertex(mesh, message = 'ukey')
#vkey = rhino.mesh_select_vertex(mesh, message = 'vkey')
#artist.clear_layer()
#artist.redraw()


dots = {rs.AddTextDot(vkey, mesh.vertex_coordinates(vkey)): vkey for vkey in mesh.vertices()}

guid = rs.GetObject('u vertex', filter = 8192)
ukey = dots[guid]

guid = rs.GetObject('v vertex', filter = 8192)
vkey = dots[guid]

rs.DeleteObjects(dots)

#artist.draw_facelabels()
#artist.redraw()
#fkey = rhino.mesh_select_face(mesh, message = 'fkey')
#artist.clear_layer()
#artist.redraw()

#artist.draw_edgelabels()
#artist.redraw()
#ukey, vkey = rhino.mesh_select_edge(mesh, message = 'edge for face strip collapse')
#artist.clear_layer()
#artist.redraw()

#rs.DeleteLayer('mesh_artist')


mesh = face_strip_collapse(Mesh, mesh, ukey, vkey)

#e = quad_mix_1(mesh, fkey, vkey, ukey)
#
### conforming: propagate T-junctions
## propagate until boundary or closed loop
#is_loop = False
#wkey = e
#count = mesh.number_of_faces()
#while count > 0:
#    count -= 1
#    next_fkey = mesh.halfedge[vkey][wkey]
#    ukey = mesh.face_vertex_descendant(next_fkey, wkey)
#    if wkey in mesh.halfedge[ukey] and mesh.halfedge[ukey][wkey] is not None:
#        next_fkey = mesh.halfedge[ukey][wkey]
#        if len(mesh.face_vertices(next_fkey)) == 5:
#            vkey = wkey
#            wkey = penta_quad_1(mesh, next_fkey, wkey)
#            # add to faces along feature to check
#            continue
#        if len(mesh.face_vertices(next_fkey)) == 6:
#            vkey = wkey
#            wkey = hexa_quad_1(mesh, next_fkey, wkey)
#            #if wkey == e2:
#            #    is_loop = True
#            # add to faces along feature to check
#            break
#    break
# # if not loop, propaget in other direction
# if not is_loop:
#     vkey = v
#     wkey = e2
#     count = mesh.number_of_faces()
#     while count > 0:
#         count -= 1
#         next_fkey = mesh.halfedge[vkey][wkey]
#         ukey = mesh.face_vertex_descendant(next_fkey, wkey)
#         if wkey in mesh.halfedge[ukey] and mesh.halfedge[ukey][wkey] is not None:
#             next_fkey = mesh.halfedge[ukey][wkey]
#             if len(mesh.face_vertices(next_fkey)) == 5:
#                 vkey = wkey
#                 wkey = penta_quad_1(mesh, next_fkey, wkey)
#                 # add to faces along feature to check
#                 continue
#             if len(mesh.face_vertices(next_fkey)) == 6:
#                 vkey = wkey
#                 wkey = hexa_quad_1(mesh, next_fkey, wkey)
#                 if wkey == e2:
#                     is_loop = True
#                 # add to faces along feature to check
#                 break
#         break

print mesh
for u, v in mesh.edges():
    u_xyz = mesh.vertex_coordinates(u)
    v_xyz = mesh.vertex_coordinates(v)
    if u_xyz == v_xyz:
        print u_xyz, v_xyz
    rs.AddLine(u_xyz, v_xyz)
# draw mesh
vertices = [mesh.vertex_coordinates(vkey) for vkey in mesh.vertices()]
face_vertices = [mesh.face_vertices(fkey) for fkey in mesh.faces()]
mesh_guid = rhino.utilities.drawing.xdraw_mesh(vertices, face_vertices, None, None)
#rhino.helpers.mesh_draw(mesh, show_faces = False)
#rs.AddLayer('edited_mesh')
#rs.ObjectLayer(mesh_guid, layer = 'edited_mesh')