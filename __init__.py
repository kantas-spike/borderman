import bpy

bl_info = {
    "name": "Borderman",
    "description": "Adds a border image strip.",
    "author": "kanta",
    "version": (0, 0, 1),
    "blender": (4, 4, 0),
    "location": "VSE > Sidebar",
    "category": "Sequencer",
}


class BordermanProperties(bpy.types.PropertyGroup):
    """Groups all properties for this addon together."""

    pass


# アドオンで使用するために定義したクラス
class_list = [BordermanProperties]


def register_props():
    bpy.types.Scene.borderman_props = bpy.props.PointerProperty(
        type=BordermanProperties
    )


def unregister_props():
    del bpy.types.Scene.borderman_props


def register():
    for cls in class_list:
        bpy.utils.register_class(cls)
    register_props()
    print(f"{bl_info['name']} has been activated")


def unregister():
    unregister_props()
    for cls in class_list:
        bpy.utils.unregister_class(cls)
    print(f"{bl_info['name']} has been deactivated")
