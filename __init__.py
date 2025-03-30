if "bpy" not in locals():
    import bpy
    from . import ops
else:
    import importlib

    importlib.reload(ops)

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

    image_dir: bpy.props.StringProperty(
        subtype="DIR_PATH", default="//borderman_imgs"
    )  # type: ignore
    shape_type: bpy.props.EnumProperty(
        name="Shape",
        description="Type of shape",
        items=[("rectangle", "Rectangle", "四角形"), ("Ellipse", "Ellipse", "楕円")],
        default="rectangle",
    )  # type: ignore
    border_color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA", min=0, max=1.0, size=4, default=(1.0, 0, 0, 1)
    )  # type: ignore
    border_size: bpy.props.IntProperty(default=10, min=0, max=100)  # type: ignore
    corner_radius: bpy.props.IntProperty(default=0, min=0, max=100)  # type: ignore


class MainPanel(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Borderman"
    bl_label = "Borderman"
    bl_idname = "BORDERMAN_PT_MainPanel"

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def draw(self, context):
        props = context.scene.borderman_props
        layout = self.layout

        layout.label(text="Placeholder:")
        box = layout.box()
        box.operator(ops.AddPlaceholder.bl_idname)

        layout.label(text="Adding Border:")
        box = layout.box()
        box.prop(props, "shape_type", text="Shape")

        box.prop(props, "border_color", text="Border Color")
        box.prop(props, "border_size", text="Border Size")
        if props.shape_type == "rectangle":
            box.prop(props, "corner_radius", text="Corner Radius")
        layout.separator()

        box = layout.box()
        box.operator(ops.ReplaceSelectedPlaceholdersToBorder.bl_idname)
        box.operator(ops.ReplaceAllPlaceholdersToBorder.bl_idname)


# アドオンで使用するために定義したクラス
class_list = ops.class_list + [BordermanProperties, MainPanel]


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
