# -*- coding: utf-8 -*-
import bpy

_PROMPT_SUFFIX = {
    "HUMAN": "single character, pure white background, no shadows, full body front view, centered, soft even lighting, concept art style, clean silhouette",
    "ANIMAL": "single creature, pure white background, no shadows, full body front view, centered, soft even lighting, concept art style, clean silhouette",
    "ENVIRONMENT": "miniature 3D scene model, pure white background, isometric view, centered, all elements visible, no shadows",
    "PROPS": "single object, pure white background, no shadows, front view, centered, product photography lighting, clean silhouette",
    "CONCEPT": "single physical sculpture representing the concept, pure white background, no shadows, centered, front view, clean silhouette",
}
_DEFAULT_SUFFIX = "single object, pure white background, no shadows, front view, centered, soft even lighting, clean silhouette"

def _import_model(obj_path, apply_sculpt, pipeline_type, prompt, status_callback=None):
    def _cb(msg):
        if status_callback: status_callback(msg)
    if obj_path.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=obj_path)
    else:
        bpy.ops.wm.obj_import(filepath=obj_path)
    imported = bpy.context.selected_objects[0] if bpy.context.selected_objects else None
    print(f"[VAXIS] import done: {obj_path}")
    if imported and apply_sculpt:
        try:
            from . import sculpt_auto
            sculpt_auto.apply_muscle_detail(imported, prompt=prompt, creature_type=pipeline_type if pipeline_type in ("HUMAN","ANIMAL") else "ANIMAL", status_callback=_cb)
        except Exception as se:
            import traceback; traceback.print_exc(); _cb(f"sculpt error: {se}")
    else:
        _cb("complete")
    return None

def _get_api_key():
    try: return bpy.context.scene.vaxis_props.tripo3d_api_key.strip()
    except: return ""

def generate_and_import(prompt, pipeline_type="ANIMAL", apply_sculpt=False, status_callback=None):
    import threading
    def _cb(msg):
        if status_callback: status_callback(msg)
    def _worker():
        try:
            import tempfile, os
            output_dir = tempfile.mkdtemp(prefix="vaxis_gen_")
            api_key = _get_api_key()
            suffix = _PROMPT_SUFFIX.get(pipeline_type, _DEFAULT_SUFFIX)
            optimized = f"{prompt}, {suffix}"
            if api_key:
                from . import tripo3d_runner
                obj_path = tripo3d_runner.generate_from_text(optimized, api_key, output_dir, _cb)
            else:
                _cb("no api key - local fallback")
                from . import image_gen_local
                img_path = os.path.join(output_dir, "reference.png")
                image_gen_local.generate(optimized, img_path, status_callback=_cb)
                from . import triposr_runner
                obj_path = triposr_runner.generate_from_image(img_path, output_dir, _cb)
            bpy.app.timers.register(lambda: _import_model(obj_path, apply_sculpt, pipeline_type, prompt, _cb), first_interval=0.1)
        except Exception as e:
            import traceback; traceback.print_exc(); _cb(f"error: {e}")
    threading.Thread(target=_worker, daemon=True).start()

def generate_from_image_path(image_path, pipeline_type="ANIMAL", apply_sculpt=False, status_callback=None):
    import threading
    def _cb(msg):
        if status_callback: status_callback(msg)
    def _worker():
        try:
            import tempfile
            output_dir = tempfile.mkdtemp(prefix="vaxis_imggen_")
            api_key = _get_api_key()
            if api_key:
                from . import tripo3d_runner
                obj_path = tripo3d_runner.generate_from_image(image_path, api_key, output_dir, _cb)
            else:
                _cb("no api key - local fallback")
                from . import triposr_runner
                obj_path = triposr_runner.generate_from_image(image_path, output_dir, _cb)
            bpy.app.timers.register(lambda: _import_model(obj_path, apply_sculpt, pipeline_type, "", _cb), first_interval=0.1)
        except Exception as e:
            import traceback; traceback.print_exc(); _cb(f"error: {e}")
    threading.Thread(target=_worker, daemon=True).start()
