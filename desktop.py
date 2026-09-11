import os

import pygame
import requests

from data_loader import load
from engine import Akinator

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
CACHE = os.path.join(HERE, ".cache", "portraits")

SIZE = (1200, 720)
GENIE = pygame.Rect(18, 265, 300, 430)
STAGE = pygame.Rect(336, 92, 548, 568)
SIDE = pygame.Rect(906, 92, 276, 568)

ANSWERS = [("yes", "Yes"), ("probably", "Probably"), ("idk", "Don't know"),
           ("probably not", "Probably not"), ("no", "No")]
KEYS = {pygame.K_1: "yes", pygame.K_2: "probably", pygame.K_3: "idk",
        pygame.K_4: "probably not", pygame.K_5: "no"}


def portrait(url, hero):
    os.makedirs(CACHE, exist_ok=True)
    name = "".join(c for c in hero.lower().replace(" ", "_") if c.isalnum() or c == "_")
    path = os.path.join(CACHE, name + ".png")

    if not os.path.exists(path):
        try:
            data = requests.get(url, timeout=10).content
        except requests.RequestException:
            return None
        with open(path, "wb") as f:
            f.write(data)
    try:
        return pygame.image.load(path).convert_alpha()
    except pygame.error:
        return None
TEXT = (238, 240, 244)
DIM = (176, 182, 194)
LINE = (92, 100, 116)
ACCENT = (194, 59, 34)
ACCENT_SOFT = (96, 38, 28)

def fit(image, box):
    scale = min(box.width / image.get_width(), box.height / image.get_height())
    size = (round(image.get_width() * scale), round(image.get_height() * scale))
    return pygame.transform.smoothscale(image, size)


def cover(image, size):
    scale = max(size[0] / image.get_width(), size[1] / image.get_height())
    return pygame.transform.smoothscale(
        image, (round(image.get_width() * scale), round(image.get_height() * scale)))


def panel(screen, rect, alpha=170):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (12, 14, 18, alpha), layer.get_rect())
    pygame.draw.rect(layer, (*LINE, 120), layer.get_rect(), width=1)
    screen.blit(layer, rect.topleft)


def ellipsize(font, text, width):
    if font.size(text)[0] <= width:
        return text
    cut = text
    while cut and font.size(cut + "…")[0] > width:
        cut = cut[:-1]
    return cut + "…"


def wrap(font, text, width):
    lines, line = [], ""
    for word in text.split():
        probe = (line + " " + word).strip()
        if not line or font.size(probe)[0] <= width:
            line = probe
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


