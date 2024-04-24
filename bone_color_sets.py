import bpy
from bpy.types import PropertyGroup, UIList, Operator
from bpy.props import (
    FloatVectorProperty,
    BoolProperty,
    IntProperty,
    StringProperty,
    CollectionProperty,
)

from . addon import get_addon_preferences, get_user_preferences
from . debug_utils import Log, DBG_OPS, DBG_JSON

import json


class CustomBoneColorSet(PropertyGroup):
    normal: FloatVectorProperty(
        name="Normal",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        description="Color for normal state"
    )
    select: FloatVectorProperty(
        name="Select",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        description="Color for selected state"
    )
    active: FloatVectorProperty(
        name="Active",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        description="Color for active state"
    )
    show_colored_constraints: BoolProperty(
        name="Show Colored Constraints",
        description="Whether to show constraints with color",
        default=False
    )

    def copy_from(self, other):
        """Copy color settings from another CustomBoneColorSet."""
        self.normal = other.normal[:]
        self.select = other.select[:]
        self.active = other.active[:]
        self.show_colored_constraints = other.show_colored_constraints
    
    def copy_to(self, other):
        """Copy color settings to another CustomBoneColorSet."""
        other.normal = self.normal[:]
        other.select = self.select[:]
        other.active = self.active[:]
        other.show_colored_constraints = self.show_colored_constraints

    def as_dict(self):
        return {
            "normal": self.normal[:],
            "select": self.select[:],
            "active": self.active[:],
            "show_colored_constraints": self.show_colored_constraints
        }
    
    def from_dict(self, data):
        self.normal = data["normal"]
        self.select = data["select"]
        self.active = data["active"]
        self.show_colored_constraints = data["show_colored_constraints"]


class CustomBoneColorSets(PropertyGroup):
    color_sets: CollectionProperty(type=CustomBoneColorSet)
    name: StringProperty(default="Custom Bone Color Sets")

    def add_color_sets(self, theme):
        """Add a new color set preset and initialize it from the given theme."""
        self.name = f"Preset {len(self.color_sets) + 1}"
        for theme_set in theme.bone_color_sets:
            preset_set = self.color_sets.add()
            preset_set.copy_from(theme_set)
        return self

    def restore_color_sets(self, theme):
        """Restore the given preset to the theme."""
        for theme_set, preset_set in zip(theme.bone_color_sets, self.color_sets):
            preset_set.copy_to(theme_set)

    def save_to_file(self, filepath):
        """Save presets to a file."""
        import json
        data = [cs.as_dict() for cs in self.color_sets]
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load_from_file(self, filepath):
        """Load presets from a file."""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        for cs_data in data:
            cs = self.color_sets.add()
            cs.from_dict(cs_data)


class BONECOLOR_OT_save_preset(Operator):
    """Save the current bone color settings as a new preset"""
    bl_idname = "bonecolor.save_preset"
    bl_label = "Save Bone Color Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        theme = get_user_preferences(context).themes[0]
        return hasattr(theme, "bone_color_sets")

    def execute(self, context):
        try:
            return self.save_preset(context)
        except Exception as e:
            Log.error(f"Failed to save new bone color preset: {e}")
            self.report({'ERROR'}, f"Failed to save new bone color preset: {e}")
            return {'CANCELLED'}

    def save_preset(self, context):
        theme = get_user_preferences(context).themes[0]
        pr = get_addon_preferences(context)
        
        new_preset = pr.bcs_presets.add()
        new_preset.add_color_sets(theme)

        pr.active_bcs_preset_index = len(pr.bcs_presets) - 1

        self.report({'INFO'}, f"New bone color preset saved: {new_preset.name}")
        return {'FINISHED'}


class BONECOLOR_OT_load_preset(Operator):
    """Load the selected bone color preset"""
    bl_idname = "bonecolor.load_preset"
    bl_label = "Load Bone Color Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return prefs.active_bcs_preset_index >= 0

    def execute(self, context):
        try:
            return self.load_preset(context)
        except Exception as e:
            Log.error(f"Failed to load bone color preset: {e}")
            self.report({'ERROR'}, f"Failed to load bone color preset: {e}")
            return {'CANCELLED'}

    def load_preset(self, context):
        theme = get_user_preferences(context).themes[0]
        pr = get_addon_preferences(context)

        source_preset = pr.bcs_presets[pr.active_bcs_preset_index]
        source_preset.restore_color_sets(theme)

        self.report({'INFO'}, f"Loaded bone color preset: {source_preset.name}")
        return {'FINISHED'}
    

class BONECOLOR_OT_remove_preset(Operator):
    """Remove the selected bone color preset"""
    bl_idname = "bonecolor.remove_preset"
    bl_label = "Remove Bone Color Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return prefs.active_bcs_preset_index >= 0

    def execute(self, context):
        try:
            return self.remove_preset(context)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to remove bone color preset: {e}")
            return {'CANCELLED'}

    def remove_preset(self, context):
        pr = get_addon_preferences(context)
        
        pr.bcs_presets.remove(pr.active_bcs_preset_index)
    

class BONECOLOR_OT_save_to_file(Operator):
    """Save presets to a file"""
    bl_idname = "bonecolor.save_to_file"
    bl_label = "Save Presets to File"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        subtype='FILE_PATH',
    )

    def execute(self, context):
        try:
            return self.save_to_file(context)
        except Exception as e:
            Log.error(f"Failed to save presets to file: {e}")
            self.report({'ERROR'}, f"Failed to save presets to file: {e}")
            return {'CANCELLED'}

    def save_to_file(self, context):
        pr = get_addon_preferences(context)
        pr.bcs_presets.save_to_file(self.filepath)
        self.report({'INFO'}, f"Saved presets to file: {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BONECOLOR_OT_load_from_file(Operator):
    """Load presets from a file"""
    bl_idname = "bonecolor.load_from_file"
    bl_label = "Load Presets from File"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        subtype='FILE_PATH',
    )

    def execute(self, context):
        try:
            return self.load_from_file(context)
        except Exception as e:
            Log.error(f"Failed to load presets from file: {e}")
            self.report({'ERROR'}, f"Failed to load presets from file: {e}")
            return {'CANCELLED'}

    def load_from_file(self, context):
        pr = get_addon_preferences(context)
        pr.bcs_presets.load_from_file(self.filepath)
        self.report({'INFO'}, f"Loaded presets from file: {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    CustomBoneColorSet,
    CustomBoneColorSets,
    BONECOLOR_OT_save_preset,
    BONECOLOR_OT_load_preset,
    BONECOLOR_OT_remove_preset,
    BONECOLOR_OT_save_to_file,
    BONECOLOR_OT_load_from_file,
)

register, unregister = bpy.utils.register_classes_factory(classes)
