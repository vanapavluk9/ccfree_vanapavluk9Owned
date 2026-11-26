import bpy, math, os

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
FPS, FRAMES = 24, 96
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.fps = FPS

def mat(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    return m

BROWN = mat("brown", (0.45, 0.25, 0.1))
DARK = mat("dark", (0.15, 0.08, 0.04))
BLACK = mat("black", (0.02, 0.02, 0.02))
GRASS = mat("grass", (0.15, 0.4, 0.12))

def cube(name, loc, scale, material, parent):
    bpy.ops.mesh.primitive_cube_add(size=2)
    o = bpy.context.object
    o.name = name
    o.parent = parent
    o.location = loc
    o.scale = scale
    o.data.materials.append(material)
    return o

def sphere(name, loc, scale, material, parent):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    o = bpy.context.object
    o.name = name
    o.parent = parent
    o.location = loc
    o.scale = scale
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o

def empty(name, loc, parent=None):
    e = bpy.data.objects.new(name, None)
    scene.collection.objects.link(e)
    e.location = loc
    e.parent = parent
    return e

# Dog (faces +X)
root = empty("DogRoot", (-3.5, 0, 0))
cube("Body", (0, 0, 0.8), (0.75, 0.3, 0.3), BROWN, root)
head = empty("HeadPivot", (0.85, 0, 1.0), root)
sphere("Head", (0, 0, 0), (0.27, 0.24, 0.24), BROWN, head)
cube("Snout", (0.28, 0, -0.05), (0.18, 0.12, 0.1), DARK, head)
sphere("Nose", (0.47, 0, -0.01), (0.05, 0.05, 0.05), BLACK, head)
sphere("EyeL", (0.17, 0.12, 0.08), (0.04, 0.04, 0.04), BLACK, head)
sphere("EyeR", (0.17, -0.12, 0.08), (0.04, 0.04, 0.04), BLACK, head)
cube("EarL", (-0.05, 0.2, 0.1), (0.07, 0.04, 0.16), DARK, head)
cube("EarR", (-0.05, -0.2, 0.1), (0.07, 0.04, 0.16), DARK, head)

tail = empty("TailPivot", (-0.75, 0, 0.95), root)
cube("Tail", (-0.25, 0, 0.1), (0.28, 0.04, 0.04), DARK, tail)
tail.rotation_euler[1] = math.radians(-25)

legs = []
for name, x, y in [("FL", 0.5, 0.2), ("FR", 0.5, -0.2), ("BL", -0.5, 0.2), ("BR", -0.5, -0.2)]:
    p = empty("Leg" + name, (x, y, 0.55), root)
    cube("LegMesh" + name, (0, 0, -0.27), (0.07, 0.07, 0.28), BROWN, p)
    cube("Paw" + name, (0.04, 0, -0.55), (0.1, 0.08, 0.04), DARK, p)
    legs.append((p, name))

# Animation
CYCLE = 24
for f in range(1, FRAMES + 2, 3):
    t = (f - 1) / CYCLE * 2 * math.pi
    for p, name in legs:
        phase = 0 if name in ("FL", "BR") else math.pi  # diagonal pairs
        p.rotation_euler[1] = math.radians(30) * math.sin(t + phase)
        p.keyframe_insert("rotation_euler", index=1, frame=f)
    tail.rotation_euler[2] = math.radians(35) * math.sin(t * 3)
    tail.keyframe_insert("rotation_euler", index=2, frame=f)
    head.rotation_euler[1] = math.radians(6) * math.sin(t * 2)
    head.keyframe_insert("rotation_euler", index=1, frame=f)
    root.location.z = 0.03 * abs(math.sin(t))
    root.location.x = -3.5 + 7.0 * (f - 1) / FRAMES
    root.keyframe_insert("location", frame=f)

# Ground, light, camera, world
bpy.ops.mesh.primitive_plane_add(size=40)
ground = bpy.context.object
ground.data.materials.append(GRASS)

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 4
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.lens = 28
cam.location = (0, -7, 1.3)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.75, 1.0, 1)

# Render
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 960, 540
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.filepath = os.path.abspath("out/dog_")
bpy.ops.render.render(animation=True)
