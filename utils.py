import bpy
import datetime
from dataclasses import dataclass
import os
import secrets

from mathutils import Matrix
import gpu
from . import shader_utils


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int


def get_screen_rect() -> Rect:
    render = bpy.context.scene.render
    width = render.resolution_x * (render.resolution_percentage / 100)
    height = render.resolution_y * (render.resolution_percentage / 100)
    return Rect(0, 0, round(width), round(height))


def get_placeholder_info(placeholder_strip: bpy.types.ColorStrip) -> Rect:
    # スクリーン解像度
    screen_rect = get_screen_rect()
    trans = placeholder_strip.transform
    # ストリップのサイズ
    strip_w = screen_rect.w * trans.scale_x
    strip_h = screen_rect.h * trans.scale_y
    # ストリップの位置
    xy = [
        trans.offset_x,
        trans.offset_y,
    ]
    return Rect(*[round(p) for p in (xy[0], xy[1], strip_w, strip_h)])


def move_center(strip: bpy.types.ColorStrip):
    screen_rect = get_screen_rect()
    strip_origin = strip.transform.origin
    strip_w = screen_rect.w * strip.transform.scale_x
    strip_h = screen_rect.h * strip.transform.scale_y
    global_origin_x = screen_rect.w * strip_origin[0] + strip.transform.offset_x
    global_origin_y = screen_rect.h * strip_origin[1] + strip.transform.offset_y
    screen_center_x = screen_rect.w / 2
    screen_center_y = screen_rect.h / 2
    strip.transform.offset_x += (
        screen_center_x - global_origin_x - (0.5 - strip_origin[0]) * strip_w
    )
    strip.transform.offset_y += (
        screen_center_y - global_origin_y - (0.5 - strip_origin[1]) * strip_h
    )


def guess_available_channel(frame_start, frame_end, target_channel, seqs):
    unavailable_channels = set()
    for seq in seqs:
        if seq.channel in unavailable_channels:
            continue
        elif (
            frame_start <= seq.frame_final_start < frame_end
            or frame_start <= seq.frame_final_end <= frame_end
        ):
            unavailable_channels.add(seq.channel)
        elif (
            seq.frame_final_start <= frame_start <= seq.frame_final_end
            and seq.frame_final_start <= frame_end <= seq.frame_final_end
        ):
            unavailable_channels.add(seq.channel)
    if target_channel not in unavailable_channels:
        return target_channel

    last_no = sorted(unavailable_channels)[-1]
    candidate = set(range(target_channel, last_no + 2))
    diff = sorted(candidate - unavailable_channels)
    # 使われていない最小のチャンネルを返す
    return diff[0]


def showMessageBox(messages=[""], title="Message Box", icon="INFO"):
    def draw(self, context):
        for msg in messages:
            self.layout.label(text=msg)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def normalize_image_dir(image_dir):
    # `//`による相対パスを展開
    clean_image_dir = bpy.path.abspath(image_dir)
    # `//`の展開成功時(or もともと絶対パスが指定されている場合)
    if os.path.isabs(clean_image_dir):
        return clean_image_dir
    # 展開失敗時, つまり相対パスが指定された場合
    else:
        # .blendファイルが保存されているなら、
        # .blendファイルのパスから擬似的に`//`と同様にパス展開
        if len(bpy.data.filepath) > 0:
            base_dir = os.path.dirname(bpy.data.filepath)
            return os.path.normpath(os.path.join(base_dir, clean_image_dir))
        # .blendファイルが保存されていない場合
        else:
            return None


def create_border_strip(
    src_strip: bpy.types.Strip,
    image_dir,
    shape_type,
    border_size,
    border_color,
    corner_radius,
):
    if src_strip.name:
        file_name = f"{src_strip.name}"
    else:
        file_name = f"{src_strip.get('placeholder_id')}"

    output_path = os.path.join(image_dir, bpy.path.clean_name(file_name) + ".png")
    rect = get_placeholder_info(src_strip)
    create_border_image(
        output_path, rect, shape_type, border_size, border_color, corner_radius
    )

    rel_image_path = (
        bpy.path.relpath(output_path) if len(bpy.data.filepath) > 0 else output_path
    )
    # print(f"rel_image_path: {rel_image_path}")
    se = bpy.context.scene.sequence_editor
    img_strip = se.strips.new_image(
        bpy.path.basename(rel_image_path),
        rel_image_path,
        src_strip.channel + 1,
        src_strip.frame_final_start,
    )
    img_strip.frame_final_end = src_strip.frame_final_end
    img_strip.transform.origin[0] = 0
    img_strip.transform.origin[1] = 1.0
    img_strip.color_tag = "COLOR_01"
    return img_strip


def _make_unique_name(prefix="___"):
    return "{0}{1}_{2}".format(
        prefix, secrets.token_urlsafe(6), datetime.datetime.now().timestamp()
    )


def create_border_image(
    output_path, strip_rect, shape_type, border_size, border_color, corner_radius
):
    border_rect = Rect(
        0,
        0,
        int(strip_rect.w + (border_size * 2)),
        int(strip_rect.h + (border_size * 2)),
    )

    image_name = _make_unique_name()
    offscreen_rect = shader_utils.get_offscreen_info(border_rect)

    offscreen = gpu.types.GPUOffScreen(offscreen_rect.w, offscreen_rect.h)

    with offscreen.bind():
        fb = gpu.state.active_framebuffer_get()
        fb.clear(color=(0.0, 0.0, 0.0, 0.0))

        with gpu.matrix.push_pop():
            # reset matrices -> use normalized device coordinates [-1, 1]
            gpu.matrix.load_matrix(Matrix.Identity(4))
            gpu.matrix.load_projection_matrix(Matrix.Identity(4))

            print(f"shape_type: {shape_type}")
            if shape_type == "rectangle":
                shader_utils.draw_rounded_rectagle_border(
                    border_rect, border_color, border_size, corner_radius
                )
            else:
                shader_utils.draw_ellipse_border(border_rect, border_color, border_size)

            buffer = fb.read_color(
                offscreen_rect.offset_x,
                offscreen_rect.offset_y,
                border_rect.w,
                border_rect.h,
                4,
                0,
                "UBYTE",
            )

    offscreen.free()
    if image_name in bpy.data.images:
        img = bpy.data.images[image_name]
        bpy.data.images.remove(img)

    img = bpy.data.images.new(
        image_name, width=border_rect.w, height=border_rect.h, alpha=True
    )
    img.file_format = "PNG"
    img.alpha_mode = "STRAIGHT"
    img.filepath = output_path
    buffer.dimensions = border_rect.w * border_rect.h * 4
    img.pixels = [v / 255 for v in buffer]
    img.save()
    bpy.data.images.remove(img)
    print(f"create_border_image: {output_path}")
