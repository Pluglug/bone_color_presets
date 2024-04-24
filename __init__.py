bl_info = {
    "name": "Bone Color Presets",
    "description": "Addon to save and load custom bone color presets.",
    "author": "Pluglug",
    "version": (0, 0, 3),
    "blender": (2, 9, 0),
    "location": "Preferences > Themes > Bone Color Sets",
    "warning": "This addon is still in development.",
    "wiki_url": "",
    "category": "Preferences",
}


# use_reload = "addon" in locals()
# if use_reload:
#     import importlib
#     importlib.reload(locals()["addon"])
#     del importlib

use_reload = "bpy" in locals()
if use_reload:
    from importlib import reload
    import sys
    for k, v in list(sys.modules.items()):
        if k.startswith('bone_color_presets'):
            reload(v)

from . import addon
addon.init_addon(
    use_reload=use_reload,
)


def register():
    addon.register_modules()


def unregister():
    addon.unregister_modules()
