import pygame
from abc import ABC, abstractmethod
from util import colored_sprite

class Player:

    def __init__(self, pos):
        self.pos = pos
        self.state = ExampleState(self)

    def update(self, dt):
        self.state.update(dt)

    def draw(self, screen):
        self.state.draw(screen)

    def action_1(self):
        self.state.action_1()

    def action_2(self):
        self.state.action_2()

    def change_state(self, new_state):
        self.state.delete()
        self.state = new_state(self)


class PlayerState(ABC):

    # Sprite é comum a classe estado
    sprite = pygame.Surface((32, 32))

    def __init__(self, player):
        self.P = player

    def draw(self, screen):
        screen.blit(self.sprite, self.P.pos)

    def delete(self):
        pass  # se precisar apagar algo na mudança de estados

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def action_1(self, dt):
        pass

    @abstractmethod
    def action_2(self, dt):
        pass


class ExampleState(PlayerState):

    # Sempre aqui para o estados, mesmo que descarregue
    # sprite = pygame.image.load("images/duck/base.png")

    # ALternativamente, use em retângulo
    sprite = colored_sprite((0, 255, 0))

    def update(self, dt):
        pass  # faça sua implementação
    
    def action_1(self):
        print("faz a ação 1")
        pass # faça sua implementação

    def action_2(self):
        print("faz a ação 2")
        pass # faça sua implementação