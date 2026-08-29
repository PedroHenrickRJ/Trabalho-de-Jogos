import pygame
from player import Player
from bullet import sinBullet
from util import EventHandler

#inicialização

pygame.init()
WIDTH   =  800; HEIGHT =  600
clock = pygame.time.Clock()

screen = pygame.display.set_mode((WIDTH, HEIGHT))  
player = Player((50, 50))
b = sinBullet((400, 300), -45, life_time=240) 

objects = []
objects.append(player)
objects.append(b)


# funções auxiliares

def handle_input(player):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.action_1() # pode ser melhorado para evento
            if event.key == pygame.K_TAB:
                player.action_2() # pode ser melhorado para evento

def remove_obj(obj):
    #variavel global é feio, mas serve como um exemplo
    if obj in objects:
        objects.remove(obj) 

#inscreve esse metodo pra remoção de objetos
EventHandler().subscribe("DestroyObj", remove_obj)

# loop principal

running = True
while running:

    handle_input(player)

    for obj in objects:
        obj.update(1)

    screen.fill((30,30,30))

    for obj in objects:
        obj.draw(screen)
    
    pygame.display.flip()
    clock.tick(60)
    