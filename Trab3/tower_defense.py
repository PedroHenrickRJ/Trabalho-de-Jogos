import math
import random
import sys
from enum import Enum, auto

import pygame

LARGURA, ALTURA = 960, 640
FPS = 60

COR_FUNDO = (30, 33, 41)
COR_CAMINHO = (90, 90, 100)
COR_CAMINHO_BORDA = (60, 60, 68)
COR_TEXTO = (235, 235, 235)
COR_GRAMA = (40, 60, 45)

LARGURA_CAMINHO = 46  # espessura visual do caminho / distância mínima p/ torres

# ---------------------------------------------------------------------------
# sistema de Eventos
EVT_ENEMY_SPAWNED = pygame.USEREVENT + 1
EVT_ENEMY_DESTROYED = pygame.USEREVENT + 2
EVT_ENEMY_REACHED_END = pygame.USEREVENT + 3
EVT_PROJECTILE_CREATED = pygame.USEREVENT + 4
EVT_PROJECTILE_DESTROYED = pygame.USEREVENT + 5
EVT_COLLISION = pygame.USEREVENT + 6
EVT_TOWER_PLACED = pygame.USEREVENT + 7
EVT_PLAYER_DAMAGED = pygame.USEREVENT + 8
EVT_POWERUP_SPAWNED = pygame.USEREVENT + 9
EVT_POWERUP_COLLECTED = pygame.USEREVENT + 10


def emitir(tipo_evento, **dados):
    # publica um evento na fila global do pygame
    pygame.event.post(pygame.event.Event(tipo_evento, **dados))


# gerando o caminho com uma lista de pontos
def gerar_caminho_em_s():
    pontos = [
        (40, 90),
        (760, 90),
        (760, 300),
        (200, 300),
        (200, 520),
        (920, 520),
    ]
    return pontos

CAMINHO = gerar_caminho_em_s()


def comprimento_total(caminho):
    total = 0.0
    for i in range(len(caminho) - 1):
        x1, y1 = caminho[i]
        x2, y2 = caminho[i + 1]
        total += math.hypot(x2 - x1, y2 - y1)
    return total


def ponto_no_caminho(caminho, distancia_percorrida):
    restante = distancia_percorrida
    for i in range(len(caminho) - 1):
        x1, y1 = caminho[i]
        x2, y2 = caminho[i + 1]
        seg_len = math.hypot(x2 - x1, y2 - y1)
        if restante <= seg_len:
            t = restante / seg_len if seg_len > 0 else 0
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            return (x, y), False
        restante -= seg_len
    return caminho[-1], True


