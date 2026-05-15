import pygame
import random
import pygame.gfxdraw
import moderngl
import numpy as np
from pygame.locals import *
from datetime import datetime

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
#define SCANLINE_WEIGHT 1.5         // Lower = softer scanlines, less banding
#define SCANLINE_GAP_BRIGHTNESS 0.65 // Higher = less contrast, but smoother
#define BLOOM_FACTOR 1.25
#define INPUT_GAMMA 1.8
#define OUTPUT_GAMMA 2.2

// Simple hash for dithering (eliminates color banding)
float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

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

    // 5. Add Dither Noise
    // This breaks up the "steps" in the gradient colors
    float noise = (rand(uv) - 0.5) * (1.0 / 255.0);
    col += noise;

    // 6. Return to Gamma Space
    f_color = vec4(pow(col, vec3(1.0 / OUTPUT_GAMMA)), 1.0);
}
"""


class drawMountain:
    # (Original drawMountain logic remains unchanged)
    llv: int = 0
    maxLv: int = 0
    xm = 4.5
    hl = 0
    ym = 2
    x = 0
    y = 0
    xshift = 0.9
    yp = 45
    snowline = 0

    def __init__(self):
        self.lv = [[0.0] * 65 for f in range(65)]
        self.colors = [[0, 0, 0]] * 32
        self.surf = pygame.Surface((320, 200))
        for a in range(16):
            r = min(int(16 * (a / 15.0)), 15)
            g = min(int(16 * (a / 25.0)), 15)
            b = min(int(16 * (a / 50.0)), 15)
            r += r << 4
            g += g << 4
            b += b << 4
            self.colors[a] = [r, g, b]
            self.colors[a + 16] = [r, r, r]
            self.colors[16] = [0, 64, 128]

    def getshade(self, a, b, x, y):
        try:
            c, d = (x + 1 - (b - y)), (y + (a - x))
            xc, yc = x + 0.5, y + 0.5
            xrun1, xrun2 = xc - a, xc - c
            yrun1, yrun2 = yc - b, yc - d
            rise1, rise2 = self.llv - self.lv[a][b], self.llv - self.lv[c][d]
            yrise = abs((rise1 * xrun2) - (rise2 * xrun1))
            yrun = abs((yrun1 * xrun2) - (xrun1 * yrun2))
            if yrun == yrise:
                yrun = yrise = 1
            xrise = abs((rise1 * yrun2) - (rise2 * yrun1))
            xrun = abs((xrun1 * yrun2) - (yrun1 * xrun2))
            if xrun == xrise:
                xrun = xrise = 1
            xshade = 1 - abs((xrise / 2) / (xrun + (xrise / 2)))
            yshade = 1 - abs((yrise / 2) / (yrun + (yrise / 2)))
            shade = 14 * xshade * yshade + 1
            if self.llv > self.snowline:
                shade += 16
            if self.llv <= 0:
                shade = 16
            return int(shade)
        except:
            return 0

    def draw(self):
        self.maxLv = 0
        self.surf.fill((0, 0, 0))
        max_val = random.uniform(0.95, 1.15)
        for iter in range(6, 0, -1):
            sk = 2**iter
            hl = int(sk / 2)
            for y in range(0, 65, sk):
                for x in range(hl, 64, sk):
                    ran = (random.random() - 0.5) * max_val * sk
                    old = (self.lv[x - hl][y] + self.lv[x + hl][y]) / 2
                    self.lv[x][y] = old + ran
            for x in range(0, 65, sk):
                for y in range(hl, 65, sk):
                    ran = (random.random() - 0.5) * max_val * sk
                    old = (self.lv[x][y - hl] + self.lv[x][y + hl]) / 2
                    self.lv[x][y] = old + ran
            for x in range(hl, 65, sk):
                for y in range(hl, 65, sk):
                    ran = (random.random() - 0.5) * max_val * sk
                    old1 = (self.lv[x + hl][y - hl] + self.lv[x - hl][y + hl]) / 2
                    old2 = (self.lv[x - hl][y - hl] + self.lv[x + hl][y + hl]) / 2
                    old = (old1 + old2) / 2
                    self.lv[x][y] = old + ran
                    if self.lv[x][y] > self.maxLv:
                        self.maxLv = int(self.lv[x][y])

        self.snowline = self.maxLv - self.maxLv / 4
        for x in range(0, 65):
            if self.lv[x][0] < 0:
                self.lv[x][0] = 0
        for y in range(0, 64):
            if self.lv[0][y] < 0:
                self.lv[0][y] = 0
            for x in range(0, 64):
                self.llv = int(
                    (
                        self.lv[x][y]
                        + self.lv[x + 1][y]
                        + self.lv[x][y + 1]
                        + self.lv[x + 1][y + 1]
                    )
                    / 4
                )
                points = [
                    (
                        self.xm * x + self.xshift * y,
                        self.ym * y + self.yp - self.lv[x][y],
                    ),
                    (
                        self.xm * (x + 1) + self.xshift * y,
                        self.ym * y + self.yp - self.lv[x + 1][y],
                    ),
                    (
                        self.xm * (x + 1) + self.xshift * (y + 1),
                        self.ym * (y + 1) + self.yp - self.lv[x + 1][y + 1],
                    ),
                    (
                        self.xm * x + self.xshift * (y + 1),
                        self.ym * (y + 1) + self.yp - self.lv[x][y + 1],
                    ),
                ]
                shade = tuple(self.colors[self.getshade(x, y, x, y)])
                pygame.gfxdraw.filled_polygon(self.surf, points, shade)

    def image_save(self):
        fn = datetime.now().strftime("mountain-%Y%m%d-%H%M%S.png")
        pygame.image.save(self.surf, fn)


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


# --- MAIN LOOP ---
WIDTH, HEIGHT = 960, 720
INT_W, INT_H = 320, 200

pygame.init()
pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
crt = CRTProcessor((INT_W, INT_H), (WIDTH, HEIGHT))
dm = drawMountain()
dm.draw()

clock = pygame.time.Clock()
done = False

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                done = True
            elif event.key == pygame.K_s:
                dm.image_save()
            else:
                dm.draw()

    crt.ctx.clear(0, 0, 0)
    crt.render(dm.surf)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
