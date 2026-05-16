import moderngl
import pygame
import numpy as np

# --- ZFAST CRT SHADER SOURCE ---
# Adapted from: https://github.com/libretro/glsl-shaders/blob/master/crt/shaders/zfast_crt.glsl
VERTEX_SHADER = """
#version 330
in vec2 in_vert;
in vec2 in_uv;
out vec2 v_uv;

void main() {
    v_uv = in_uv;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330
uniform sampler2D tex;
uniform vec4 SourceSize;
uniform vec4 OutputSize;
in vec2 v_uv;
out vec4 f_color;

// --- ADJUSTABLE PARAMETERS ---
#define SCANLINE_WEIGHT 1.2         // Lower = softer scanlines, less banding
#define SCANLINE_GAP_BRIGHTNESS 0.65 // Higher = less contrast, but smoother
#define BLOOM_FACTOR 1.25
#define INPUT_GAMMA 1.8
#define OUTPUT_GAMMA 2.2

void main() {
    vec2 uv = v_uv;

    // 1. Curvature (Reduced slightly to prevent edge banding)
    vec2 cc = uv - 0.5;
    float dist = dot(cc, cc) * 0.002;
    uv = (cc + cc * dist) + 0.5;

    if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) {
        f_color = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // 2. Sample Color & Linearize
    vec3 col = texture(tex, uv).rgb;
    col = pow(col, vec3(INPUT_GAMMA));

    // 3. Smooth Scanlines (The "Zfast" Anti-Banding Method)
    // We calculate the distance to the center of the source pixel
    float pos_y = uv.y * SourceSize.y;
    float delta_y = abs(fract(pos_y) - 0.5);
    
    // Using smoothstep instead of a hard multiply reduces moiré patterns
    float scanline = mix(1.0, SCANLINE_GAP_BRIGHTNESS, smoothstep(0.0, 0.5, delta_y * SCANLINE_WEIGHT));

    // 4. Combine and Apply Bloom
    col *= scanline;
    col *= BLOOM_FACTOR;

// 5. Return to Gamma Space
    f_color = vec4(pow(col, vec3(1.0 / OUTPUT_GAMMA)), 1.0);
}
"""


class CRTProcessor:
    def __init__(self, internal_res, output_res):
        self.ctx = moderngl.create_context()
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )

        # Defensive uniform setting: Only set if the shader actually uses them
        if "SourceSize" in self.prog:
            self.prog["SourceSize"].value = (
                internal_res[0],
                internal_res[1],
                1.0 / internal_res[0],
                1.0 / internal_res[1],
            )
        if "OutputSize" in self.prog:
            self.prog["OutputSize"].value = (
                output_res[0],
                output_res[1],
                1.0 / output_res[0],
                1.0 / output_res[1],
            )

        # Standard 4-point strip for a full-screen quad
        vertices = np.array(
            [
                -1.0,
                1.0,
                0.0,
                1.0,
                -1.0,
                -1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                0.0,
            ],
            dtype="f4",
        )

        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(
            self.prog, [(self.vbo, "2f 2f", "in_vert", "in_uv")]
        )
        self.texture = self.ctx.texture(internal_res, 4)
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def render(self, surface):
        rgba_data = pygame.image.tobytes(surface, "RGBA", True)
        self.texture.write(rgba_data)
        self.texture.use()
        self.vao.render(moderngl.TRIANGLE_STRIP)