class Desktop:
    def __init__(self):
        heroes, questions, traits, images = load(
            os.path.join(HERE, "heroes.csv"), os.path.join(HERE, "questions.csv"))
        self.images = images
        self.game = Akinator(heroes, questions, traits)

        pygame.init()
        pygame.display.set_caption("Dota Akinator")
        self.screen = pygame.display.set_mode(SIZE)
        self.clock = pygame.time.Clock()
        self.big = pygame.font.Font(None, 46)
        self.small = pygame.font.Font(None, 28)
        self.tiny = pygame.font.Font(None, 23)

        self.background = cover(pygame.image.load(
            os.path.join(ASSETS, "background.jpg")).convert(), SIZE)
        self.genie = fit(pygame.image.load(
            os.path.join(ASSETS, "akinator.png")).convert_alpha(), GENIE)
        self.scrim = pygame.Surface(SIZE, pygame.SRCALPHA)
        self.scrim.fill((10, 12, 16, 150))
        self.start()

    def start(self):
        self.game.reset()
        self.guesses = 0
        self.picture = None
        self.buttons = []
        self.message = ""
        self.advance()

    def advance(self):
        if self.game.should_guess():
            self.hero = self.game.best_guess()
            self.picture = portrait(self.images[self.hero], self.game.heroes[self.hero])
            self.state = "guessing"
        else:
            self.question, _ = self.game.next_question()
            self.state = "asking"

    def answer(self, value):
        self.game.answer(self.question, value)
        self.advance()

    def confirm(self, correct):
        if correct:
            self.message = f"Guessed it in {len(self.game.asked)} questions. (EZ)"
            self.state = "over"
            return

        self.guesses += 1
        if self.guesses >= self.game.max_guesses or len(self.game.asked) >= self.game.max_questions:
            self.message = "I give up. Who was it tho?"
            self.state = "over"
            return

        self.game.reject(self.hero)
        self.advance()

    def button(self, rect, label, accent=False):
        fill = ACCENT_SOFT if accent else (46, 52, 64)
        if rect.collidepoint(pygame.mouse.get_pos()):
            fill = tuple(min(255, c + 22) for c in fill)
        pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(self.screen, LINE, rect, width=1)
        text = self.small.render(label, True, TEXT)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_header(self):
        hint = "1 Yes   2 Probably   3 Don't know   4 Probably not   5 No  R restart    Esc quit"
        self.screen.blit(self.tiny.render(hint, True, DIM), (50, 15))

    def draw_meter(self):
        asked = len(self.game.asked)
        left = self.tiny.render(f"{asked} of {self.game.max_questions} questions", True, DIM)
        # right = self.tiny.render(f"{self.game.entropy():.1f} bits left", True, DIM)
        self.screen.blit(left, (STAGE.x + 22, STAGE.y + 20))
        # self.screen.blit(right, (STAGE.right - 22 - right.get_width(), STAGE.y + 20))

        track = pygame.Rect(STAGE.x + 22, STAGE.y + 48, STAGE.width - 44, 3)
        pygame.draw.rect(self.screen, LINE, track)
        width = int(track.width * min(1.0, asked / self.game.max_questions))
        if width:
            pygame.draw.rect(self.screen, ACCENT, pygame.Rect(track.x, track.y, width, 3))

    def draw_asking(self):
        y = STAGE.y + 88
        for line in wrap(self.big, self.game.questions[self.question], STAGE.width - 44):
            self.screen.blit(self.big.render(line, True, TEXT), (STAGE.x + 22, y))
            y += 46
        self.buttons = []
        for i, (value, label) in enumerate(ANSWERS):
            rect = pygame.Rect(STAGE.x + 22, STAGE.y + 254 + i * 54, STAGE.width - 44, 46)
            self.button(rect, label, accent=value == "yes")
            self.buttons.append((rect, ("answer", value)))

    def draw_guessing(self):
        x, y = STAGE.x + 22, STAGE.y + 88
        if self.picture:
            self.screen.blit(pygame.transform.smoothscale(self.picture, (300, 169)), (x, y))
            y += 190

        self.screen.blit(self.tiny.render("I think your hero is", True, DIM), (x, y))
        self.screen.blit(self.big.render(self.game.heroes[self.hero], True, TEXT), (x, y + 26))
        sure = f"{self.game.belief[self.hero]:.0%} sure, after {len(self.game.asked)} questions"
        self.screen.blit(self.tiny.render(sure, True, DIM), (x, y + 76))

        self.buttons = []
        for i, (label, correct) in enumerate([("Correct", True), ("Wrong", False)]):
            rect = pygame.Rect(x + i * 140, y + 110, 130, 46)
            self.button(rect, label, accent=correct)
            self.buttons.append((rect, ("confirm", correct)))

    def draw_over(self):
        x = STAGE.x + 22
        for i, line in enumerate(wrap(self.big, self.message, STAGE.width - 44)):
            self.screen.blit(self.big.render(line, True, TEXT), (x, STAGE.y + 150 + i * 46))

        rect = pygame.Rect(x, STAGE.y + 270, 180, 48)
        self.button(rect, "Play again", accent=True)
        self.buttons = [(rect, ("restart", None))]

    def draw_sidebar(self):
        panel(self.screen, SIDE)
        self.screen.blit(self.tiny.render("WHAT I BELIEVE RIGHT NOW", True, DIM),
                         (SIDE.x + 20, SIDE.y + 24))

        y = SIDE.y + 66
        for hero, p in self.game.top(8, skip_rejected=True):
            share = self.tiny.render(f"{p:.1%}", True, DIM)
            room = SIDE.width - 50 - share.get_width()
            self.screen.blit(self.small.render(ellipsize(self.small, hero, room), True, TEXT),
                             (SIDE.x + 20, y))
            self.screen.blit(share, (SIDE.right - 20 - share.get_width(), y + 4))

            track = pygame.Rect(SIDE.x + 20, y + 32, SIDE.width - 40, 4)
            pygame.draw.rect(self.screen, LINE, track)
            width = int(track.width * min(1.0, p))
            if width:
                pygame.draw.rect(self.screen, ACCENT, pygame.Rect(track.x, track.y, width, 4))
            y += 60

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.scrim, (0, 0))
        self.screen.blit(self.genie, self.genie.get_rect(midbottom=GENIE.midbottom))

        self.draw_header()
        panel(self.screen, STAGE)
        self.draw_meter()
        if self.state == "asking":
            self.draw_asking()
        elif self.state == "guessing":
            self.draw_guessing()
        else:
            self.draw_over()
        self.draw_sidebar()
        pygame.display.flip()

    def click(self, pos):
        for rect, (kind, value) in self.buttons:
            if not rect.collidepoint(pos):
                continue
            if kind == "answer":
                self.answer(value)
            elif kind == "confirm":
                self.confirm(value)
            else:
                self.start()
            return

    def key(self, key):
        if key == pygame.K_ESCAPE:
            return False
        if key == pygame.K_r:
            self.start()
        elif self.state == "asking" and key in KEYS:
            self.answer(KEYS[key])
        elif self.state == "guessing" and key in (pygame.K_y, pygame.K_n):
            self.confirm(key == pygame.K_y)
        return True

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    running = self.key(event.key)
            self.draw()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    Desktop().run()
