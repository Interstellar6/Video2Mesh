#!/usr/bin/env python3
"""Load a Video2Mesh export run into Blender.

Usage:
    blender --python tools/open_export_in_blender.py -- exports/milscene2_real_demo
    blender --background --python tools/open_export_in_blender.py -- exports/milscene2_real_demo --save exports/milscene2_real_demo/video2mesh_scene.blend
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Open a Video2Mesh export in Blender.")
    parser.add_argument("export_dir", help="Path such as exports/milscene2_real_demo")
    parser.add_argument("--save", help="Optional .blend path to save after importing")
    parser.add_argument("--no-scene", action="store_true", help="Skip scene-level PLY files")
    parser.add_argument("--no-objects", action="store_true", help="Skip object OBJ meshes")
    parser.add_argument("--no-masks", action="store_true", help="Skip object 3D mask PLY files")
    parser.add_argument("--keep-existing", action="store_true", help="Do not clear the current scene first")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def project_root_from_export(export_dir: Path) -> Path:
    for parent in [export_dir, *export_dir.parents]:
        if parent.name == "exports":
            return parent.parent
    return export_dir.parent


def resolve_path(raw_path: object, export_dir: Path, project_root: Path) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None

    path = Path(raw_path)
    candidates = []
    if path.is_absolute():
        candidates.append(path)
        parts = path.parts
        if "exports" in parts:
            exports_index = parts.index("exports")
            candidates.append(project_root.joinpath(*parts[exports_index:]))
    else:
        candidates.extend([project_root / path, export_dir / path])

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0] if candidates else None


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def collection(name: str) -> bpy.types.Collection:
    existing = bpy.data.collections.get(name)
    if existing:
        return existing
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to_collection(obj: bpy.types.Object, coll: bpy.types.Collection) -> None:
    if obj.name not in coll.objects:
        coll.objects.link(obj)
    for existing in list(obj.users_collection):
        if existing != coll:
            existing.objects.unlink(obj)


def material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    return mat


def imported_objects_after(operation) -> list[bpy.types.Object]:
    before = {obj.name for obj in bpy.data.objects}
    operation()
    return [obj for obj in bpy.context.selected_objects if obj.name not in before]


def import_obj(path: Path) -> list[bpy.types.Object]:
    def operation() -> None:
        if hasattr(bpy.ops.wm, "obj_import"):
            bpy.ops.wm.obj_import(filepath=str(path))
        else:
            bpy.ops.import_scene.obj(filepath=str(path))

    return imported_objects_after(operation)


def import_ply(path: Path) -> list[bpy.types.Object]:
    def operation() -> None:
        if hasattr(bpy.ops.wm, "ply_import"):
            bpy.ops.wm.ply_import(filepath=str(path))
        else:
            bpy.ops.import_mesh.ply(filepath=str(path))

    return imported_objects_after(operation)


def color_from_id(identifier: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    seed = sum((index + 1) * ord(char) for index, char in enumerate(identifier))
    hue = (seed % 360) / 360.0
    chroma = 0.65
    x = chroma * (1 - abs((hue * 6) % 2 - 1))
    sector = int(hue * 6) % 6
    base = [
        (chroma, x, 0),
        (x, chroma, 0),
        (0, chroma, x),
        (0, x, chroma),
        (x, 0, chroma),
        (chroma, 0, x),
    ][sector]
    m = 0.85 - chroma
    return (base[0] + m, base[1] + m, base[2] + m, alpha)


def apply_pose(obj: bpy.types.Object, pose: dict) -> None:
    position = pose.get("position")
    rotation_xyzw = pose.get("rotation_xyzw")
    scale = pose.get("scale")

    if isinstance(position, list) and len(position) == 3:
        obj.location = tuple(float(v) for v in position)

    if isinstance(rotation_xyzw, list) and len(rotation_xyzw) == 4:
        x, y, z, w = (float(v) for v in rotation_xyzw)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Quaternion((w, x, y, z))

    if isinstance(scale, list) and len(scale) == 3:
        obj.scale = tuple(float(v) for v in scale)
    elif isinstance(scale, (int, float)) and math.isfinite(float(scale)):
        obj.scale = (float(scale), float(scale), float(scale))


def set_viewport_display(obj: bpy.types.Object, color: tuple[float, float, float, float]) -> None:
    obj.color = color
    obj.show_name = True
    obj.show_in_front = True
    if obj.type == "MESH" and not obj.data.polygons:
        obj.display_type = "WIRE"


def load_scene_clouds(export_dir: Path, project_root: Path) -> None:
    bundle = load_json(export_dir / "simulator_assets" / "simulator_asset_bundle.json")
    scene_assets = bundle.get("scene_assets", {})
    paths = [
        scene_assets.get("point_cloud"),
        scene_assets.get("semantic_splats_ply"),
        str(export_dir / "simulator_assets" / "semantic_preview" / "semantic_splats_colored.ply"),
        str(export_dir / "simulator_assets" / "semantic_splats.ply"),
        str(export_dir / "scene" / "reconstruction" / "point_cloud.ply"),
    ]

    coll = collection("Scene clouds")
    seen = set()
    for raw_path in paths:
        path = resolve_path(raw_path, export_dir, project_root)
        if not path or not path.exists() or path in seen:
            continue
        seen.add(path)
        imported = import_ply(path)
        for obj in imported:
            obj.name = path.stem
            move_to_collection(obj, coll)
            set_viewport_display(obj, (0.65, 0.7, 0.75, 1.0))


def object_items(export_dir: Path) -> list[tuple[str, dict]]:
    bundle = load_json(export_dir / "simulator_assets" / "simulator_asset_bundle.json")
    objects = bundle.get("objects")
    if objects:
        if isinstance(objects, list):
            return [(obj.get("object_id", f"object_{i:03d}"), obj) for i, obj in enumerate(objects)]
        if isinstance(objects, dict):
            return list(objects.items())

    data = load_json(export_dir / "simulator_assets" / "object_meshes.json")
    objects = data.get("objects", {})
    if isinstance(objects, list):
        return [(obj.get("object_id", f"object_{i:03d}"), obj) for i, obj in enumerate(objects)]
    if isinstance(objects, dict):
        return list(objects.items())
    return []


def mesh_paths(obj_data: dict, export_dir: Path, project_root: Path) -> tuple[Path | None, Path | None]:
    mesh = obj_data.get("mesh", {})
    mesh_path = resolve_path(mesh.get("path"), export_dir, project_root)
    source_path = resolve_path(mesh.get("source_path"), export_dir, project_root)
    asset_path = resolve_path(obj_data.get("asset_path"), export_dir, project_root)
    source_mesh = resolve_path(obj_data.get("source_mesh"), export_dir, project_root)
    return (mesh_path or asset_path, source_path or source_mesh)


def mask_path(object_id: str, obj_data: dict, export_dir: Path, project_root: Path) -> Path | None:
    masks = obj_data.get("masks", {})
    mask_cloud = masks.get("mask_3d_cloud", {}) if isinstance(masks, dict) else {}
    manifest_path = resolve_path(mask_cloud.get("path"), export_dir, project_root)
    generated_path = resolve_path(obj_data.get("source_mask_cloud"), export_dir, project_root)
    conventional_path = export_dir / "simulator_assets" / "object_masks_3d" / f"{object_id}.ply"
    return manifest_path or generated_path or conventional_path


def load_objects(export_dir: Path, project_root: Path, include_masks: bool) -> None:
    items = object_items(export_dir)
    if not items:
        return

    object_coll = collection("Object meshes")
    mask_coll = collection("Object mask clouds")

    for object_id, obj_data in items:
        if not isinstance(obj_data, dict):
            continue
        mesh_path, source_path = mesh_paths(obj_data, export_dir, project_root)
        path = mesh_path if mesh_path and mesh_path.exists() else source_path

        if path and path.exists():
            imported = import_obj(path)
            mat = material(f"{object_id}_material", color_from_id(object_id))
            for obj in imported:
                obj.name = object_id
                obj.data.materials.clear()
                obj.data.materials.append(mat)
                move_to_collection(obj, object_coll)
                set_viewport_display(obj, mat.diffuse_color)
                if path == mesh_path:
                    apply_pose(obj, obj_data.get("pose", {}))

        if include_masks:
            object_mask_path = mask_path(object_id, obj_data, export_dir, project_root)
            if object_mask_path and object_mask_path.exists():
                imported_masks = import_ply(object_mask_path)
                mask_color = color_from_id(f"{object_id}_mask", 0.55)
                for mask_obj in imported_masks:
                    mask_obj.name = f"{object_id}_mask"
                    move_to_collection(mask_obj, mask_coll)
                    set_viewport_display(mask_obj, mask_color)


def add_camera_and_light() -> None:
    bpy.ops.object.light_add(type="AREA", location=(0, -4, 5))
    light = bpy.context.object
    light.name = "Viewer area light"
    light.data.energy = 450
    light.data.size = 5

    bpy.ops.object.camera_add(location=(3, -5, 3), rotation=(math.radians(60), 0, math.radians(35)))
    bpy.context.scene.camera = bpy.context.object


def main() -> None:
    args = parse_args()
    export_dir = Path(args.export_dir).expanduser().resolve()
    if not export_dir.exists():
        raise FileNotFoundError(f"Export directory does not exist: {export_dir}")

    project_root = project_root_from_export(export_dir)
    if not args.keep_existing:
        clear_scene()

    if not args.no_scene:
        load_scene_clouds(export_dir, project_root)
    if not args.no_objects:
        load_objects(export_dir, project_root, include_masks=not args.no_masks)

    add_camera_and_light()
    bpy.context.scene.view_settings.view_transform = "Filmic"
    bpy.context.scene.view_settings.look = "Medium High Contrast"

    if args.save:
        save_path = Path(args.save).expanduser()
        if not save_path.is_absolute():
            save_path = project_root / save_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(save_path))
        print(f"Saved Blender scene: {save_path}")


if __name__ == "__main__":
    main()
