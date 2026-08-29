import pygame
from abc import ABC, abstractmethod
from util import colored_sprite, EventHandler


import math

def rotate(pos, angle, axis = (0,0)):
    angle = math.radians(angle)
    x, y = pos
    ax, ay = axis

    # Translate so axis is the origin
    x -= ax
    y -= ay

    # Rotate
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    rx = x * cos_a - y * sin_a
    ry = x * sin_a + y * cos_a

    # Translate back
    return rx + ax, ry + ay

class Bullet (ABC):

    def __init__(self, pos, angle = 0, radius = 16, life_time = None):
        self.pos = pos
        self.origin = pygame.Vector2(pos)
        self.life_time = life_time
        self.angle = angle
        self.elapsed = 0
        self.radius = radius

        self.sprite = colored_sprite ((255, 0, 0), (self.radius*2, self.radius*2))

    def update(self, dt):

        self.elapsed += dt
        if self.life_time and self.elapsed >= self.life_time:
                self.destroy()       

        self.pos = rotate(self.move(), self.angle)+self.origin

    def draw(self, screen):
        screen.blit(self.sprite, self.pos)

    @abstractmethod
    def move(self):
        pass

    def destroy(self): # pede para deletar
        EventHandler().notify("DestroyObj", self) # avisa o mundo que saiu da tela

class sinBullet (Bullet):
    # exemplo, façam algo mais rebuscado

    def move(self):
        return pygame.Vector2(self.elapsed, math.sin(self.elapsed/50)*50) 