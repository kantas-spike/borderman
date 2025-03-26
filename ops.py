import bpy
from bpy.types import Context, Event
import datetime

from . import utils

DEFAULT_PLACEHOLDER_DURATION = 30
DEFAULT_PLACEHOLDER_CHANNEL_NO = 3
CUSTOM_KEY_GENERATER = "generated_by"
CUSTOM_KEY_STRIP_TYPE = "strip_type"
CUSTOM_KEY_PLACEHOLDER_ID = "placeholder_id"
ADDON_NAME = "borderman"
STRIP_TYPE_PLACEHOLDER = "placeholder"
STRIP_TYPE_BORDER = "border"


def is_placeholder(strip: bpy.types.Strip):
    if (
        strip.get(CUSTOM_KEY_GENERATER) == ADDON_NAME
        and strip.get(CUSTOM_KEY_STRIP_TYPE) == STRIP_TYPE_PLACEHOLDER
    ):
        return True
    else:
        return False


def is_addon_generated(strip: bpy.types.Strip):
    if strip.get(CUSTOM_KEY_GENERATER) == ADDON_NAME:
        return True
    else:
        return False


class AddPlaceholder(bpy.types.Operator):
    bl_idname = "borderman.add_placeholder"
    bl_label = "Add a placeholder"
    bl_description = "Add a placeholder representing a border strip size."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        cur_frame = bpy.context.scene.frame_current
        seqs = bpy.context.scene.sequence_editor.strips
        frame_end = cur_frame + DEFAULT_PLACEHOLDER_DURATION

        target_channel = utils.guess_available_channel(
            cur_frame, frame_end, DEFAULT_PLACEHOLDER_CHANNEL_NO, seqs
        )

        placeholder_strip: bpy.types.ColorStrip = seqs.new_effect(
            name=f"placeholder_{datetime.datetime.now().timestamp()}",
            type="COLOR",
            frame_start=cur_frame,
            frame_end=frame_end,
            channel=target_channel,
        )
        placeholder_strip.transform.scale_x = 0.2
        placeholder_strip.transform.scale_y = 0.3
        placeholder_strip.transform.origin[0] = 0
        placeholder_strip.transform.origin[1] = 1.0
        utils.move_center(placeholder_strip)
        placeholder_strip.color = (0, 1, 0)
        placeholder_strip.blend_alpha = 0.35
        placeholder_strip[CUSTOM_KEY_GENERATER] = ADDON_NAME
        placeholder_strip[CUSTOM_KEY_STRIP_TYPE] = STRIP_TYPE_PLACEHOLDER
        placeholder_strip[CUSTOM_KEY_PLACEHOLDER_ID] = placeholder_strip.name

        bpy.ops.sequencer.select_all(action="DESELECT")
        context.scene.sequence_editor.active_strip = placeholder_strip

        return {"FINISHED"}


class ReplacePlaceholdersToBorder(bpy.types.Operator):
    _timer = None

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def get_target_placeholders(self, context: Context):
        return []

    def modal(self, context: Context, event: Event):
        if event.type == "TIMER":
            context.window_manager.event_timer_remove(self._timer)
            selected_placeholders = self.get_target_placeholders(context)
            bpy.ops.sequencer.select_all(action="DESELECT")
            ret = add_border_strip(context, selected_placeholders)
            self._timer = None
            return ret
        else:
            return {"RUNNING_MODAL"}

    def invoke(self, context: Context, event: Event):
        if self._timer:
            self.report({"WARNING"}, "処理中のためキャンセル")
            return {"CANCELLED"}
        self.report({"INFO"}, "処理中...")
        self._timer = context.window_manager.event_timer_add(1.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


class ReplaceSelectedPlaceholdersToBorder(ReplacePlaceholdersToBorder):
    bl_idname = "borderman.replace_selected_placeholders"
    bl_label = "Replace selected placeholders"
    bl_description = "Replace selected placeholders to border strip."
    bl_options = {"REGISTER", "UNDO"}

    def get_target_placeholders(self, context: Context):
        return [strip for strip in context.selected_strips if is_placeholder(strip)]


class ReplaceAllPlaceholdersToBorder(ReplacePlaceholdersToBorder):
    bl_idname = "borderman.replace_all_placeholders"
    bl_label = "Replace all placeholders"
    bl_description = "Replace all placeholders to border strip."
    bl_options = {"REGISTER", "UNDO"}

    def get_target_placeholders(self, context: Context):
        return [strip for strip in context.strips if is_placeholder(strip)]


def add_border_strip(context, target_strip_list):
    utils.showMessageBox(message=f"add border strip!!: {len(target_strip_list)}")
    for strip in target_strip_list:
        rect = utils.get_strip_info(strip)
        print(rect)
    return {"CANCELLED"}


class_list = [
    AddPlaceholder,
    ReplaceSelectedPlaceholdersToBorder,
    ReplaceAllPlaceholdersToBorder,
]
