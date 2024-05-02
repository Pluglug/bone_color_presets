import bpy
import importlib
import os
import sys

from . debug_utils import Log, DBG_INIT


BACK_GROUND = False
ADDON_VERSION = (0, 0, 0)
ADDON_ID = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
ADDON_PATH = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
ICON_ENUM_ITEMS = bpy.types.UILayout.bl_rna.functions[
    "prop"].parameters["icon"].enum_items

SINCE_4_0_0 = bpy.app.version >= (4, 0, 0)


def uprefs(context=bpy.context):
    """Get User Preferences."""
    preferences = getattr(context, "preferences", None)
    if preferences is not None:
        return preferences
    else:
        raise AttributeError("Unable to access preferences")


def prefs(context=bpy.context):
    """Get Addon Preferences."""
    user_prefs = uprefs(context)
    addon_prefs = user_prefs.addons.get(ADDON_ID)
    if addon_prefs is not None:
        return addon_prefs.preferences
    else:
        raise KeyError(f"Addon '{ADDON_ID}' not found. Ensure it is installed and enabled.")


def init_addon(
        # module_names, 
        use_reload=False, 
    ):
    DBG_INIT and Log.info(f"Initializing {ADDON_ID}...")
    global ADDON_VERSION, BACK_GROUND

    module = sys.modules[ADDON_ID]
    ADDON_VERSION = module.bl_info.get("version", ADDON_VERSION)

    if not BACK_GROUND and bpy.app.background:
        return

    def get_module_names(path=ADDON_PATH, package_name=ADDON_ID):
        """Get the names of all modules in the package."""
        pass


modules = [
    "bone_color_sets",
    "preferences",
]


def register_modules():
    if not BACK_GROUND and bpy.app.background:
        return
    
    DBG_INIT and Log.header(f"Registering modules in {ADDON_ID}.", title="BONE COLOR PRESETS")

    for module_name in modules:
        module = importlib.import_module(f".{module_name}", package=ADDON_ID)
        if hasattr(module, "register"):
            DBG_INIT and Log.info(f"  Registering {module_name}.")
            module.register()
    
    DBG_INIT and Log.footer("Modules registered.")


def unregister_modules():
    if not BACK_GROUND and bpy.app.background:
        return
    
    DBG_INIT and Log.header(f"Unregistering modules in {ADDON_ID}.", title="BONE COLOR PRESETS")

    for module_name in reversed(modules):
        module = importlib.import_module(f".{module_name}", package=ADDON_ID)
        if hasattr(module, "unregister"):
            DBG_INIT and Log.info(f"  Unregistering {module_name}.")
            module.unregister()

    DBG_INIT and Log.footer("Modules unregistered.")
