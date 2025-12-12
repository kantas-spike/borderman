import bpy
from bpy.types import Context, Event
import datetime
import glob
import os
import re
from . import utils


DEFAULT_PLACEHOLDER_DURATION = 30
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


def is_border_image(strip: bpy.types.Strip):
    if (
        strip.get(CUSTOM_KEY_GENERATER) == ADDON_NAME
        and strip.get(CUSTOM_KEY_STRIP_TYPE) == STRIP_TYPE_BORDER
    ):
        return True
    else:
        return False


def is_addon_generated(strip: bpy.types.Strip):
    if strip.get(CUSTOM_KEY_GENERATER) == ADDON_NAME:
        return True
    else:
        return False


def get_max_strip_no(context: bpy.types.Context, prefix):
    max_no = 0
    pattern = fr'\A{re.escape(prefix)}(\d+)(.png)?'
    for strip in context.scene.sequence_editor.strips_all:
        if not is_addon_generated(strip):
            continue
        strip_name = strip.name
        if not strip_name.startswith(prefix):
            continue
        # prefixあり
        m = re.match(pattern, strip_name)
        if not m:
            continue
        strip_no = int(m.group(1))
        max_no = max(max_no, strip_no)
    return max_no


def get_strip_name(context, props):
    if props.naming_rule == "auto":
        return f"placeholder_{datetime.datetime.now().timestamp()}"
    else:
        prefix = props.prefix
        strip_no = get_max_strip_no(context, prefix) + 1
        return f"{prefix}{strip_no:03}"


class AddPlaceholder(bpy.types.Operator):
    bl_idname = "borderman.add_placeholder"
    bl_label = "Add a placeholder"
    bl_description = "Add a placeholder representing a border strip size."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.borderman_props
        cur_frame = bpy.context.scene.frame_current
        seqs = bpy.context.scene.sequence_editor.strips
        frame_end = cur_frame + props.placeholder_duration

        target_channel = utils.guess_available_channel(
            cur_frame, frame_end, props.placeholder_channel_no, seqs
        )

        strip_name = get_strip_name(context, props)
        placeholder_strip: bpy.types.ColorStrip = seqs.new_effect(
            name=strip_name,
            type="COLOR",
            frame_start=cur_frame,
            length=props.placeholder_duration,
            channel=target_channel,
        )
        placeholder_strip.transform.scale_x = 0.2
        placeholder_strip.transform.scale_y = 0.3
        placeholder_strip.transform.origin[0] = 0
        placeholder_strip.transform.origin[1] = 1.0
        utils.move_center(placeholder_strip)
        placeholder_strip.color = props.placeholder_color[:3]
        placeholder_strip.blend_alpha = props.placeholder_color[-1]
        placeholder_strip[CUSTOM_KEY_GENERATER] = ADDON_NAME
        placeholder_strip[CUSTOM_KEY_STRIP_TYPE] = STRIP_TYPE_PLACEHOLDER
        placeholder_strip[CUSTOM_KEY_PLACEHOLDER_ID] = placeholder_strip.name

        bpy.ops.sequencer.select_all(action="DESELECT")
        context.scene.sequence_editor.active_strip = placeholder_strip

        return {"FINISHED"}


class DeleteUnusedBorderImages(bpy.types.Operator):
    bl_idname = "borderman.delete_unused_borderimages"
    bl_label = "Delete unused border images"
    bl_description = "Delete unused border images."
    bl_options = {"REGISTER", "UNDO"}

    def get_border_images(self, context: Context):
        results = []
        for strip in context.strips:
            if not is_border_image(strip):
                continue
            img_strip: bpy.types.ImageStrip = strip
            elm = img_strip.elements[0]
            if not elm:
                continue
            img_path = os.path.join(img_strip.directory, elm.filename)
            abs_img_path = bpy.path.abspath(img_path)
            results.append(abs_img_path)
        return results

    def delete_unused_border_iamges(self, context, image_dir):
        used_list = self.get_border_images(context)
        abs_image_dir = bpy.path.abspath(image_dir)
        path_pattern = os.path.join(abs_image_dir, "*.png")
        for img_path in glob.glob(path_pattern):
            if img_path not in used_list:
                print("remove unused image...", img_path)
                os.remove(img_path)
        return {"FINISHED"}

    def execute(self, context):
        props = context.scene.borderman_props
        if not props.image_dir:
            utils.showMessageBox(
                messages=self._messages_no_placeholder,
                title="枠線画像ファイルの保存ディレクトリが指定されていません。",
                icon="ERROR",
            )
            return {"CANCELLED"}
        image_dir = utils.normalize_image_dir(props.image_dir)
        if not image_dir:
            utils.showMessageBox(
                messages=self._messages_no_placeholder,
                title="枠線画像ファイルの保存ディレクトリが指定されていません。",
                icon="ERROR",
            )
        if not image_dir:
            utils.showMessageBox(
                messages=self._messages_no_placeholder,
                title="プロジェクトを保存してから実行してください。",
                icon="ERROR",
            )
            return {"CANCELLED"}
        if not os.path.exists(image_dir):
            utils.showMessageBox(
                messages=self._messages_no_placeholder,
                title="枠線画像ファイルの保存ディレクトリが存在しません。",
                icon="ERROR",
            )
            return {"CANCELLED"}

        return self.delete_unused_border_iamges(context, image_dir)


