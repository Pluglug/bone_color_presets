import bpy
from bpy.types import AddonPreferences, UIList
from bpy.props import CollectionProperty, IntProperty, BoolProperty

from bl_ui.space_userpref import USERPREF_PT_theme_bone_color_sets

from . bone_color_sets import BCSPresets

from . addon import ADDON_ID, prefs, uprefs
from . debug_utils import Log, DBG_PREFS, DBG_JSON


class BoneColorSetsEditor(bpy.types.PropertyGroup):
    selected: BoolProperty(
        name="Selected",
        default=False
    )

    @classmethod
    def initialize(cls, theme):
        pr = prefs()
        pr.ed_bone_color_sets.clear()
        for i in range(len(theme.bone_color_sets)):
            pr.ed_bone_color_sets.add()

    # @property
    # def theme_bone_color_set(self):
    #     """Access the corresponding bone color set in the theme."""
    #     theme = uprefs().themes[0]
    #     index = prefs().ed_bone_color_sets.find(self)  # ?
    #     return theme.bone_color_sets[index] if index >= 0 else None
    
    @classmethod
    def get_selected(cls, theme):
        ed_bcs = prefs().ed_bone_color_sets
        bl_bcs = theme.bone_color_sets
        if len(ed_bcs) != len(bl_bcs):
            raise ValueError("Bone color sets do not match")

        selected = []
        for ed, bl in zip(ed_bcs, bl_bcs):
            if ed.selected:
                selected.append(bl)
        return selected

    @classmethod
    def set_all_selected(cls, value):
        for ed in prefs().ed_bone_color_sets:
            ed.selected = value


class BONECOLOR_OT_EditValue(bpy.types.Operator):
    bl_idname = "bonecolor.edit_value"
    bl_label = "Edit Value"
    bl_description = "Edit the value of the selected bone color set"
    bl_options = {'REGISTER', 'UNDO'}

    target_color: bpy.props.EnumProperty(
        name="Target Color",
        items=(
            ("NORMAL", "Normal", "Edit the normal color"),
            ("SELECT", "Select", "Edit the select color"),
            ("ACTIVE", "Active", "Edit the active color"),
        )
    )
    target_value: bpy.props.EnumProperty(
        name="Target Value",
        items=(
            ("HUE", "Hue", "Edit the hue value"),
            ("SATURATION", "Saturation", "Edit the saturation value"),
            ("VALUE", "Value", "Edit the value value"),
        )
    )
    direction: bpy.props.EnumProperty(
        name="Direction",
        items=(
            ("UP", "Up", "Increase the value"),
            ("DOWN", "Down", "Decrease the value"),
        )
    )
    step: bpy.props.FloatProperty(
        name="Step",
        default=0.05,
    )

    @classmethod
    def poll(cls, context):
        return len(BoneColorSetsEditor.get_selected(uprefs().themes[0])) > 0

    def execute(self, context):
        theme = uprefs(context).themes[0]
        val_index = ("HUE", "SATURATION", "VALUE").index(self.target_value)
        direction = 1 if self.direction == "UP" else -1
        value = direction * self.step

        for s in BoneColorSetsEditor.get_selected(theme):
            trg = getattr(s, self.target_color.lower())
            # Retrieve the current HSV values
            current_hsv = list(trg.hsv)  # Convert tuple to list to modify it

            # Modify the targeted value
            new_value = current_hsv[val_index] + value

            # Handling the specific case for 'HUE' which should wrap around
            if self.target_value == "HUE":
                new_value = new_value % 1.0
            else:
                # Ensure that saturation and value stay within the range 0.0 to 1.0
                new_value = max(0.0, min(1.0, new_value))

            # Update the hue, saturation, or value
            current_hsv[val_index] = new_value

            # Convert the list back to a tuple and update the color
            trg.hsv = tuple(current_hsv)

        return {'FINISHED'}


class BONECOLOR_OT_SelectAll(bpy.types.Operator):
    bl_idname = "bonecolor.select_all"
    bl_label = "Select All"
    bl_description = "Select all bone color sets"
    bl_options = {'INTERNAL'}

    value: bpy.props.BoolProperty(
        name="Value",
        default=True
    )

    def execute(self, context):
        BoneColorSetsEditor.set_all_selected(self.value)
        return {'FINISHED'}


class BCSPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    bcs_presets: CollectionProperty(type=BCSPresets)
    active_bcs_preset_index: IntProperty(default=0)

    ed_bone_color_sets : CollectionProperty(type=BoneColorSetsEditor)
    target_color: bpy.props.EnumProperty(
        name="Target Color",
        items=(
            ("NORMAL", "Normal", "Edit the normal color"),
            ("SELECT", "Select", "Edit the select color"),
            ("ACTIVE", "Active", "Edit the active color"),
        ),
    )


