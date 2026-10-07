import bpy, math, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
# Generalised from docs/chair_scene.py (SheenChair case).
# env: MODEL OUT MODE(color|clay|mask) AZ(deg, 0=front -Y) EL(camera height as fraction of size.z above ground, or absolute via ELABS)
#      TZ (target height fraction) FILL (fraction of frame the object occupies) LENS RX RY RZ (extra object rotation deg) W H SAMPLES FLOOR(r,g,b)
OUT=os.environ["OUT"]; MODE=os.environ.get("MODE","color")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.environ["MODEL"])
sc=bpy.context.scene
# optional variant / hide
for nm in os.environ.get("HIDE","").split(","):
    if nm and nm in bpy.data.objects: bpy.data.objects[nm].hide_render=True
# extra rotation about origin via empty parent
rx,ry,rz=(math.radians(float(os.environ.get(k,"0"))) for k in ("RX","RY","RZ"))
if rx or ry or rz:
    bpy.ops.object.empty_add(location=(0,0,0)); P=bpy.context.active_object
    for o in list(sc.objects):
        if o is not P and o.parent is None: o.parent=P
    P.rotation_euler=(rx,ry,rz); bpy.context.view_layer.update()
objs=[o for o in sc.objects if o.type=="MESH" and not o.hide_render]
mn=Vector((1e9,)*3); mx=Vector((-1e9,)*3)
for o in objs:
    for c in o.bound_box:
        w=o.matrix_world@Vector(c); mn=Vector(map(min,mn,w)); mx=Vector(map(max,mx,w))
ctr=(mn+mx)/2; size=mx-mn; H=mn.z; R=max(size.x,size.y,size.z)
print("BOUNDS",tuple(mn),tuple(mx))
fc=tuple(float(v) for v in os.environ.get("FLOOR","0.8,0.8,0.8").split(","))
bpy.ops.mesh.primitive_plane_add(size=R*40,location=(ctr.x,ctr.y,H)); fl=bpy.context.active_object
fm=bpy.data.materials.new("Floor"); fm.use_nodes=True; fb=fm.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value=fc+(1,); fb.inputs["Roughness"].default_value=0.7; fl.data.materials.append(fm)
w=sc.world=bpy.data.worlds.new("W"); w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.75,0.77,0.8,1); w.node_tree.nodes["Background"].inputs[1].default_value=0.6
az=math.radians(float(os.environ.get("AZ","-35")))
el=float(os.environ.get("EL","0.32")); tz=float(os.environ.get("TZ","0.48"))
tgt=Vector((ctr.x,ctr.y,H+size.z*tz))
dirv=Vector((math.sin(az),-math.cos(az),0))
bpy.ops.object.camera_add(); cam=bpy.context.active_object; sc.camera=cam; cam.data.lens=float(os.environ.get("LENS","50"))
sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage=int(os.environ.get("W","960")),int(os.environ.get("H","540")),100
corners=[]
for o in objs:
    corners+= [o.matrix_world@Vector(c) for c in o.bound_box]
FILL=float(os.environ.get("FILL","0.7"))
def place(d):
    cp=tgt+dirv*d; cp.z=H+size.z*el if "ELABS" not in os.environ else H+R*float(os.environ["ELABS"])
    cam.location=cp; cam.rotation_euler=(tgt-cp).to_track_quat('-Z','Y').to_euler(); bpy.context.view_layer.update()
    pts=[world_to_camera_view(sc,cam,p) for p in corners]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]
    return max(max(xs)-min(xs),max(ys)-min(ys)), (min(xs),max(xs),min(ys),max(ys))
d=R*2.6
for _ in range(30):
    f,bb=place(d); d*=(f/FILL)**0.9
f,bb=place(d); print("FRAME",f,bb)
cp=cam.location.copy()
bpy.ops.object.light_add(type="AREA",location=(ctr.x-R*1.5,ctr.y-R*1.5,H+R*2.2)); L=bpy.context.active_object
L.data.size=R*1.5; L.data.energy=300*R*R; L.rotation_euler=(tgt-L.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type="AREA",location=(ctr.x+R*2,ctr.y-R*0.5,H+R*1.2)); L2=bpy.context.active_object
L2.data.size=R*2; L2.data.energy=120*R*R; L2.rotation_euler=(tgt-L2.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine="CYCLES"; sc.cycles.device="CPU"; sc.cycles.samples=int(os.environ.get("SAMPLES","48")); sc.cycles.use_denoising=False
sc.view_settings.view_transform="AgX"
if MODE=="clay":
    cm=bpy.data.materials.new("Clay"); cm.use_nodes=True; cb=cm.node_tree.nodes["Principled BSDF"]
    cb.inputs["Base Color"].default_value=(0.78,0.78,0.78,1); cb.inputs["Roughness"].default_value=0.6
    bpy.context.view_layer.material_override=cm
if MODE=="mask":
    fl.hide_render=True; sc.render.film_transparent=True; sc.cycles.samples=4
    for l in (L,L2): l.hide_render=True
sc.render.filepath=os.path.join(OUT,f"{MODE}.png"); bpy.ops.render.render(write_still=True); print("DONE",MODE,"ctr",tuple(ctr),"size",tuple(size))
