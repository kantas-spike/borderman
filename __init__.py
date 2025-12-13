# BlenderのReload Scriptsによるモジュールリロード対応
if "bpy" not in locals():
    import bpy
    import importlib
    from . import shader_utils
    from . import utils
    from . import ops
else:
    # 最新のモジュールを再読み込み
    importlib.reload(shader_utils)
    importlib.reload(utils)
    importlib.reload(ops)


bl_info = {
    "name": "Borderman",
    "description": "Adds a border image strip.",
    "author": "kanta",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "VSE > Sidebar",
    "category": "Sequencer",
}


class BordermanProperties(bpy.types.PropertyGroup):
    """Groups all properties for this addon together."""

    image_dir: bpy.props.StringProperty(
        subtype="DIR_PATH", default="//borderman_imgs"
    )  # type: ignore
    placeholder_color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA", min=0, max=1.0, size=4, default=(0, 1.0, 0, 0.35)
    )  # type: ignore
    placeholder_channel_no: bpy.props.IntProperty(default=3, min=1, max=128)  # type: ignore
    placeholder_duration: bpy.props.IntProperty(default=30, min=10, max=600)  # type: ignore
    shape_type: bpy.props.EnumProperty(
        name="Shape",
        description="Type of shape",
        items=[("rectangle", "Rectangle", "四角形"), ("Ellipse", "Ellipse", "楕円")],
        default="rectangle",
    )  # type: ignore
    border_color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA", min=0, max=1.0, size=4, default=(1.0, 0, 0, 1)
    )  # type: ignore
    border_size: bpy.props.IntProperty(default=20, min=1, max=200)  # type: ignore
    corner_radius: bpy.props.IntProperty(default=0, min=0, max=200)  # type: ignore
    # Strip Naming Rule
    naming_rule: bpy.props.EnumProperty(
        name="NamingRule",
        description="rule",
        items=[("auto", "Auto", "自動"), ("prefix", "Prefix", "プレフィックス")],
        default="prefix",
    )  # type: ignore
    prefix: bpy.props.StringProperty(
        default="枠線_"
    )  # type: ignore


class MainPanel(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Borderman"
    bl_label = "Operations"
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
        layout.separator()

        layout.label(text="Adding Border:")
        box = layout.box()
        box.label(text="Options:")
        inner_box = box.box()
        inner_box.prop(props, "shape_type", text="Shape")

        inner_box.prop(props, "border_color", text="Border Color")
        inner_box.prop(props, "border_size", text="Border Size")
        if props.shape_type == "rectangle":
            inner_box.prop(props, "corner_radius", text="Corner Radius")
        box.separator(factor=0.1)
        box.operator(ops.ReplaceSelectedPlaceholdersToBorder.bl_idname)
        box.operator(ops.ReplaceAllPlaceholdersToBorder.bl_idname)

        layout.separator()
        layout.label(text="Maintenance:")
        box = layout.box()
        box.operator(ops.DeleteUnusedBorderImages.bl_idname)


class SettingsPanel(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Borderman"
    bl_label = "Settings"
    bl_idname = "BORDERMAN_PT_SettingsPanel"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def draw(self, context):
        props = context.scene.borderman_props
        layout = self.layout
        layout.prop(props, "image_dir", text="Image Dir")
        layout.separator(factor=0.2)
        layout.label(text="Placeholder:")
        box = layout.box()
        box.prop(props, "placeholder_color", text="Color")
        box.prop(props, "placeholder_channel_no", text="Channel No")
        box.prop(props, "placeholder_duration", text="Duration")
        layout.label(text="Strip Naming Rule:")
        box = layout.box()
        box.prop(props, "naming_rule", text="Naming Rule", expand=True)
        if props.naming_rule == "prefix":
            box.prop(props, "prefix", text="Prefix")


# アドオンで使用するために定義したクラス
class_list = ops.class_list + [BordermanProperties, MainPanel, SettingsPanel]


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
