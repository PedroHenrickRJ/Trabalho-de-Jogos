import math
import random
import sys
from enum import Enum, auto

import pygame

LARGURA, ALTURA = 900, 700
FPS = 60
FASE_FINAL = 5

COR_FUNDO = (18, 18, 26)
COR_TEXTO = (235, 235, 235)
COR_DESTAQUE = (255, 210, 90)

TAMANHO_TIJOLO = (60, 26)
TAMANHO_BONUS = (28, 28)
TAMANHO_OBSTACULO = (70, 50)

# progressão de dificuldade por fase (1 a 5): muda a quantidade de linhas e
# também a vida permitida dos tijolos.
HPS_PERMITIDOS_POR_FASE = {1: [1], 2: [1, 2], 3: [1, 2, 3], 4: [5], 5: [10]}
LINHAS_POR_FASE = {1: 3, 2: 4, 3: 5, 4: 5, 5: 5}
COLUNAS_PADRAO = 10
PROB_BURACO_PADRAO = 0.08
OBSTACULOS_POR_FASE = {1: 0, 2: 0, 3: 1, 4: 2, 5: 3}


# Definição das formas
def pontos_retangulo(w, h):
    return [(0, 0), (w, 0), (w, h), (0, h)]


def pontos_triangulo(w, h):
    return [(w / 2, 0), (w, h), (0, h)]


def pontos_diamante(w, h):
    return [(w / 2, 0), (w, h / 2), (w / 2, h), (0, h / 2)]


def pontos_hexagono(w, h):
    return [
        (w * 0.25, 0), (w * 0.75, 0), (w, h / 2),
        (w * 0.75, h), (w * 0.25, h), (0, h / 2),
    ]


def pontos_seta(w, h):
    return [(0, 0), (w, 0), (w, h * 0.5), (w * 0.5, h), (0, h * 0.5)]


def pontos_estrela(w, h):
    cx, cy = w / 2, h / 2
    raio_ext = min(w, h) / 2
    raio_int = raio_ext * 0.45
    pontos = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = raio_ext if i % 2 == 0 else raio_int
        pontos.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pontos


def pontos_rocha(w, h):
    # polígono irregular fixo simulando uma rocha (obstáculo indestrutível)
    return [
        (0, h * 0.4), (w * 0.15, 0), (w * 0.6, h * 0.05),
        (w, h * 0.35), (w * 0.85, h), (w * 0.2, h * 0.95),
    ]


def _arredondar(pontos):
    return [(int(round(x)), int(round(y))) for x, y in pontos]


FORMAS_PONTOS = {
    "retangulo": pontos_retangulo(*TAMANHO_TIJOLO),
    "triangulo": pontos_triangulo(*TAMANHO_TIJOLO),
    "diamante": pontos_diamante(*TAMANHO_TIJOLO),
    "hexagono": pontos_hexagono(*TAMANHO_TIJOLO),
    "seta": pontos_seta(*TAMANHO_TIJOLO),
}
PONTOS_ESTRELA = pontos_estrela(*TAMANHO_BONUS)
PONTOS_ROCHA = pontos_rocha(*TAMANHO_OBSTACULO)


def criar_mascara_poligono(pontos, tamanho):
    #Desenha o polígono numa Surface com canal alfa e extrai a Mask dele.
    #A cor não importa para a máscara, só a forma (o que está opaco vira
    #parte da máscara de colisão).
    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill((0, 0, 0, 0))
    pygame.draw.polygon(superficie, (255, 255, 255, 255), _arredondar(pontos))
    return pygame.mask.from_surface(superficie)


def criar_mascara_circulo(raio):
    tamanho = (raio * 2, raio * 2)
    superficie = pygame.Surface(tamanho, pygame.SRCALPHA)
    superficie.fill((0, 0, 0, 0))
    pygame.draw.circle(superficie, (255, 255, 255, 255), (raio, raio), raio)
    return pygame.mask.from_surface(superficie)



