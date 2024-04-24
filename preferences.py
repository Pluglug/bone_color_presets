import bpy
from bpy.types import AddonPreferences, UIList
from bpy.props import CollectionProperty, IntProperty

from bl_ui.space_userpref import USERPREF_PT_theme_bone_color_sets

from . bone_color_sets import CustomBoneColorSets

from . addon import ADDON_ID, get_addon_preferences
from . debug_utils import Log, DBG_PREFS


class BCSPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    bcs_presets: CollectionProperty(type=CustomBoneColorSets)
    active_bcs_preset_index: IntProperty(default=0)


class BONECOLOR_UL_presets_bone_color_sets(UIList):
    def draw_item(self, context, layout, data, item, 
                  icon, active_data, active_propname, index):
        # item: CustomBoneColorSets
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="")


def _draw_presets(self, context):
    prefs = get_addon_preferences(context)

    layout = self.layout
    box = layout.box()

    box.label(text="Bone Color Presets", icon='PRESET_NEW')

    box.template_list("BONECOLOR_UL_presets_bone_color_sets", "", 
                         prefs, "bcs_presets", prefs, "active_bcs_preset_index")

    row = box.row()
    row.operator("bonecolor.save_preset", icon='EXPORT', text="Save Preset")

    if prefs.active_bcs_preset_index >= 0:
        row.operator("bonecolor.remove_preset", icon='TRASH', text="Remove Preset")
        row.operator("bonecolor.load_preset", icon='IMPORT', text="Load Preset")

    layout.separator()


def register():
    bpy.utils.register_class(BONECOLOR_UL_presets_bone_color_sets)
    bpy.utils.register_class(BCSPreferences)

    USERPREF_PT_theme_bone_color_sets.prepend(_draw_presets)


def unregister():
    USERPREF_PT_theme_bone_color_sets.remove(_draw_presets)

    bpy.utils.unregister_class(BCSPreferences)
    bpy.utils.unregister_class(BONECOLOR_UL_presets_bone_color_sets)