class BONECOLOR_UL_presets_bone_color_sets(UIList):
    def draw_item(self, context, layout, data, item, 
                  icon, active_data, active_propname, index):
        # item: BCSPresets
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="")


class BoneColorPresetsUI:
    def __init__(self):
        self.original_draw = None

    def draw_presets(self, context, layout):
        pr = prefs(context)

        # layout = self.layout
        layout.use_property_split = False 
        box = layout.box()

        box.label(text="Bone Color Presets", icon='PRESET_NEW')

        box.template_list("BONECOLOR_UL_presets_bone_color_sets", "", 
                             pr, "bcs_presets", pr, "active_bcs_preset_index")

        row = box.row()
        row.operator("bonecolor.save_preset", icon='EXPORT', text="Save Preset")

        if pr.active_bcs_preset_index >= 0:
            row.operator("bonecolor.remove_preset", icon='TRASH', text="Remove Preset")
            row.operator("bonecolor.load_preset", icon='IMPORT', text="Load Preset")

        subrow = box.row()
        subrow.operator("bonecolor.export_preset", icon='EXPORT', text="Export Presets")
        subrow.operator("bonecolor.import_preset", icon='IMPORT', text="Import Presets")

        layout.separator()

        self.draw_color_sets(context, layout)
    
    def draw_color_sets(self, context, layout):
        theme = context.preferences.themes[0]
        pr = prefs(context)

        layout.label(text="Edit Bone Color Sets", icon='COLOR')

        row = layout.row()
        row.label(text="Target Color:")
        row.prop(pr, "target_color", expand=True)

        ed_row = layout.row()

        ed_cb_row = ed_row.row(align=True)
        ed_cb_row.operator("bonecolor.select_all", text="", icon='CHECKBOX_HLT').value = True
        ed_cb_row.operator("bonecolor.select_all", text="", icon='CHECKBOX_DEHLT').value = False

        ed_hue_row = ed_row.row(align=True)
        ops = ed_hue_row.operator("bonecolor.edit_value", text="Hue +", icon='TRIA_UP')
        ops.target_color = pr.target_color
        ops.target_value = "HUE"
        ops.direction = "UP"

        ops = ed_hue_row.operator("bonecolor.edit_value", text="Hue -", icon='TRIA_DOWN')
        ops.target_color = pr.target_color
        ops.target_value = "HUE"
        ops.direction = "DOWN"

        ed_sat_row = ed_row.row(align=True)
        ops = ed_sat_row.operator("bonecolor.edit_value", text="Sat +", icon='TRIA_UP')
        ops.target_color = pr.target_color
        ops.target_value = "SATURATION"
        ops.direction = "UP"

        ops = ed_sat_row.operator("bonecolor.edit_value", text="Sat -", icon='TRIA_DOWN')
        ops.target_color = pr.target_color
        ops.target_value = "SATURATION"
        ops.direction = "DOWN"

        ed_val_row = ed_row.row(align=True)
        ops = ed_val_row.operator("bonecolor.edit_value", text="Val +", icon='TRIA_UP')
        ops.target_color = pr.target_color
        ops.target_value = "VALUE"
        ops.direction = "UP"

        ops = ed_val_row.operator("bonecolor.edit_value", text="Val -", icon='TRIA_DOWN')
        ops.target_color = pr.target_color
        ops.target_value = "VALUE"
        ops.direction = "DOWN"

        layout.separator()
               

        for i, (ui, ed) in enumerate(zip(theme.bone_color_sets, pr.ed_bone_color_sets), 1):
            row = layout.row(align=True)
            
            row.prop(ed, "selected", text=f"Set {i}")

            row.prop(ui, "normal", text="")
            row.prop(ui, "select", text="")
            row.prop(ui, "active", text="")
            row.separator()
            row.prop(ui, "show_colored_constraints", text="", icon='CONSTRAINT_BONE', toggle=True)

    def ui_register(self):
        self.original_draw = USERPREF_PT_theme_bone_color_sets.draw_centered
        USERPREF_PT_theme_bone_color_sets.draw_centered = self.draw_presets
    
    def ui_unregister(self):
        USERPREF_PT_theme_bone_color_sets.draw_centered = self.original_draw


bone_color_presets_ui = BoneColorPresetsUI()


classes = (
    BoneColorSetsEditor,
    BONECOLOR_OT_EditValue,
    BONECOLOR_OT_SelectAll,
    BONECOLOR_UL_presets_bone_color_sets,
    BCSPreferences,
)   


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    BoneColorSetsEditor.initialize(uprefs().themes[0])

    bone_color_presets_ui.ui_register()


def unregister():
    bone_color_presets_ui.ui_unregister()

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)