class ReplacePlaceholdersToBorder(bpy.types.Operator):
    _timer = None
    _messages_no_placeholder = ("",)

    @classmethod
    def poll(cls, context):
        return context.space_data.view_type == "SEQUENCER"

    def get_target_placeholders(self, context: Context):
        return []

    def add_border_strip(
        self,
        context: Context,
        target_strip_list,
        image_dir,
        shape_type,
        border_color,
        border_size,
        corner_radius,
    ):
        screen_rect = utils.get_screen_rect()
        for strip in target_strip_list:
            rect = utils.get_placeholder_info(strip)
            img_strip = utils.create_border_strip(
                strip,
                image_dir,
                shape_type,
                border_size,
                border_color,
                corner_radius,
            )
            strip_center = (rect.x + (rect.w / 2), rect.y - (rect.h / 2))
            # スクリーンの中央を取得
            #    image stripはスクリーンの中央が基準のようなので..
            screen_center = (screen_rect.w / 2, -1 * screen_rect.h / 2)
            # placeholder stripと追加したimage stripの位置の差を取得
            diff_center = (
                round(strip_center[0] - screen_center[0]),
                round(strip_center[1] - screen_center[1]),
            )
            # image stripの中心をplaceholder stripの中心に移動
            img_strip.transform.offset_x = diff_center[0]
            img_strip.transform.offset_y = diff_center[1]
            # image stripのメタ情報を設定
            img_strip[CUSTOM_KEY_GENERATER] = ADDON_NAME
            img_strip[CUSTOM_KEY_STRIP_TYPE] = STRIP_TYPE_BORDER

            # image stripのチャンネルを更新
            #   stripが重なることを防ぐため、placeholder stripを削除してから更新する
            org_channel = strip.channel
            context.scene.sequence_editor.strips.remove(strip)
            img_strip.channel = org_channel

        return {"FINISHED"}

    def modal(self, context: Context, event: Event):
        if event.type == "TIMER":
            context.window_manager.event_timer_remove(self._timer)

            selected_placeholders = self.get_target_placeholders(context)
            if len(selected_placeholders) == 0:
                utils.showMessageBox(
                    messages=self._messages_no_placeholder,
                    title="処理対象がありません!!",
                    icon="ERROR",
                )
                return {"CANCELLED"}

            props = context.scene.borderman_props
            if not props.image_dir:
                utils.showMessageBox(
                    messages=self._messages_no_placeholder,
                    title="枠線画像ファイルの保存ディレクトリが指定されていません。",
                    icon="ERROR",
                )
                return {"CANCELLED"}
            image_dir = utils.normalize_image_dir(props.image_dir)
            if not image_dir:
                # 事前にプロジェクトの保存をチェックするため、通常ありえない
                utils.showMessageBox(
                    messages=self._messages_no_placeholder,
                    title="プロジェクトを保存してから実行してください。",
                    icon="ERROR",
                )
                return {"CANCELLED"}
            if not os.path.exists(image_dir):
                self.report(
                    {"INFO"},
                    f"画像保存ディレクトリが存在しないため作成:{image_dir}",
                )
                os.makedirs(image_dir)

            bpy.ops.sequencer.select_all(action="DESELECT")
            ret = self.add_border_strip(
                context,
                selected_placeholders,
                image_dir,
                props.shape_type,
                props.border_color,
                props.border_size,
                props.corner_radius,
            )
            self._timer = None
            return ret
        else:
            return {"RUNNING_MODAL"}

    def invoke(self, context: Context, event: Event):
        # blendファイルの存在チェック
        if not bpy.data.is_saved:
            utils.showMessageBox(
                messages=(
                    "画像ファイルをプロジェクトからの相対パスで保存するため、",
                    "プロジェクトを保存してから実行してください!!",
                ),
                title="プロジェクトファイル(.blend)を保存してください!!",
                icon="ERROR",
            )
            return {"CANCELLED"}

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

    _messages_no_placeholder = ("1つ以上のplaceholderを選択してください!!",)

    def get_target_placeholders(self, context: Context):
        return [strip for strip in context.selected_strips if is_placeholder(strip)]


class ReplaceAllPlaceholdersToBorder(ReplacePlaceholdersToBorder):
    bl_idname = "borderman.replace_all_placeholders"
    bl_label = "Replace all placeholders"
    bl_description = "Replace all placeholders to border strip."
    bl_options = {"REGISTER", "UNDO"}

    _messages_no_placeholder = (
        "placeholderがありません。",
        "1つ以上のplaceholderを追加してください!!",
    )

    def get_target_placeholders(self, context: Context):
        return [strip for strip in context.strips if is_placeholder(strip)]


class_list = [
    AddPlaceholder,
    ReplaceSelectedPlaceholdersToBorder,
    ReplaceAllPlaceholdersToBorder,
    DeleteUnusedBorderImages,
]
