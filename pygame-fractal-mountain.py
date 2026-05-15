#!/usr/bin/env python
# Originally Copyright 1987 Compute! Publications, Inc.
# All Rights Reserved.
# Ported to Pygame 2020 Shane Simmons

import pygame
import random
import pygame.gfxdraw
import moderngl
import numpy as np
from pygame.locals import *
from datetime import datetime

# --- CRT SHADER SOURCE ---
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
in vec2 v_uv;
out vec4 f_color;

void main() {
    // Curvature effect
    vec2 uv = v_uv * 2.0 - 1.0;
    vec2 offset = abs(uv.yx) / vec2(12.0, 8.0); // Adjust for curve intensity
    uv = uv + uv * offset * offset;
    uv = uv * 0.5 + 0.5;

    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        f_color = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec4 baseColor = texture(tex, uv);
    
    // Scanline intensity
    baseColor.rgb *= 1.1; // 10% brightness boost
    float scanline = sin(uv.y * 3.1415927 * 200.0) * 0.033333333;
    baseColor.rgb -= scanline;


    // Subtle Vignette
    float vignette = uv.x * (1.0 - uv.x) * uv.y * (1.0 - uv.y) * 15.0;
    baseColor.rgb *= pow(vignette, 0.08);

    f_color = baseColor;
}
"""


class drawMountain:
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
        self.surf = pygame.Surface((320, 200))  # Internal resolution
        for a in range(16):
            r = min(int(16 * (a / 15.0)), 15)
            g = min(int(16 * (a / 25.0)), 15)
            b = min(int(16 * (a / 50.0)), 15)
            r += r << 4
            g += g << 4
            b += b << 4
            self.colors[a] = [r, g, b]  # dirt tones
            self.colors[a + 16] = [r, r, r]  # snow tones
            self.colors[16] = [0, 64, 128]  # water color

    def getshade(self, a, b, x, y):
        # (Keep original getshade logic)
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
        max = random.uniform(
            0.95, 1.15
        )  # maximum variation, original program says "1 is nice"
        for iter in range(6, 0, -1):
            sk = 2**iter
            hl = int(sk / 2)
            # do tops
            for y in range(0, 65, sk):
                for x in range(hl, 64, sk):
                    ran = (random.random() - 0.5) * max * sk
                    old = (self.lv[x - hl][y] + self.lv[x + hl][y]) / 2
                    self.lv[x][y] = old + ran
                    # do bottoms
            for x in range(0, 65, sk):
                for y in range(hl, 65, sk):
                    ran = (random.random() - 0.5) * max * sk
                    old = (self.lv[x][y - hl] + self.lv[x][y + hl]) / 2
                    self.lv[x][y] = old + ran
                    # do centers
            for x in range(hl, 65, sk):
                for y in range(hl, 65, sk):
                    ran = (random.random() - 0.5) * max * sk
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
    def __init__(self, width, height):
        self.ctx = moderngl.create_context()
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )

        # This defines the "quad" (two triangles) that fills the screen
        # Each row is: x, y (position) and u, v (texture coordinates)
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
        self.texture = self.ctx.texture((width, height), 4)
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def render(self, surface):
        # Convert Pygame surface to raw bytes for the GPU
        rgba_data = pygame.image.tostring(surface, "RGBA", True)
        self.texture.write(rgba_data)
        self.texture.use()
        self.vao.render(moderngl.TRIANGLE_STRIP)


# --- MAIN LOOP ---
pygame.init()
# Set display for OpenGL
pygame.display.set_mode((960, 720), DOUBLEBUF | OPENGL)
crt = CRTProcessor(320, 200)  # Process the low-res surface
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

    # Clear GL Context
    crt.ctx.clear(0, 0, 0)
    # Render mountain surface through the CRT shader
    crt.render(dm.surf)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
