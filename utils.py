import bpy
from dataclasses import dataclass


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


def get_strip_info(placeholder_strip: bpy.types.ColorStrip) -> Rect:
    screen_rect = get_screen_rect()
    strip_origin = placeholder_strip.transform.origin
    strip_w = screen_rect.w * placeholder_strip.transform.scale_x
    strip_h = screen_rect.h * placeholder_strip.transform.scale_y
    global_origin_x = (
        screen_rect.w * strip_origin[0] + placeholder_strip.transform.offset_x
    )
    global_origin_y = (
        screen_rect.h * strip_origin[1] + placeholder_strip.transform.offset_y
    )

    return Rect(global_origin_x, global_origin_y, strip_w, strip_h)


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


def showMessageBox(message="", title="Message Box", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
