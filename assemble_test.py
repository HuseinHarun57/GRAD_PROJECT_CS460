"""
Build parts A, B, C from test_parts.json and assemble them with a DFS over the
connection graph (undirected; cycles are checked for consistency, not re-placed).

Run in Blender: Scripting tab -> open this file -> Run Script.
"""
import json
from collections import defaultdict

import bpy
from mathutils import Vector

JSON_PATH = "C:/Users/husei/Desktop/UNO/FALL 2026/3D GRAPHICS/GRAD PROJECT/3/git/test_parts.json"   # <-- edit
SCALE = 0.01                              # cm -> Blender metres
COLLECTION = "TestAssembly"
TOL = 1e-6


def make_box(name, dims_cm, collection):
    """Box with its origin at the min corner, so connection points are simple offsets."""
    dx, dy, dz = (d * SCALE for d in dims_cm)
    verts = [(x, y, z) for x in (0, dx) for y in (0, dy) for z in (0, dz)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5),   # -x, +x
             (0, 4, 5, 1), (2, 3, 7, 6),   # -y, +y
             (0, 2, 6, 4), (1, 5, 7, 3)]   # -z, +z
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def assemble(part_names, connections, base):
    """DFS from base. Each edge places the neighbour so its point coincides with ours."""
    adj = defaultdict(list)
    for c in connections:
        p, q = c["parts"]
        pp, qp = (Vector(v) for v in c["points"])
        adj[p].append((q, pp, qp))
        adj[q].append((p, qp, pp))

    loc = {base: Vector((0, 0, 0))}
    order, stack = [base], [base]
    while stack:
        cur = stack.pop()
        for nbr, cur_pt, nbr_pt in adj[cur]:
            target = loc[cur] + cur_pt - nbr_pt
            if nbr not in loc:
                loc[nbr] = target
                order.append(nbr)
                stack.append(nbr)
            elif (loc[nbr] - target).length > TOL:   # cycle edge disagrees
                raise ValueError(f"Inconsistent placement of {nbr}: "
                                 f"{tuple(loc[nbr])} vs {tuple(target)} via {cur}")

    missing = set(part_names) - set(loc)
    if missing:
        raise ValueError(f"Parts not connected to base {base}: {sorted(missing)}")
    return loc, order


def main():
    with open(JSON_PATH) as f:
        spec = json.load(f)

    #Clearing object (cube) in Blender's default collection
    for o in list(bpy.data.objects):
            if o.type == 'MESH':
                bpy.data.objects.remove(o, do_unlink=True)

    # fresh collection each run
    old = bpy.data.collections.get(COLLECTION)
    if old:
        for o in list(old.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)

    objs = {n: make_box(n, p["dims"], coll) for n, p in spec["parts"].items()}
    loc, order = assemble(spec["parts"].keys(), spec["connections"], spec["base"])

    for name, l in loc.items():
        objs[name].location = l * SCALE
    print("DFS placement order:", " -> ".join(order))
    for name in order:
        print(f"  {name}: {tuple(round(v, 3) for v in loc[name])} cm")


main()
