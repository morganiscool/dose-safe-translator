"""Dose-Safe Translator: the 3D pictures for the landing page, built and rendered by script.

Run (from the repo folder):
  "C:/Program Files/Blender Foundation/Blender 5.3/blender.exe" --background --python blender/scene.py -- --out web/media/src --shot all

Shots:
  carton   an over-the-counter carton at three-quarters, caplets in front, transparent background
           (its faces are blender/textures/front.png and drugfacts.png; the Drug Facts lines are real
           label text from data/otc_directions.csv)
  caplets  six caplets in a row on carton-blue board: "do not take more than 6 caplets"
"""
import argparse
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--out", default=os.path.join(HERE, "..", "web", "media", "src"))
parser.add_argument("--shot", default="all", choices=["all", "carton", "caplets", "turntable"])
parser.add_argument("--samples", type=int, default=160)
args = parser.parse_args(argv)
args.out = os.path.abspath(args.out)  # Blender would otherwise resolve it against the drive root
os.makedirs(args.out, exist_ok=True)


def linear(hex_colour):
    """sRGB hex to Blender's linear RGBA."""
    out = []
    for i in (1, 3, 5):
        c = int(hex_colour[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


CARTON = linear("#0e4c92")


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"  # keep the brand colours as they are
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.92, 0.95, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.12
    scene.world = world
    return scene


def use_gpu(scene):
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            (prefs.refresh_devices if hasattr(prefs, "refresh_devices") else prefs.get_devices)()
            found = [d for d in prefs.devices if d.type == kind]
            if found:
                for d in prefs.devices:
                    d.use = d.type == kind
                scene.cycles.device = "GPU"
                return kind
        except Exception:
            continue
    scene.cycles.device = "CPU"
    return "CPU"


def material(name, colour=(1, 1, 1, 1), roughness=0.5, image=None, subsurface=0.0, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Roughness"].default_value = roughness
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    if coat and "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.25
    if image:
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image)
        tex.interpolation = "Cubic"
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def area_light(name, location, target, size, energy, colour=(1, 1, 1)):
    data = bpy.data.lights.new(name, "AREA")
    data.size, data.energy, data.color = size, energy, colour
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = location
    aim(light, target)
    return light


def aim(obj, target):
    direction = (bpy.data.objects.new("_t", None).location.__class__(target) - obj.location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera(location, target, lens=70, f_stop=None, focus=None):
    data = bpy.data.cameras.new("Camera")
    data.lens = lens
    if f_stop:
        data.dof.use_dof = True
        data.dof.aperture_fstop = f_stop
        data.dof.focus_distance = focus
    cam = bpy.data.objects.new("Camera", data)
    bpy.context.collection.objects.link(cam)
    cam.location = location
    aim(cam, target)
    bpy.context.scene.camera = cam
    return cam


def plane(name, size_xy, location, rotation, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size_xy[0], size_xy[1], 1)
    obj.data.materials.append(mat)
    return obj


def caplet(location, angle, mat, tilt=0.0):
    """An oblong caplet: a rounded box, smoothed."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=(tilt, 0, angle))
    obj = bpy.context.object
    obj.scale = (0.19, 0.075, 0.056)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new("round", "BEVEL")
    bevel.width, bevel.segments, bevel.limit_method = 0.032, 8, "NONE"
    obj.modifiers.new("smooth", "SUBSURF").levels = 2
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return obj


def carton_box(w=0.55, d=0.40, h=0.90):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h / 2))
    body = bpy.context.object
    body.scale = (w, d, h)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    body.modifiers.new("edge", "BEVEL").width = 0.004
    body.data.materials.append(material("Carton board", CARTON, roughness=0.55))
    eps = 0.0012
    tex = os.path.join(HERE, "textures")
    front = material("Carton front", image=os.path.join(tex, "front.png"), roughness=0.5)
    facts = material("Drug Facts panel", image=os.path.join(tex, "drugfacts.png"), roughness=0.5)
    faces = [plane("Front", (w, h), (0, -d / 2 - eps, h / 2), (math.radians(90), 0, 0), front),
             plane("Side", (d, h), (w / 2 + eps, 0, h / 2), (math.radians(90), 0, math.radians(90)), facts)]
    for face in faces:  # the printed faces turn with the carton
        face.parent = body
        face.matrix_parent_inverse = body.matrix_world.inverted()
    return body


def render(scene, name, width, height, transparent):
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.film_transparent = transparent
    scene.render.filepath = os.path.join(args.out, name)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {scene.render.filepath} on {scene.cycles.device}")


def shot_carton():
    scene = reset()
    use_gpu(scene)
    carton_box()
    white = material("Caplet", (0.94, 0.94, 0.92, 1), roughness=0.38, subsurface=0.08, coat=0.3)
    for loc, ang in [((-0.20, -0.55, 0.028), 0.5), ((0.05, -0.62, 0.028), -0.35), ((0.33, -0.47, 0.028), 1.2)]:
        caplet(loc, ang, white)
    ground = plane("Ground", (6, 6), (0, 0, 0), (0, 0, 0), material("Ground", (1, 1, 1, 1)))
    ground.is_shadow_catcher = True
    area_light("Key", (-1.2, -1.6, 3.4), (0, 0, 0.4), 2.6, 300)
    # Only the key light casts a shadow, so the shadow stays soft and inside the picture.
    for light in (area_light("Fill", (2.6, -1.0, 1.0), (0, 0, 0.45), 2.5, 60),
                  area_light("Rim", (0.8, 2.4, 2.2), (0, 0, 0.6), 1.2, 160)):
        light.data.use_shadow = False
    camera((1.55, -2.45, 1.15), (0.06, -0.08, 0.42), lens=62)
    render(scene, "carton.png", 1600, 2000, transparent=True)


def shot_caplets():
    scene = reset()
    use_gpu(scene)
    plane("Board", (8, 8), (0, 0, 0), (0, 0, 0), material("Carton board", CARTON, roughness=0.7))
    white = material("Caplet", (0.94, 0.94, 0.92, 1), roughness=0.38, subsurface=0.08, coat=0.3)
    for i in range(6):
        x = (i - 2.5) * 0.235
        caplet((x, (i % 2) * 0.03, 0.028), math.radians((i % 3 - 1) * 7), white)
    area_light("Key", (-1.8, -1.2, 2.4), (0, 0, 0), 3.0, 170)
    area_light("Fill", (2.0, -1.5, 1.2), (0, 0, 0), 3.0, 40)
    camera((0.0, -1.55, 0.62), (0, 0.02, 0.02), lens=36, f_stop=3.2, focus=1.67)
    render(scene, "caplets.png", 2400, 1350, transparent=False)


def shot_turntable():
    """2 s for the explainer's first shot: the carton turns its Drug Facts panel to the camera while the
    camera pushes in. Transparent PNG frames; the video script puts them on white."""
    scene = reset()
    use_gpu(scene)
    scene.cycles.samples = min(args.samples, 64)
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, 60
    body = carton_box()
    white = material("Caplet", (0.94, 0.94, 0.92, 1), roughness=0.38, subsurface=0.08, coat=0.3)
    for loc, ang in [((-0.20, -0.55, 0.028), 0.5), ((0.05, -0.62, 0.028), -0.35), ((0.33, -0.47, 0.028), 1.2)]:
        caplet(loc, ang, white)
    ground = plane("Ground", (8, 8), (0, 0, 0), (0, 0, 0), material("Ground", (1, 1, 1, 1)))
    ground.is_shadow_catcher = True
    area_light("Key", (-1.2, -1.6, 3.4), (0, 0, 0.4), 2.6, 300)
    for light in (area_light("Fill", (2.6, -1.0, 1.0), (0, 0, 0.45), 2.5, 60),
                  area_light("Rim", (0.8, 2.4, 2.2), (0, 0, 0.6), 1.2, 160)):
        light.data.use_shadow = False
    # The carton turns from showing its front to facing its Drug Facts panel at the camera.
    body.rotation_euler = (0, 0, math.radians(22))
    body.keyframe_insert("rotation_euler", frame=1)
    body.rotation_euler = (0, 0, math.radians(-50))
    body.keyframe_insert("rotation_euler", frame=60)
    # The camera pushes in on a target that drifts from the whole carton to the panel.
    target = bpy.data.objects.new("Target", None)
    bpy.context.collection.objects.link(target)
    target.location = (0.04, -0.05, 0.45)
    target.keyframe_insert("location", frame=1)
    target.location = (0.17, -0.19, 0.52)
    target.keyframe_insert("location", frame=60)
    cam = camera((1.55, -2.45, 1.15), (0, 0, 0.45), lens=40)
    track = cam.constraints.new("TRACK_TO")
    track.target, track.track_axis, track.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    cam.keyframe_insert("location", frame=1)
    cam.data.keyframe_insert("lens", frame=1)
    cam.location = (1.05, -1.62, 0.78)
    cam.data.lens = 78
    cam.keyframe_insert("location", frame=60)
    cam.data.keyframe_insert("lens", frame=60)
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.film_transparent = True
    frames = os.path.join(args.out, "turntable")
    os.makedirs(frames, exist_ok=True)
    scene.render.filepath = os.path.join(frames, "####")
    scene.render.use_overwrite = False  # a re-run renders only the frames that are missing
    bpy.ops.render.render(animation=True)
    print(f"Rendered {scene.frame_end} frames to {frames} on {scene.cycles.device}")


if args.shot in ("all", "carton"):
    shot_carton()
if args.shot in ("all", "caplets"):
    shot_caplets()
if args.shot == "turntable":
    shot_turntable()
