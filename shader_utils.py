import gpu
from gpu_extras.batch import batch_for_shader


def ellipse_border_shader():
    vert_out = gpu.types.GPUStageInterfaceInfo("ellipse_border")
    vert_out.smooth("VEC3", "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant("VEC2", "boxSize")
    shader_info.push_constant("VEC2", "innerSize")
    shader_info.push_constant("VEC4", "borderColor")
    shader_info.vertex_in(0, "VEC3", "position")
    shader_info.vertex_out(vert_out)
    shader_info.fragment_out(0, "VEC4", "FragColor")

    shader_info.vertex_source(
        """"
    void main() {
      pos = position;
      gl_Position = vec4(position, 1.0);
    }
    """
    )

    shader_info.fragment_source(
        """
    // from https://iquilezles.org/articles/ellipsedist/
    float sdEllipse(in vec2 p, in vec2 ab) {
        // symmetry
        p = abs( p );

        // initial value
        vec2 q = ab*(p-ab);
        vec2 cs = normalize( (q.x<q.y) ? vec2(0.01,1) : vec2(1,0.01) );

        // find root with Newton solver
        for( int i=0; i<5; i++ )
        {
            vec2 u = ab*vec2( cs.x,cs.y);
            vec2 v = ab*vec2(-cs.y,cs.x);
            float a = dot(p-u,v);
            float c = dot(p-u,u) + dot(v,v);
            float b = sqrt(c*c-a*a);
            cs = vec2( cs.x*b-cs.y*a, cs.y*b+cs.x*a )/c;
        }

        // compute final point and distance
        float d = length(p-ab*cs);

        // return signed distance
        return (dot(p/ab,p/ab)>1.0) ? d : -d;
    }
    void main() {
      float d1 = sdEllipse(pos.xy, boxSize);
      float d2 = sdEllipse(pos.xy, innerSize);
      float d = max(d1, -d2);
      if (d <= 0) {
        FragColor = borderColor;
      } else {
        FragColor = vec4(vec3(0.0), 0.0);
      }
    }
    """
    )
    shader = gpu.shader.create_from_info(shader_info)
    del vert_out
    del shader_info
    return shader


def rounded_rectagle_border_shader():
    vert_out = gpu.types.GPUStageInterfaceInfo("rounded_rectagle_border")
    vert_out.smooth("VEC3", "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    shader_info.push_constant("VEC2", "boxSize")
    shader_info.push_constant("VEC2", "innerSize")
    shader_info.push_constant("VEC4", "borderColor")
    shader_info.push_constant("FLOAT", "cornerRadius")
    shader_info.vertex_in(0, "VEC3", "position")
    shader_info.vertex_out(vert_out)
    shader_info.fragment_out(0, "VEC4", "FragColor")

    shader_info.vertex_source(
        """"
    void main() {
      pos = position;
      gl_Position = vec4(position, 1.0);
    }
    """
    )

    shader_info.fragment_source(
        """
    // from https://iquilezles.org/articles/distfunctions2d/
    float sdBox(in vec2 p, in vec2 b, in float r) {
        vec2 d = abs(p) - b + r;
        return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r;
    }
    void main() {
      float d1 = sdBox(pos.xy, boxSize, cornerRadius);
      float d2 = sdBox(pos.xy, innerSize, 0);
      float d = max(d1, -d2);
      if (d <= 0) {
        FragColor = borderColor;
      } else {
        FragColor = vec4(vec3(0.0), 0.0);
      }
    }
    """
    )
    shader = gpu.shader.create_from_info(shader_info)
    del vert_out
    del shader_info
    return shader


def draw_rounded_rectagle_border(border_rect, inner_rect, border_color, corner_radius):
    screen_size = max(border_rect.w, border_rect.h)
    with gpu.matrix.push_pop():
        shader = rounded_rectagle_border_shader()
        batch = batch_for_shader(
            shader,
            "TRIS",
            {
                "position": [
                    [-1.0, -1.0],
                    [1.0, -1.0],
                    [1.0, 1.0],
                    [-1.0, -1.0],
                    [1.0, 1.0],
                    [-1.0, 1.0],
                ]
            },
        )
        shader.uniform_float(
            "boxSize", (border_rect.w / screen_size, border_rect.h / screen_size)
        )
        shader.uniform_float(
            "innerSize",
            (inner_rect.w / screen_size, inner_rect.h / screen_size),
        )
        shader.uniform_float("borderColor", border_color)
        shader.uniform_float(
            "cornerRadius",
            corner_radius / screen_size,
        )
        batch.draw(shader)


def draw_ellipse_border(border_rect, inner_rect, border_color):
    screen_size = max(border_rect.w, border_rect.h)
    with gpu.matrix.push_pop():
        shader = ellipse_border_shader()
        batch = batch_for_shader(
            shader,
            "TRIS",
            {
                "position": [
                    [-1.0, -1.0],
                    [1.0, -1.0],
                    [1.0, 1.0],
                    [-1.0, -1.0],
                    [1.0, 1.0],
                    [-1.0, 1.0],
                ]
            },
        )
        shader.uniform_float(
            "boxSize", (border_rect.w / screen_size, border_rect.h / screen_size)
        )
        shader.uniform_float(
            "innerSize",
            (inner_rect.w / screen_size, inner_rect.h / screen_size),
        )
        shader.uniform_float("borderColor", border_color)
        batch.draw(shader)
