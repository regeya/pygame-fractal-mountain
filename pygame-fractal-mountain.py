#!/usr/bin/env python
# Originally Copyright 1987 Compute! Publications, Inc.
# All Rights Reserved.
# Ported to Pygame 2020 Shane Simmons

import pygame, sys, random, pygame.gfxdraw
from pygame.locals import *
from datetime import datetime

window = pygame.display.set_mode((960, 720))

class drawMountain:
    llv = 0
    maxLv = 0
    xm = 4.5
    hl = 0
    ym =2 
    x = 0
    y = 0 
    xshift = .9
    yp = 45
    snowline = 0
    def __init__(self):
        self.lv = [[0.0] * 65 for f in range (65)]
        self.colors = [[None] * 3] * 32
        self.surf = pygame.Surface((320,200))
        for a in range(16):
            r = min(int(16*(a/15.0)), 15)
            g = min(int(16*(a/25.0)), 15)
            b = min(int(16*(a/50.0)), 15)
            r += (r << 4)
            g += (g << 4)
            b += (b << 4)
            self.colors[a] = [r, g, b]  # dirt tones
            self.colors[a+16] = [r, r, r] # snow tones
            self.colors[16] = [0, 64, 128] # water color

    def getshade(self, a, b, x, y):
        c = x + 1 - (b - y)
        d = y + (a - x)
        xc = x + .5
        yc = y + .5
        xrun1 = xc - a
        xrun2 = xc - c
        yrun1 = yc - b
        yrun2 = yc - d
        rise1 = self.llv - self.lv[a][b]
        rise2 = self.llv - self.lv[c][d]
        yrise = abs((rise1 * xrun2) - (rise2 * xrun1))
        yrun = abs((yrun1 * xrun2) - (xrun1 * yrun2))
        if (yrun == yrise):
            yrun = 1
            yrise = 1
        xrise = abs((rise1 * yrun2) - (rise2 * yrun1))
        xrun = abs((xrun1 * yrun2) - (yrun1 * xrun2))
        if (xrun == xrise):
            xrun = 1
            xrise = 1
        xrise = xrise / 2
        yrise = yrise / 2
        xshade = 1-abs(xrise / (xrun + xrise))
        yshade = 1-abs(yrise / (yrun + yrise))
        shade = 14 * xshade * yshade + 1
        if (self.llv > self.snowline):
            shade = shade + 16
        if (self.llv <= 0):
            shade = 16
        return(int(shade))

    def draw(self):
        self.maxLv = 0
        self.surf.fill((0,0,0))
        max = random.uniform(0.95, 1.15) # maximum variation, original program says "1 is nice"
        for iter in range(6,0,-1):
            sk = 2 ** iter
            hl = int(sk / 2)
                # do tops
            for y in range(0,65,sk):
                for x in range(hl,64,sk):
                    ran = (random.random() - 0.5) * max * sk
                    old = (self.lv[x-hl][y] + self.lv[x + hl][y]) / 2
                    self.lv[x][y] = old + ran
                    # do bottoms
            for x in range(0, 65, sk):
                for y in range(hl, 65, sk):
                    ran = (random.random() - 0.5) * max * sk
                    old = (self.lv[x][y-hl] + self.lv[x][y+hl]) / 2
                    self.lv[x][y] = old + ran
                    # do centers
            for x in range(hl, 65, sk):
                for y in range(hl, 65, sk):
                    ran = (random.random()-0.5) * max * sk
                    old1 = (self.lv[x+hl][y-hl] + self.lv[x-hl][y+hl]) / 2
                    old2 = (self.lv[x-hl][y-hl] + self.lv[x+hl][y+hl]) / 2
                    old = (old1 + old2) / 2
                    self.lv[x][y] = old + ran
                    if self.lv[x][y] > self.maxLv:
                        self.maxLv = self.lv[x][y]

        self.snowline = self.maxLv - self.maxLv/4
        for x in range(0,65):
            if (self.lv[x][0] < 0):
                self.lv[x][0] = 0
        for y in range(0,64):
            if (self.lv[0][y] < 0):
                self.lv[0][y] = 0
            for x in range(0,64):
                if (self.lv[x+1][y+1] < 0):
                    self.lv[x+1][y+1] = 0
                self.llv = self.lv[x][y] + self.lv[x+1][y] + self.lv[x][y+1]
                self.llv = (self.llv + self.lv[x+1][y+1]) / 4
                a = x 
                b = y
                rx1 = self.xm * a + self.xshift * b
                ry1 = self.ym * b + self.yp - self.lv[a][b]
                shade1 = tuple(self.colors[self.getshade(a, b, x, y)])
                a = x + 1
                rx2 = self.xm * a + self.xshift * b
                ry2 = self.ym * b + self.yp - self.lv[a][b]
                shade2 = tuple(self.colors[self.getshade(a, b, x, y)])
                a = x
                b = y + 1
                rx3 = self.xm * a + self.xshift * b
                ry3 = self.ym * b + self.yp - self.lv[a][b]
                shade3 = tuple(self.colors[self.getshade(a, b, x, y)])
                a = x + 1
                rx4 = self.xm * a + self.xshift * b
                ry4 = self.ym * b + self.yp - self.lv[a][b]
                shade4 = tuple(self.colors[self.getshade(a, b, x, y)])
                a = x + .5
                b = y + .5
                rx = self.xm * a + self.xshift * b
                ry = self.ym * b + self.yp
                a = x
                b = y
                ry = ry - self.llv
                pygame.gfxdraw.filled_polygon(self.surf, ((rx, ry), (rx1, ry1), (rx2, ry2)), shade1)
                pygame.gfxdraw.filled_polygon(self.surf, ((rx, ry), (rx2, ry2), (rx4, ry4)), shade2)
                pygame.gfxdraw.filled_polygon(self.surf, ((rx, ry), (rx1, ry1), (rx3, ry3)), shade3)
                pygame.gfxdraw.filled_polygon(self.surf, ((rx, ry), (rx3, ry3), (rx4, ry4)), shade4)

        pygame.transform.smoothscale(pygame.transform.gaussian_blur(self.surf,1),(960,720), window)
        window.blit(self.surf, (960,720))
        pygame.display.flip()
        pygame.display.update()

    def image_save(self):
        now = datetime.now()
        fn = now.strftime("mountain-%Y%m%d-%H%M%S.png")
        pygame.image.save(self.surf, fn)

dm = drawMountain()

dm.draw()

done = False

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                done = True
            elif event.key == pygame.K_s:
                dm.image_save()
            else:
                dm.draw()