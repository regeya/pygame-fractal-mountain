import pygame
import random
import pygame.gfxdraw
import crt
from datetime import datetime
import pygame.locals as pg


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
        for x in range(0, 64):
            for y in range(0, 64):
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
                        self.ym * y + self.yp - max(0, self.lv[x][y]),
                    ),
                    (
                        self.xm * (x + 1) + self.xshift * y,
                        self.ym * y + self.yp - max(0, self.lv[x + 1][y]),
                    ),
                    (
                        self.xm * (x + 1) + self.xshift * (y + 1),
                        self.ym * (y + 1) + self.yp - max(0, self.lv[x + 1][y + 1]),
                    ),
                    (
                        self.xm * x + self.xshift * (y + 1),
                        self.ym * (y + 1) + self.yp - max(0, self.lv[x][y + 1]),
                    ),
                ]
                shade = tuple(self.colors[self.getshade(x, y, x, y)])
                pygame.gfxdraw.filled_polygon(self.surf, points, shade)

    def image_save(self):
        fn = datetime.now().strftime("mountain-%Y%m%d-%H%M%S.png")
        pygame.image.save(self.surf, fn)


# --- MAIN LOOP ---
WIDTH, HEIGHT = 960, 720
INT_W, INT_H = 320, 200

pygame.init()
pygame.display.set_mode((WIDTH, HEIGHT), pg.DOUBLEBUF | pg.OPENGL)
crt = crt.CRTProcessor((INT_W, INT_H), (WIDTH, HEIGHT))
dm = drawMountain()
dm.draw()

clock = pygame.time.Clock()
done = False

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
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
