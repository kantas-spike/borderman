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


# アドオンで使用するために定義したクラス
class_list = []


def register_props():
    pass


def unregister_props():
    pass


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