def dist_ponto_para_segmento(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x, proj_y = x1 + t * dx, y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def dist_ponto_para_caminho(caminho, px, py):
    return min(
        dist_ponto_para_segmento(px, py, *caminho[i], *caminho[i + 1])
        for i in range(len(caminho) - 1)
    )


# ---------------------------------------------------------------------------
# Estados do Inimigo
class EstadoInimigo(Enum):
    APROXIMANDO = auto()
    ATORDOADO = auto()
    MORTO = auto()


class Inimigo:
    RAIO = 14

    def __init__(self, vida_max, velocidade, id_):
        self.id = id_
        self.distancia = 0.0
        self.vida_max = vida_max
        self.vida = vida_max
        self.velocidade = velocidade
        self.estado = EstadoInimigo.APROXIMANDO
        self.timer_atordoado = 0.0
        self.pos = CAMINHO[0]
        emitir(EVT_ENEMY_SPAWNED, inimigo=self)

    # --- transições de estado -------------------------------------------------
    def aplicar_dano(self, dano):
        if self.estado == EstadoInimigo.MORTO:
            return
        self.vida -= dano
        if self.vida <= 0:
            self.morrer()

    def atordoar(self, duracao):
        if self.estado == EstadoInimigo.MORTO:
            return
        self.estado = EstadoInimigo.ATORDOADO
        self.timer_atordoado = max(self.timer_atordoado, duracao)

    def morrer(self):
        if self.estado == EstadoInimigo.MORTO:
            return
        self.estado = EstadoInimigo.MORTO
        emitir(EVT_ENEMY_DESTROYED, inimigo=self)

    def atualizar(self, dt, comprimento_max):
        if self.estado == EstadoInimigo.MORTO:
            return

        if self.estado == EstadoInimigo.ATORDOADO:
            self.timer_atordoado -= dt
            if self.timer_atordoado <= 0:
                self.estado = EstadoInimigo.APROXIMANDO
            return  # enquanto atordoado, não anda

        if self.estado == EstadoInimigo.APROXIMANDO:
            self.distancia += self.velocidade * dt
            pos, chegou = ponto_no_caminho(CAMINHO, self.distancia)
            self.pos = pos
            if chegou:
                self.estado = EstadoInimigo.MORTO
                emitir(EVT_ENEMY_REACHED_END, inimigo=self)

    def desenhar(self, tela):
        x, y = self.pos
        cor = (220, 70, 70) if self.estado != EstadoInimigo.ATORDOADO else (230, 200, 60)
        pygame.draw.circle(tela, cor, (int(x), int(y)), self.RAIO)
        pygame.draw.circle(tela, (20, 20, 20), (int(x), int(y)), self.RAIO, 2)
        # barra de vida
        largura_barra = 30
        vida_pct = max(0, self.vida / self.vida_max)
        pygame.draw.rect(tela, (60, 0, 0), (x - largura_barra / 2, y - 26, largura_barra, 5))
        pygame.draw.rect(
            tela, (0, 200, 60), (x - largura_barra / 2, y - 26, largura_barra * vida_pct, 5)
        )
        if self.estado == EstadoInimigo.ATORDOADO:
            fonte = pygame.font.SysFont("arial", 14, bold=True)
            txt = fonte.render("Z", True, (255, 255, 0))
            tela.blit(txt, (x + self.RAIO - 4, y - self.RAIO - 20))


class TipoProjetil(Enum):
    ATORDOANTE = auto()
    AREA = auto()


class Projetil:
    VELOCIDADE = 480

    def __init__(self, origem, alvo, tipo, dano, raio_area=0, duracao_atordoamento=0.0):
        self.pos = list(origem)
        self.alvo = alvo  # referência ao inimigo alvo (pode morrer antes de chegar)
        self.pos_alvo_congelada = alvo.pos  # usado se o alvo morrer no meio do caminho
        self.tipo = tipo
        self.dano = dano
        self.raio_area = raio_area
        self.duracao_atordoamento = duracao_atordoamento
        self.vivo = True
        emitir(EVT_PROJECTILE_CREATED, projetil=self)

    def atualizar(self, dt, lista_inimigos):
        if not self.vivo:
            return

        if self.alvo.estado != EstadoInimigo.MORTO:
            self.pos_alvo_congelada = self.alvo.pos

        alvo_x, alvo_y = self.pos_alvo_congelada
        dx, dy = alvo_x - self.pos[0], alvo_y - self.pos[1]
        dist = math.hypot(dx, dy)
        passo = self.VELOCIDADE * dt

        if dist <= passo or dist < 6:
            self._atingir(lista_inimigos)
            return

        self.pos[0] += dx / dist * passo
        self.pos[1] += dy / dist * passo

    def _atingir(self, lista_inimigos):
        emitir(EVT_COLLISION, projetil=self, ponto=tuple(self.pos))

        if self.tipo == TipoProjetil.ATORDOANTE:
            if self.alvo.estado != EstadoInimigo.MORTO:
                self.alvo.aplicar_dano(self.dano)
                self.alvo.atordoar(self.duracao_atordoamento)
        else:  # dano em área, sem atordoar
            for inimigo in lista_inimigos:
                if inimigo.estado == EstadoInimigo.MORTO:
                    continue
                if math.hypot(inimigo.pos[0] - self.pos[0], inimigo.pos[1] - self.pos[1]) <= self.raio_area:
                    inimigo.aplicar_dano(self.dano)

        self.vivo = False
        emitir(EVT_PROJECTILE_DESTROYED, projetil=self)

    def desenhar(self, tela):
        cor = (255, 230, 90) if self.tipo == TipoProjetil.ATORDOANTE else (255, 130, 60)
        pygame.draw.circle(tela, cor, (int(self.pos[0]), int(self.pos[1])), 6)


# ---------- torres -----------------------------
class TipoTorre(Enum):
    ATORDOAMENTO = auto()
    AREA = auto()


TORRE_INFO = {
    TipoTorre.ATORDOAMENTO: dict(
        custo=60, alcance=140, cooldown=1.1, dano=18, duracao_atordoamento=1.2,
        cor=(90, 150, 230), nome="Torre Atordoante",
    ),
    TipoTorre.AREA: dict(
        custo=90, alcance=115, cooldown=1.6, dano=22, raio_area=55,
        cor=(230, 120, 60), nome="Torre de Área",
    ),
}


class Torre:
    RAIO_BASE = 18

    def __init__(self, pos, tipo):
        self.pos = pos
        self.tipo = tipo
        info = TORRE_INFO[tipo]
        self.alcance = info["alcance"]
        self.cooldown_max = info["cooldown"]
        self.dano = info["dano"]
        self.cooldown_atual = 0.0
        self.raio_area = info.get("raio_area", 0)
        self.duracao_atordoamento = info.get("duracao_atordoamento", 0.0)
        self.alvo_atual = None
        emitir(EVT_TOWER_PLACED, torre=self)

    def _procurar_alvo(self, inimigos):
        candidatos = [
            e for e in inimigos
            if e.estado != EstadoInimigo.MORTO
            and math.hypot(e.pos[0] - self.pos[0], e.pos[1] - self.pos[1]) <= self.alcance
        ]
        if not candidatos:
            return None
        # mira no inimigo mais avançado no caminho
        return max(candidatos, key=lambda e: e.distancia)

    def atualizar(self, dt, inimigos, projeteis, multiplicador_dano):
        self.cooldown_atual -= dt
        self.alvo_atual = self._procurar_alvo(inimigos)

        if self.alvo_atual is not None and self.cooldown_atual <= 0:
            self.cooldown_atual = self.cooldown_max
            dano_final = self.dano * multiplicador_dano
            if self.tipo == TipoTorre.ATORDOAMENTO:
                projeteis.append(
                    Projetil(
                        self.pos, self.alvo_atual, TipoProjetil.ATORDOANTE,
                        dano_final, duracao_atordoamento=self.duracao_atordoamento,
                    )
                )
            else:
                projeteis.append(
                    Projetil(
                        self.pos, self.alvo_atual, TipoProjetil.AREA,
                        dano_final, raio_area=self.raio_area,
                    )
                )

    def desenhar(self, tela, mostrar_alcance=False):
        info = TORRE_INFO[self.tipo]
        x, y = self.pos
        if mostrar_alcance:
            s = pygame.Surface((self.alcance * 2, self.alcance * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, 40), (self.alcance, self.alcance), self.alcance)
            tela.blit(s, (x - self.alcance, y - self.alcance))
        pygame.draw.circle(tela, info["cor"], (int(x), int(y)), self.RAIO_BASE)
        pygame.draw.circle(tela, (20, 20, 20), (int(x), int(y)), self.RAIO_BASE, 2)
        if self.tipo == TipoTorre.ATORDOAMENTO:
            pygame.draw.circle(tela, (255, 255, 255), (int(x), int(y)), 5)
        else:
            pygame.draw.rect(tela, (255, 255, 255), (x - 5, y - 5, 10, 10))

class PowerUp:
    RAIO = 10

    def __init__(self, pos):
        self.pos = pos
        emitir(EVT_POWERUP_SPAWNED, powerup=self)

# ------------------------------------------------------------------
# Estados e controle do Jogador
class EstadoSelecaoTorre(Enum):
    NENHUMA = auto()
    ATORDOAMENTO = auto()
    AREA = auto()


class Jogador:

    DURACAO_INVENCIBILIDADE = 1.0  # segundos sem poder perder vida de novo
    DURACAO_POWERUP = 10.0

    def __init__(self):
        self.dinheiro = 150
        self.vidas = 10
        self.selecao = EstadoSelecaoTorre.NENHUMA
        self.timer_invencivel = 0.0
        self.timer_powerup = 0.0

    @property
    def esta_invencivel(self):
        return self.timer_invencivel > 0

    @property
    def powerup_ativo(self):
        return self.timer_powerup > 0

    @property
    def multiplicador_dano(self):
        return 2.0 if self.powerup_ativo else 1.0

    def selecionar_torre(self, tipo_tecla):
        if tipo_tecla == 1:
            self.selecao = (
                EstadoSelecaoTorre.NENHUMA
                if self.selecao == EstadoSelecaoTorre.ATORDOAMENTO
                else EstadoSelecaoTorre.ATORDOAMENTO
            )
        elif tipo_tecla == 2:
            self.selecao = (
                EstadoSelecaoTorre.NENHUMA
                if self.selecao == EstadoSelecaoTorre.AREA
                else EstadoSelecaoTorre.AREA
            )

    def cancelar_selecao(self):
        self.selecao = EstadoSelecaoTorre.NENHUMA

    def levar_dano(self, quantidade=1):
        if self.esta_invencivel:
            return False
        self.vidas -= quantidade
        self.timer_invencivel = self.DURACAO_INVENCIBILIDADE
        emitir(EVT_PLAYER_DAMAGED, vidas_restantes=self.vidas)
        return True

    def coletar_powerup(self):
        self.timer_powerup = self.DURACAO_POWERUP
        emitir(EVT_POWERUP_COLLECTED)

    def atualizar(self, dt):
        if self.timer_invencivel > 0:
            self.timer_invencivel -= dt
        if self.timer_powerup > 0:
            self.timer_powerup -= dt


# ---------------------------------------------------------------------------
# Jogo principal
class Jogo:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tower Defense - Trabalho")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("arial", 18)
        self.fonte_grande = pygame.font.SysFont("arial", 42, bold=True)
        self.comprimento_caminho = comprimento_total(CAMINHO)
        self.reiniciar()

    def reiniciar(self):
        self.jogador = Jogador()
        self.inimigos = []
        self.projeteis = []
        self.torres = []
        self.powerups = []
        self.proximo_id_inimigo = 0
        self.timer_spawn = 0.0
        self.intervalo_spawn = 1.6
        self.onda = 1
        self.inimigos_para_spawn = 6
        self.inimigos_spawnados_na_onda = 0
        self.game_over = False
        self.log_eventos = []  # criar um pequeno histórico visível na tela para acompanhar os eventos

    # -----------------------------------------------------------------
    def registrar_log(self, texto):
        self.log_eventos.append(texto)
        if len(self.log_eventos) > 6:
            self.log_eventos.pop(0)

    def processar_eventos_pygame(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_1:
                    self.jogador.selecionar_torre(1)
                elif evento.key == pygame.K_2:
                    self.jogador.selecionar_torre(2)
                elif evento.key == pygame.K_ESCAPE:
                    self.jogador.cancelar_selecao()
                elif evento.key == pygame.K_r and self.game_over:
                    self.reiniciar()

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 3:
                    self.jogador.cancelar_selecao()
                elif evento.button == 1 and not self.game_over:
                    self.tratar_clique(evento.pos)

            # --- eventos customizados do jogo (comunicação entre objetos) ---
            elif evento.type == EVT_ENEMY_SPAWNED:
                self.registrar_log(f"Inimigo #{evento.inimigo.id} criado")
            elif evento.type == EVT_ENEMY_DESTROYED:
                self.registrar_log(f"Inimigo #{evento.inimigo.id} destruído")
                self.jogador.dinheiro += 12
                if random.random() < 0.18:
                    self.powerups.append(PowerUp(evento.inimigo.pos))
            elif evento.type == EVT_ENEMY_REACHED_END:
                self.registrar_log(f"Inimigo #{evento.inimigo.id} chegou ao fim!")
                dano_recebido = self.jogador.levar_dano(1)
                if dano_recebido and self.jogador.vidas <= 0:
                    self.game_over = True
            elif evento.type == EVT_PROJECTILE_CREATED:
                pass  # poderia tocar som, etc...
            elif evento.type == EVT_PROJECTILE_DESTROYED:
                pass
            elif evento.type == EVT_COLLISION:
                pass
            elif evento.type == EVT_TOWER_PLACED:
                self.registrar_log(f"Torre {TORRE_INFO[evento.torre.tipo]['nome']} posicionada")
            elif evento.type == EVT_PLAYER_DAMAGED:
                pass
            elif evento.type == EVT_POWERUP_SPAWNED:
                self.registrar_log("Power-up apareceu no mapa")
            elif evento.type == EVT_POWERUP_COLLECTED:
                self.registrar_log("Power-up coletado: dano em dobro!")

    def tratar_clique(self, pos):
        # primeiro, checa se clicou em cima de um power-up
        for pu in list(self.powerups):
            if math.hypot(pu.pos[0] - pos[0], pu.pos[1] - pos[1]) <= PowerUp.RAIO + 6:
                self.powerups.remove(pu)
                self.jogador.coletar_powerup()
                return

        if self.jogador.selecao == EstadoSelecaoTorre.NENHUMA:
            return

        tipo = (
            TipoTorre.ATORDOAMENTO
            if self.jogador.selecao == EstadoSelecaoTorre.ATORDOAMENTO
            else TipoTorre.AREA
        )
        info = TORRE_INFO[tipo]

        if self.jogador.dinheiro < info["custo"]:
            self.registrar_log("Dinheiro insuficiente!")
            return

        if dist_ponto_para_caminho(CAMINHO, *pos) < LARGURA_CAMINHO / 2 + 14:
            self.registrar_log("Não é possível construir sobre o caminho!")
            return

        for torre in self.torres:
            if math.hypot(torre.pos[0] - pos[0], torre.pos[1] - pos[1]) < Torre.RAIO_BASE * 2 + 4:
                self.registrar_log("Muito perto de outra torre!")
                return

        self.jogador.dinheiro -= info["custo"]
        self.torres.append(Torre(pos, tipo))
        self.jogador.cancelar_selecao()

    # -----------------------------------------------------------------
    def spawn_inimigos(self, dt):
        if self.inimigos_spawnados_na_onda >= self.inimigos_para_spawn:
            if not any(e.estado != EstadoInimigo.MORTO for e in self.inimigos):
                # onda concluída, prepara a próxima
                self.onda += 1
                self.inimigos_para_spawn += 2
                self.inimigos_spawnados_na_onda = 0
                self.intervalo_spawn = max(0.6, self.intervalo_spawn - 0.05)
                self.registrar_log(f"Onda {self.onda} começando!")
            return

        self.timer_spawn -= dt
        if self.timer_spawn <= 0:
            self.timer_spawn = self.intervalo_spawn
            vida = 40 + (self.onda - 1) * 12
            velocidade = 55 + (self.onda - 1) * 3
            inimigo = Inimigo(vida, velocidade, self.proximo_id_inimigo)
            self.proximo_id_inimigo += 1
            self.inimigos.append(inimigo)
            self.inimigos_spawnados_na_onda += 1

    # -----------------------------------------------------------------
    def atualizar(self, dt):
        if self.game_over:
            return

        self.jogador.atualizar(dt)
        self.spawn_inimigos(dt)

        for inimigo in self.inimigos:
            inimigo.atualizar(dt, self.comprimento_caminho)
        self.inimigos = [e for e in self.inimigos if e.estado != EstadoInimigo.MORTO]

        for torre in self.torres:
            torre.atualizar(dt, self.inimigos, self.projeteis, self.jogador.multiplicador_dano)

        for projetil in self.projeteis:
            projetil.atualizar(dt, self.inimigos)
        self.projeteis = [p for p in self.projeteis if p.vivo]

    # -----------------------------------------------------------------
    def desenhar_caminho(self):
        pygame.draw.lines(self.tela, COR_CAMINHO_BORDA, False, CAMINHO, LARGURA_CAMINHO + 8)
        pygame.draw.lines(self.tela, COR_CAMINHO, False, CAMINHO, LARGURA_CAMINHO)

    def desenhar_hud(self):
        textos = [
            f"Dinheiro: {self.jogador.dinheiro}",
            f"Vidas: {self.jogador.vidas}",
            f"Onda: {self.onda}",
        ]
        for i, txt in enumerate(textos):
            superficie = self.fonte.render(txt, True, COR_TEXTO)
            self.tela.blit(superficie, (14, 14 + i * 22))

        # estado do jogador (seleção de torre / invencibilidade / powerup)
        y = 14
        info_sel = "Nenhuma torre selecionada"
        if self.jogador.selecao == EstadoSelecaoTorre.ATORDOAMENTO:
            info_sel = f"Selecionado: Atordoante (custo {TORRE_INFO[TipoTorre.ATORDOAMENTO]['custo']})"
        elif self.jogador.selecao == EstadoSelecaoTorre.AREA:
            info_sel = f"Selecionado: Área (custo {TORRE_INFO[TipoTorre.AREA]['custo']})"
        sup = self.fonte.render(info_sel, True, (255, 255, 150))
        self.tela.blit(sup, (LARGURA - sup.get_width() - 14, y))
        y += 22

        if self.jogador.esta_invencivel:
            sup = self.fonte.render("Invencível (pós-dano)!", True, (150, 200, 255))
            self.tela.blit(sup, (LARGURA - sup.get_width() - 14, y))
            y += 22
        if self.jogador.powerup_ativo:
            sup = self.fonte.render(
                f"Power-up ativo: dano x2 ({self.jogador.timer_powerup:0.1f}s)", True, (255, 180, 60)
            )
            self.tela.blit(sup, (LARGURA - sup.get_width() - 14, y))

        # instruções/comandos
        instrucoes = "[1] Torre Atordoante   [2] Torre de Área   [ESC/botão direito] cancelar"
        sup = self.fonte.render(instrucoes, True, (180, 180, 180))
        self.tela.blit(sup, (14, ALTURA - 28))

        # log de eventos
        for i, txt in enumerate(reversed(self.log_eventos)):
            sup = self.fonte.render(txt, True, (140, 220, 140))
            self.tela.blit(sup, (14, ALTURA - 56 - i * 20))

    def desenhar_preview_torre(self):
        if self.jogador.selecao == EstadoSelecaoTorre.NENHUMA:
            return
        tipo = (
            TipoTorre.ATORDOAMENTO
            if self.jogador.selecao == EstadoSelecaoTorre.ATORDOAMENTO
            else TipoTorre.AREA
        )
        info = TORRE_INFO[tipo]
        pos = pygame.mouse.get_pos()
        s = pygame.Surface((info["alcance"] * 2, info["alcance"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 50), (info["alcance"], info["alcance"]), info["alcance"])
        self.tela.blit(s, (pos[0] - info["alcance"], pos[1] - info["alcance"]))
        pygame.draw.circle(self.tela, info["cor"], pos, Torre.RAIO_BASE, 3)

    def desenhar_game_over(self):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.tela.blit(overlay, (0, 0))
        txt = self.fonte_grande.render("GAME OVER", True, (255, 80, 80))
        self.tela.blit(txt, (LARGURA / 2 - txt.get_width() / 2, ALTURA / 2 - 60))
        txt2 = self.fonte.render(f"Você sobreviveu até a onda {self.onda}", True, COR_TEXTO)
        self.tela.blit(txt2, (LARGURA / 2 - txt2.get_width() / 2, ALTURA / 2))
        txt3 = self.fonte.render("Pressione R para reiniciar", True, COR_TEXTO)
        self.tela.blit(txt3, (LARGURA / 2 - txt3.get_width() / 2, ALTURA / 2 + 30))

    def desenhar(self):
        self.tela.fill(COR_GRAMA)
        self.desenhar_caminho()

        for torre in self.torres:
            torre.desenhar(self.tela, mostrar_alcance=True)
        for pu in self.powerups:
            pygame.draw.circle(self.tela, (255, 220, 40), (int(pu.pos[0]), int(pu.pos[1])), PowerUp.RAIO)
            pygame.draw.circle(self.tela, (120, 90, 0), (int(pu.pos[0]), int(pu.pos[1])), PowerUp.RAIO, 2)
        for inimigo in self.inimigos:
            inimigo.desenhar(self.tela)
        for projetil in self.projeteis:
            projetil.desenhar(self.tela)

        self.desenhar_preview_torre()
        self.desenhar_hud()

        if self.game_over:
            self.desenhar_game_over()

        pygame.display.flip()

    # -----------------------------------------------------------------
    def rodar(self):
        while True:
            dt = self.relogio.tick(FPS) / 1000.0
            self.processar_eventos_pygame()
            self.atualizar(dt)
            self.desenhar()


if __name__ == "__main__":
    Jogo().rodar()