# Função central de colisão por máscara (usada só quando precisamos refletir)
def normal_da_colisao(bola, alvo):
    #Retorna um vetor normal (nx, ny) estimado da colisão entre a bola e um
    # alvo qualquer (que tenha .rect e .mask), ou None se não há sobreposição
    offset = (alvo.rect.x - bola.rect.x, alvo.rect.y - bola.rect.y)
    if bola.mask.overlap(alvo.mask, offset) is None:
        return None

    sobreposicao = bola.mask.overlap_mask(alvo.mask, offset)
    if sobreposicao.count() == 0:
        return None

    cx, cy = sobreposicao.centroid()  # coordenadas relativas ao rect da bola
    centro_sobreposicao = (bola.rect.x + cx, bola.rect.y + cy)
    centro_bola = bola.rect.center

    nx = centro_bola[0] - centro_sobreposicao[0]
    ny = centro_bola[1] - centro_sobreposicao[1]
    dist = math.hypot(nx, ny)
    if dist < 0.01:
        return (0.0, -1.0)
    return (nx / dist, ny / dist)


def refletir_bola(bola, normal):
    nx, ny = normal
    produto_escalar = bola.vx * nx + bola.vy * ny
    bola.vx -= 2 * produto_escalar * nx
    bola.vy -= 2 * produto_escalar * ny
    # empurra a bola pra fora ao longo da normal, pra não colidir de novo
    # com o mesmo alvo no próximo frame 
    bola.x += nx * 6
    bola.y += ny * 6
    bola.sincronizar_rect()

