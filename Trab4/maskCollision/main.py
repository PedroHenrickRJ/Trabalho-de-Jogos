import pygame
from abc import ABC, abstractmethod
from collision import Collider


pygame.init()
screen = pygame.display.set_mode((400, 400))
clock = pygame.time.Clock()

#inicialização

class obj (ABC):
    def __init__ (self, sprite, coord):
        self.sprite = sprite
        self.mask = pygame.mask.from_surface(sprite)
        self.coord = coord

    def draw (self, screen):
        screen.blit(self.sprite, self.coord) 

    @abstractmethod
    def lidar_colisao(self, obj):
        pass

    @abstractmethod
    def lidar_pato(self, pato):
        pass

    @abstractmethod
    def lidar_cursor(self, cursor):
        pass

class Pato(obj):

    def __init__(self, sprite, coord):
        super().__init__(sprite, coord)


    def lidar_colisao(self, obj):
        Collider().lidar_pato(self, obj)

    def lidar_pato(self, pato):
        pass # por enquanto patos não interagem
    
    def lidar_cursor(self, cursor):
        Collider().colisao_pato_cursor(self, cursor)
    
class Cursor(obj):
    def lidar_colisao(self,obj):
        Collider().lidar_cursor(self, obj)

    def lidar_pato(self, pato):
        Collider().colisao_pato_cursor(pato, self)
    
    def lidar_cursor(self, cursor):
        pass # cursores não colidem

duck = Pato(pygame.image.load("base.png").convert_alpha(),
           (100, 100))

cursor = Cursor(pygame.transform.scale2x(pygame.image.load("cursor.png").convert_alpha()), (200, 200))

objects = [duck, cursor]


running = True

while running:
    ## input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEMOTION:
            cursor.coord = pygame.mouse.get_pos()

    ## atualização
    if duck.mask.overlap(cursor.mask,
                        (cursor.coord[0]- duck.coord[0],
                         cursor.coord[1]- duck.coord[1])):
        print("colidiu")
        Collider().lidar_colisao(duck, cursor)


    ## desenho

    screen.fill((30,30,30))

    for o in objects:
        o.draw(screen)

    pygame.display.flip()
    clock.tick(150)
    pass