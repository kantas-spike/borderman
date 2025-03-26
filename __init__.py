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


def register():
    print(f"{bl_info['name']} has been activated")


def unregister():
    print(f"{bl_info['name']} has been deactivated")