# ------------ bola --------------------------------
class Bola:
    RAIO = 9

    def __init__(self, x, y, vx, vy, dano, mascara):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.dano = dano
        self.raio = self.RAIO
        self.mask = mascara
        self.rect = pygame.Rect(0, 0, self.raio * 2, self.raio * 2)
        self.sincronizar_rect()

    def sincronizar_rect(self):
        self.rect.center = (round(self.x), round(self.y))

    def mover(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.sincronizar_rect()

    def desenhar(self, tela):
        pygame.draw.circle(tela, (255, 255, 255), self.rect.center, self.raio)
        pygame.draw.circle(tela, (150, 150, 255), self.rect.center, self.raio, 2)



# Raquete (retângulo simples, colisão sem máscra) 
class Raquete:
    ALTURA = 18

    def __init__(self, largura, vida_maxima):
        self.largura = largura
        self.vida = vida_maxima
        self.rect = pygame.Rect(0, 0, largura, self.ALTURA)
        self.rect.centerx = LARGURA // 2
        self.rect.bottom = ALTURA - 30

    def definir_largura(self, nova_largura):
        centro = self.rect.centerx
        self.largura = nova_largura
        self.rect.width = nova_largura
        self.rect.centerx = centro

    def mover_para(self, x):
        self.rect.centerx = max(self.largura // 2, min(LARGURA - self.largura // 2, x))

    def desenhar(self, tela, vida_maxima):
        pygame.draw.rect(tela, (90, 200, 140), self.rect, border_radius=6)
        pygame.draw.rect(tela, (20, 20, 20), self.rect, 2, border_radius=6)

        largura_barra = self.largura
        x = self.rect.left
        y = self.rect.bottom + 6
        pct = max(0, self.vida) / vida_maxima if vida_maxima > 0 else 0
        pygame.draw.rect(tela, (70, 20, 20), (x, y, largura_barra, 7))
        pygame.draw.rect(tela, (80, 220, 100), (x, y, largura_barra * pct, 7))
        pygame.draw.rect(tela, (15, 15, 18), (x, y, largura_barra, 7), 1)


def colidir_raquete(bola, raquete):
    #Colisão sem máscara
    if bola.vy <= 0:
        return False
    cx = max(raquete.rect.left, min(bola.x, raquete.rect.right))
    cy = max(raquete.rect.top, min(bola.y, raquete.rect.bottom))
    dist = math.hypot(bola.x - cx, bola.y - cy)
    if dist > bola.raio:
        return False

    rel = (bola.x - raquete.rect.centerx) / (raquete.largura / 2)
    rel = max(-1.0, min(1.0, rel))
    velocidade = math.hypot(bola.vx, bola.vy)
    angulo = rel * math.radians(65)
    bola.vx = velocidade * math.sin(angulo)
    bola.vy = -abs(velocidade * math.cos(angulo))
    bola.y = raquete.rect.top - bola.raio - 1
    bola.sincronizar_rect()
    return True


# ---------------------------------------------------------------------------
# Tijolo (forma irregular, bloueia, dá pontos e moedas)
CORES_POR_HP = {
    1: (150, 220, 150), 2: (110, 200, 110), 3: (230, 210, 70),
    5: (230, 140, 60), 10: (200, 70, 70),
}


class Tijolo:
    def __init__(self, x, y, forma, hp, mascara):
        self.forma = forma
        self.hp = hp
        self.hp_max = hp
        self.mask = mascara
        largura, altura = mascara.get_size()
        self.rect = pygame.Rect(int(x), int(y), largura, altura)
        self.pontos_locais = _arredondar(FORMAS_PONTOS[forma])
        self.vivo = True

    def levar_dano(self, dano):
        self.hp -= dano
        if self.hp <= 0:
            self.vivo = False

    def desenhar(self, tela, fonte):
        pontos_mundo = [(self.rect.x + px, self.rect.y + py) for px, py in self.pontos_locais]
        cor = CORES_POR_HP.get(self.hp_max, (180, 180, 180))
        pygame.draw.polygon(tela, cor, pontos_mundo)
        pygame.draw.polygon(tela, (20, 20, 20), pontos_mundo, 2)
        txt = fonte.render(str(self.hp), True, (20, 20, 20))
        tela.blit(txt, txt.get_rect(center=self.rect.center))


# ---------------------------------------------------------------------------
# Zona Bônus/estrela (forma irregular, NÃO bloqueia a bola, só DÁ PONTOS e MOEDAS)
class ZonaBonus:
    def __init__(self, x, y, mascara, moedas=15):
        self.mask = mascara
        largura, altura = mascara.get_size()
        self.rect = pygame.Rect(int(x), int(y), largura, altura)
        self.pontos_locais = _arredondar(PONTOS_ESTRELA)
        self.valor_moedas = moedas
        self.coletado = False

    def desenhar(self, tela):
        pontos_mundo = [(self.rect.x + px, self.rect.y + py) for px, py in self.pontos_locais]
        pygame.draw.polygon(tela, COR_DESTAQUE, pontos_mundo)
        pygame.draw.polygon(tela, (140, 100, 10), pontos_mundo, 2)


# ---------------------------------------------------------------------------
# Obstáculo/Pedra (forma irregular, BLOQUEIA mas NÃO dá pontos, indestrutível)
class Obstaculo:
    def __init__(self, x, y, mascara):
        self.mask = mascara
        largura, altura = mascara.get_size()
        self.rect = pygame.Rect(int(x), int(y), largura, altura)
        self.pontos_locais = _arredondar(PONTOS_ROCHA)

    def desenhar(self, tela):
        pontos_mundo = [(self.rect.x + px, self.rect.y + py) for px, py in self.pontos_locais]
        pygame.draw.polygon(tela, (120, 115, 110), pontos_mundo)
        pygame.draw.polygon(tela, (60, 55, 50), pontos_mundo, 2)


# ---------------------------------------------------------------------------
# Upgrades (permanentes durante a run, comprados com moedas na loja)
UPGRADE_INFO = {
    "raquete": dict(nome="Raquete Maior", custo_base=40, incremento=25, nivel_max=20, passo=22),
    "bola": dict(nome="Bola Extra", custo_base=90, incremento=70, nivel_max=20, passo=1),
    "dano": dict(nome="Dano da Bola", custo_base=60, incremento=45, nivel_max=20, passo=1),
    "vida": dict(nome="Vida da Raquete", custo_base=35, incremento=20, nivel_max=20, passo=5),
}


class Upgrades:
    def __init__(self):
        self.niveis = {"raquete": 0, "bola": 0, "dano": 0, "vida": 0}

    def largura_raquete(self):
        return 110 + self.niveis["raquete"] * UPGRADE_INFO["raquete"]["passo"]

    def bolas_iniciais(self):
        return 1 + self.niveis["bola"]

    def dano_base(self):
        return 1 + self.niveis["dano"]

    def vida_maxima(self):
        return 5 + self.niveis["vida"] * UPGRADE_INFO["vida"]["passo"]

    def custo_atual(self, chave):
        info = UPGRADE_INFO[chave]
        return info["custo_base"] + info["incremento"] * self.niveis[chave]

    def no_maximo(self, chave):
        return self.niveis[chave] >= UPGRADE_INFO[chave]["nivel_max"]

    def comprar(self, chave, moedas_disponiveis):
        if self.no_maximo(chave):
            return False, moedas_disponiveis, "Upgrade no nível máximo!"
        custo = self.custo_atual(chave)
        if moedas_disponiveis < custo:
            return False, moedas_disponiveis, "Moedas insuficientes!"
        self.niveis[chave] += 1
        return True, moedas_disponiveis - custo, None


# ---------------------------------------------------------------------------
# Botão simples (usado na loja)
class Botao:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def clicado(self, pos):
        return self.rect.collidepoint(pos)

    def desenhar(self, tela, fonte, texto, cor_fundo=(55, 58, 70)):
        pygame.draw.rect(tela, cor_fundo, self.rect, border_radius=8)
        pygame.draw.rect(tela, (15, 15, 18), self.rect, 2, border_radius=8)
        sup = fonte.render(texto, True, (240, 240, 240))
        tela.blit(sup, sup.get_rect(center=self.rect.center))


# ---------------------------------------------------------------------------
# Estados do jogo
class Estado(Enum):
    MENU = auto()
    JOGANDO = auto()
    LOJA = auto()
    VITORIA = auto()


# ---------------------------------------------------------------------------
# Jogo principal
class Jogo:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Breakout Roguelike: Colisão por Máscara")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("arial", 18)
        self.fonte_pequena = pygame.font.SysFont("arial", 14, bold=True)
        self.fonte_grande = pygame.font.SysFont("arial", 40, bold=True)

        # máscaras criadas UMA VEZ e reaproveitadas por todos os objetos da
        # mesma forma (só a posição/rect muda de objeto para objeto)
        self.mascaras_tijolo = {
            forma: criar_mascara_poligono(pontos, TAMANHO_TIJOLO)
            for forma, pontos in FORMAS_PONTOS.items()
        }
        self.mascara_estrela = criar_mascara_poligono(PONTOS_ESTRELA, TAMANHO_BONUS)
        self.mascara_rocha = criar_mascara_poligono(PONTOS_ROCHA, TAMANHO_OBSTACULO)
        self.mascara_bola = criar_mascara_circulo(Bola.RAIO)

        self.botoes_loja = {
            "raquete": Botao((LARGURA / 2 - 180, 225, 360, 50)),
            "bola": Botao((LARGURA / 2 - 180, 285, 360, 50)),
            "dano": Botao((LARGURA / 2 - 180, 345, 360, 50)),
            "vida": Botao((LARGURA / 2 - 180, 405, 360, 50)),
            "continuar": Botao((LARGURA / 2 - 150, 480, 300, 56)),
        }
        # Botão de debug: adiciona 500 moedas imediatamente.
        self.botao_debug_dinheiro = Botao((LARGURA - 170, 54, 155, 34))

        self.estado = Estado.MENU
        self.log_eventos = []
        self.iniciar_run()


    def registrar_log(self, texto):
        self.log_eventos.append(texto)
        if len(self.log_eventos) > 6:
            self.log_eventos.pop(0)


    def iniciar_run(self):
        self.nivel = 1
        self.moedas = 0
        self.pontuacao = 0
        self.upgrades = Upgrades()
        self.raquete = Raquete(self.upgrades.largura_raquete(), self.upgrades.vida_maxima())
        self.bolas = []
        self.bolas_lancadas = False
        self.aguardando_avanco_de_fase = False
        self.tijolos, self.obstaculos, self.zonas_bonus = self.gerar_fase(self.nivel)
        self.estado = Estado.MENU
        self.log_eventos = []

    def comecar_a_jogar(self):
        self.estado = Estado.JOGANDO

    def gerar_fase(self, nivel):
        tijolos = []
        formas_possiveis = list(FORMAS_PONTOS.keys())
        hps_permitidos = HPS_PERMITIDOS_POR_FASE.get(nivel, [10])
        linhas = LINHAS_POR_FASE.get(nivel, 5)

        espaco_x = TAMANHO_TIJOLO[0] + 12
        margem_x = (LARGURA - COLUNAS_PADRAO * espaco_x) / 2
        y0 = 70

        for linha in range(linhas):
            for col in range(COLUNAS_PADRAO):
                if random.random() < PROB_BURACO_PADRAO:  # pequena variação visual
                    continue
                forma = random.choice(formas_possiveis)
                hp = random.choice(hps_permitidos)
                x = margem_x + col * espaco_x
                y = y0 + linha * (TAMANHO_TIJOLO[1] + 10)
                tijolos.append(Tijolo(x, y, forma, hp, self.mascaras_tijolo[forma]))

        fundo_tijolos = y0 + linhas * (TAMANHO_TIJOLO[1] + 10)

        zonas_bonus = []
        for _ in range(random.randint(1, 3)):
            x = random.uniform(60, LARGURA - 60 - TAMANHO_BONUS[0])
            y = random.uniform(y0, fundo_tijolos)
            zonas_bonus.append(ZonaBonus(x, y, self.mascara_estrela))

        obstaculos = []
        for _ in range(OBSTACULOS_POR_FASE.get(nivel, 3)):
            x = random.uniform(80, LARGURA - 80 - TAMANHO_OBSTACULO[0])
            y = random.uniform(fundo_tijolos + 20, ALTURA * 0.62)
            obstaculos.append(Obstaculo(x, y, self.mascara_rocha))

        return tijolos, obstaculos, zonas_bonus

    def lancar_bolas(self):
        quantidade = self.upgrades.bolas_iniciais()
        dano = self.upgrades.dano_base()
        x0, y0 = self.raquete.rect.centerx, self.raquete.rect.top - Bola.RAIO - 1
        for i in range(quantidade):
            espalhamento = (i - (quantidade - 1) / 2) * 12
            angulo = math.radians(espalhamento)
            velocidade = 360
            vx = velocidade * math.sin(angulo)
            vy = -velocidade * math.cos(angulo)
            self.bolas.append(Bola(x0, y0, vx, vy, dano, self.mascara_bola))
        self.bolas_lancadas = True
        self.registrar_log(f"{quantidade} bola(s) lançada(s)!")

    def perder_fase(self):
        #Todas as bolas caíram sem tocar a raquete:A fase é reiniciada do zero
        #e o jogador perde TODAS as moedas e pontuação acumuladas.
        self.registrar_log("Todas as bolas caíram! Fase perdida - moedas e pontuação zeradas.")
        self.moedas = 0
        self.pontuacao = 0
        self.raquete.vida = self.upgrades.vida_maxima()
        self.tijolos, self.obstaculos, self.zonas_bonus = self.gerar_fase(self.nivel)
        self.bolas = []
        self.bolas_lancadas = False

    def ir_para_loja(self, concluiu_fase):
        """Manda o jogador pra loja. Isso acontece em dois casos:
        1- a vida da raquete zerou no meio da fase (ao
        continuar, a MESMA fase é sorteada de novo do zero: o jogador
        tenta de novo com um tabuleiro novo, até ter upgrades suficientes
        pra limpar ela) ou
        2- todos os tijolos da fase foram destruídos
        (aí, ao continuar, vamos pra próxima fase, também com tabuleiro
        novo e mais difícil)."""

        self.aguardando_avanco_de_fase = concluiu_fase
        self.bolas = []
        self.bolas_lancadas = False
        self.estado = Estado.LOJA
        if concluiu_fase:
            self.registrar_log(f"Fase {self.nivel} concluída! Bem-vindo à loja.")
        else:
            self.registrar_log("A raquete ficou sem vida! Hora de comprar upgrades.")

    def continuar_da_loja(self):
        if self.aguardando_avanco_de_fase:
            if self.nivel >= FASE_FINAL:
                self.estado = Estado.VITORIA
                return
            self.nivel += 1
        # tanto ao avançar de fase quanto ao tentar de novo a mesma fase
        # (vida zerada), o tabuleiro é sempre gerado do zero - se a vida
        # acabar, o jogador enfrenta a MESMA fase outra vez com um layout
        # novo, até conseguir upgrades suficientes pra limpar ela de vez.
        self.tijolos, self.obstaculos, self.zonas_bonus = self.gerar_fase(self.nivel)

        self.raquete.definir_largura(self.upgrades.largura_raquete())
        self.raquete.vida = self.upgrades.vida_maxima()
        self.bolas = []
        self.bolas_lancadas = False
        self.estado = Estado.JOGANDO

    def comprar_upgrade(self, chave):
        sucesso, novas_moedas, motivo_falha = self.upgrades.comprar(chave, self.moedas)
        if sucesso:
            self.moedas = novas_moedas
            self.registrar_log(f"Upgrade comprado: {UPGRADE_INFO[chave]['nome']}")
        else:
            self.registrar_log(motivo_falha)


    def processar_eventos_pygame(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    if self.estado == Estado.MENU:
                        self.comecar_a_jogar()
                    elif self.estado == Estado.JOGANDO and not self.bolas_lancadas:
                        self.lancar_bolas()
                elif evento.key == pygame.K_r and self.estado == Estado.VITORIA:
                    self.iniciar_run()

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.estado == Estado.MENU:
                    self.comecar_a_jogar()
                elif self.estado in (Estado.JOGANDO, Estado.LOJA):
                    if self.botao_debug_dinheiro.clicado(evento.pos):
                        self.adicionar_dinheiro_debug()
                    elif self.estado == Estado.LOJA:
                        self.tratar_clique_loja(evento.pos)

    def adicionar_dinheiro_debug(self):
        #Botão de debug: adiciona 500 moedas imediatamente
        self.moedas += 500
        self.registrar_log("DEBUG: +500 moedas")

    def tratar_clique_loja(self, pos):
        for chave, botao in self.botoes_loja.items():
            if botao.clicado(pos):
                if chave == "continuar":
                    self.continuar_da_loja()
                else:
                    self.comprar_upgrade(chave)
                return

    def atualizar(self, dt):
        if self.estado != Estado.JOGANDO:
            return

        self.raquete.mover_para(pygame.mouse.get_pos()[0])

        if not self.bolas_lancadas:
            return

        for bola in self.bolas:
            bola.mover(dt)
            self._colidir_paredes(bola)
            if colidir_raquete(bola, self.raquete):
                self.raquete.vida -= 1
                self.registrar_log(f"Ricochete na raquete! Vida: {max(self.raquete.vida, 0)}")
            self._colidir_tijolos(bola)
            self._colidir_obstaculos(bola)
            self._colidir_bonus(bola)

        self.bolas = [b for b in self.bolas if b.y - b.raio <= ALTURA]
        self.tijolos = [t for t in self.tijolos if t.vivo]

        # a vida da raquete zerou -> pausa a fase e manda pra loja
        if self.raquete.vida <= 0:
            self.ir_para_loja(concluiu_fase=False)
            return

        # todas as bolas caíram sem tocar a raquete -> perde a fase e as moedas
        if self.bolas_lancadas and not self.bolas:
            self.perder_fase()
            return

        # tabuleiro limpo -> fase concluída, vai pra loja
        if not self.tijolos:
            self.ir_para_loja(concluiu_fase=True)

    def _colidir_paredes(self, bola):
        if bola.x - bola.raio <= 0:
            bola.x = bola.raio
            bola.vx = abs(bola.vx)
        elif bola.x + bola.raio >= LARGURA:
            bola.x = LARGURA - bola.raio
            bola.vx = -abs(bola.vx)
        if bola.y - bola.raio <= 0:
            bola.y = bola.raio
            bola.vy = abs(bola.vy)
        bola.sincronizar_rect()

    def _colidir_tijolos(self, bola):
        for tijolo in self.tijolos:
            if not tijolo.vivo:
                continue
            normal = normal_da_colisao(bola, tijolo)
            if normal is not None:
                refletir_bola(bola, normal)
                tijolo.levar_dano(bola.dano)
                if tijolo.vivo:
                    self.registrar_log(f"Tijolo {tijolo.forma} atingido (-{bola.dano})")
                else:
                    moedas_ganhas = tijolo.hp_max * 5
                    self.moedas += moedas_ganhas
                    self.pontuacao += 10
                    self.registrar_log(
                        f"Tijolo {tijolo.forma} destruído! +{moedas_ganhas} moedas"
                    )
                break  

    def _colidir_obstaculos(self, bola):
        for obstaculo in self.obstaculos:
            normal = normal_da_colisao(bola, obstaculo)
            if normal is not None:
                refletir_bola(bola, normal)  # bloqueia/reflete, mas NÃO dá pontos
                break

    def _colidir_bonus(self, bola):
        for zona in self.zonas_bonus:
            if zona.coletado:
                continue
            offset = (zona.rect.x - bola.rect.x, zona.rect.y - bola.rect.y)
            # aqui só precisamos saber SE colidiu, a trajetória da bola não vai ser alterada
            if bola.mask.overlap(zona.mask, offset) is not None:
                zona.coletado = True
                self.moedas += zona.valor_moedas
                self.pontuacao += zona.valor_moedas * 2
                self.registrar_log(f"Bônus coletado (+{zona.valor_moedas} moedas, sem desviar a bola)")
        self.zonas_bonus = [z for z in self.zonas_bonus if not z.coletado]

    def desenhar_hud(self):
        textos = [
            f"Fase: {self.nivel}/{FASE_FINAL}",
            f"Moedas: {self.moedas}",
            f"Pontuação: {self.pontuacao}",
            f"Vida da raquete: {max(self.raquete.vida, 0)}/{self.upgrades.vida_maxima()}",
        ]
        for i, txt in enumerate(textos):
            sup = self.fonte.render(txt, True, COR_TEXTO)
            self.tela.blit(sup, (14, 14 + i * 22))

        resumo = (
            f"Raquete nv{self.upgrades.niveis['raquete']}  "
            f"Bolas: {self.upgrades.bolas_iniciais()}  "
            f"Dano: {self.upgrades.dano_base()}"
        )
        sup = self.fonte.render(resumo, True, (170, 200, 255))
        self.tela.blit(sup, (LARGURA - sup.get_width() - 14, 14))

        self.botao_debug_dinheiro.desenhar(
            self.tela, self.fonte_pequena, "+500 MOEDAS (DEBUG)", (95, 70, 110)
        )

        if not self.bolas_lancadas:
            sup = self.fonte.render("Pressione ESPAÇO para lançar a(s) bola(s)", True, COR_DESTAQUE)
            self.tela.blit(sup, (LARGURA / 2 - sup.get_width() / 2, ALTURA - 60))

        for i, txt in enumerate(reversed(self.log_eventos)):
            sup = self.fonte_pequena.render(txt, True, (140, 220, 140))
            self.tela.blit(sup, (14, ALTURA - 30 - i * 18))

    def desenhar_bola_presa(self):
        if self.bolas_lancadas:
            return
        pos = (self.raquete.rect.centerx, self.raquete.rect.top - Bola.RAIO - 1)
        pygame.draw.circle(self.tela, (255, 255, 255), pos, Bola.RAIO)

    def desenhar_menu(self):
        titulo = self.fonte_grande.render("BREAKOUT ROGUELIKE", True, COR_DESTAQUE)
        self.tela.blit(titulo, (LARGURA / 2 - titulo.get_width() / 2, 140))
        linhas = [
            "Mova o Mouse para controlar a raquete. Espaço lança as bolas.",
            "Cada Tijolo destruído dá 5 moedas por HP. A partir da segunda fase, os tijolos podem ter mais HP",
            "Cada ricochete da bola na raquete tira 1 ponto da barra de vida dela.",
            "Deixar TODAS as bolas caírem perde a fase e zera suas moedas e pontuação",
            "Quando a vida da raquete zera, você vai pra loja comprar upgrades e tentar a fase de novo.",
            "Ao colidir com a estrela dourada, a bola não é desviada e concede pontos.",
            "A partir da fase 2, obstáculos (pedras) aparecem e bloueiam a bola, mas não dão pontos",
            "Pressione ESPAÇO para começar",
        ]
        for i, linha in enumerate(linhas):
            sup = self.fonte.render(linha, True, COR_TEXTO)
            self.tela.blit(sup, (LARGURA / 2 - sup.get_width() / 2, 260 + i * 28))

    def desenhar_loja(self):
        if self.aguardando_avanco_de_fase:
            titulo_txt = f"LOJA - Fase {self.nivel} concluída!"
        else:
            titulo_txt = f"LOJA - Vida da raquete zerou (Fase {self.nivel})"
        titulo = self.fonte_grande.render(titulo_txt, True, COR_DESTAQUE)
        self.tela.blit(titulo, (LARGURA / 2 - titulo.get_width() / 2, 90))
        sup = self.fonte.render(f"Moedas disponíveis: {self.moedas}", True, COR_TEXTO)
        self.tela.blit(sup, (LARGURA / 2 - sup.get_width() / 2, 160))

        self.botao_debug_dinheiro.desenhar(
            self.tela, self.fonte_pequena, "+500 MOEDAS (DEBUG)", (95, 70, 110)
        )

        for chave, botao in self.botoes_loja.items():
            if chave == "continuar":
                if self.aguardando_avanco_de_fase and self.nivel >= FASE_FINAL:
                    texto = "Concluir o jogo!"
                elif self.aguardando_avanco_de_fase:
                    texto = f"Avançar para a Fase {self.nivel + 1}"
                else:
                    texto = f"Tentar a Fase {self.nivel} de novo (tabuleiro novo, vida reposta)"
                botao.desenhar(self.tela, self.fonte, texto, (70, 130, 90))
                continue
            info = UPGRADE_INFO[chave]
            nivel_atual = self.upgrades.niveis[chave]
            if self.upgrades.no_maximo(chave):
                texto = f"{info['nome']} - NÍVEL MÁXIMO ({nivel_atual}/{info['nivel_max']})"
                cor = (50, 50, 55)
            else:
                custo = self.upgrades.custo_atual(chave)
                texto = f"{info['nome']} (nv {nivel_atual}/{info['nivel_max']}) - custa {custo} moedas"
                cor = (55, 58, 70)
            botao.desenhar(self.tela, self.fonte, texto, cor)

        for i, txt in enumerate(reversed(self.log_eventos[-3:])):
            sup = self.fonte_pequena.render(txt, True, (140, 220, 140))
            self.tela.blit(sup, (LARGURA / 2 - sup.get_width() / 2, 560 + i * 18))

    def desenhar_vitoria(self):
        txt = self.fonte_grande.render("VOCÊ VENCEU O JOGO!", True, (120, 230, 140))
        self.tela.blit(txt, (LARGURA / 2 - txt.get_width() / 2, ALTURA / 2 - 80))
        txt2 = self.fonte.render(
            f"Todas as {FASE_FINAL} fases concluídas com {self.pontuacao} pontos!", True, COR_TEXTO
        )
        self.tela.blit(txt2, (LARGURA / 2 - txt2.get_width() / 2, ALTURA / 2 - 10))
        txt3 = self.fonte.render("Pressione R para jogar uma nova run", True, COR_TEXTO)
        self.tela.blit(txt3, (LARGURA / 2 - txt3.get_width() / 2, ALTURA / 2 + 20))

    def desenhar(self):
        self.tela.fill(COR_FUNDO)

        if self.estado == Estado.MENU:
            self.desenhar_menu()
        elif self.estado == Estado.JOGANDO:
            for obstaculo in self.obstaculos:
                obstaculo.desenhar(self.tela)
            for zona in self.zonas_bonus:
                zona.desenhar(self.tela)
            for tijolo in self.tijolos:
                tijolo.desenhar(self.tela, self.fonte_pequena)
            self.raquete.desenhar(self.tela, self.upgrades.vida_maxima())
            self.desenhar_bola_presa()
            for bola in self.bolas:
                bola.desenhar(self.tela)
            self.desenhar_hud()
        elif self.estado == Estado.LOJA:
            self.desenhar_loja()
        elif self.estado == Estado.VITORIA:
            self.desenhar_vitoria()

        pygame.display.flip()

    def rodar(self):
        while True:
            dt = self.relogio.tick(FPS) / 1000.0
            self.processar_eventos_pygame()
            self.atualizar(dt)
            self.desenhar()


if __name__ == "__main__":
    Jogo().rodar()