import pygame
import random
import time

# Состояния клеток
CELL_STATES = ['closed', 'opened', 'flagged', 'bombed', 'nobomb']

DIFFICULTIES = {
    'Легко': (9, 9, 10),
    'Средне': (16, 16, 40),
    'Сложно': (30, 16, 99)
}

CELL_SIZE = 30
UI_PANEL_HEIGHT = 70
FONT_COLOR = (0, 0, 0)

WHITE = (255, 255, 255)
GRAY = (192, 192, 192)
RED = (255, 0, 0)
GREEN = (0, 180, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)


class Board:
    def __init__(self, cols, rows, bombs_amount):
        self.cols = cols
        self.rows = rows
        self.bombs_amount = bombs_amount
        self.flags = 0
        self.visible_board = [[CELL_STATES.index('closed')] * cols for _ in range(rows)]
        self.hidden_board = [[0] * cols for _ in range(rows)]
        self.bombs = []
        self.init_bombs()

    def init_bombs(self):
        self.bombs = []

    def place_bombs(self, first_click_x, first_click_y):
        possible_positions = [(x, y) for x in range(self.cols) for y in range(self.rows)]

        exclude = set()
        for i in range(first_click_x - 1, first_click_x + 2):
            for j in range(first_click_y - 1, first_click_y + 2):
                if 0 <= i < self.cols and 0 <= j < self.rows:
                    exclude.add((i, j))
        possible_positions = [pos for pos in possible_positions if pos not in exclude]

        self.bombs = random.sample(possible_positions, self.bombs_amount)
        self.init_hidden_board()

    def init_hidden_board(self):
        for x in range(self.cols):
            for y in range(self.rows):
                if (x, y) in self.bombs:
                    self.hidden_board[y][x] = -1
                else:
                    self.hidden_board[y][x] = self.count_bombs_around(x, y)

    def count_bombs_around(self, x, y):
        count = 0
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if 0 <= i < self.cols and 0 <= j < self.rows:
                    if (i, j) in self.bombs:
                        count += 1
        return count

    def in_range(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows


class Game:
    def __init__(self, cols, rows, bombs_amount):
        self.board = Board(cols, rows, bombs_amount)
        self.cols = cols
        self.rows = rows
        self.flags = 0
        self.closed_cells = cols * rows
        self.state = 'playing'
        self.start_time = None
        self.elapsed_time = 0
        self.first_click_done = False

    def reveal(self, x, y):
        if not self.board.in_range(x, y):
            return
        if self.board.visible_board[y][x] != CELL_STATES.index('closed'):
            return
        if self.start_time is None:
            self.start_time = time.time()

        self.board.visible_board[y][x] = CELL_STATES.index('opened')
        self.closed_cells -= 1

        if self.board.hidden_board[y][x] == -1:
            self.state = 'lose'
            self.elapsed_time = time.time() - self.start_time  # фиксируем время при проигрыше
            self.reveal_all_cells()
            return

        if self.board.hidden_board[y][x] == 0:
            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if self.board.in_range(i, j) and self.board.visible_board[j][i] == CELL_STATES.index('closed'):
                        self.reveal(i, j)

        self.check_win()

    def reveal_all_bombs(self):
        for (x, y) in self.board.bombs:
            if self.board.visible_board[y][x] != CELL_STATES.index('flagged'):
                self.board.visible_board[y][x] = CELL_STATES.index('bombed')

    def reveal_all_cells(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if self.board.visible_board[y][x] == CELL_STATES.index('closed'):
                    if self.board.hidden_board[y][x] == -1:
                        self.board.visible_board[y][x] = CELL_STATES.index('bombed')
                    else:
                        self.board.visible_board[y][x] = CELL_STATES.index('opened')

    def on_left_click(self, x, y):
        if self.state != 'playing':
            return

        if not self.first_click_done:
            self.board.place_bombs(x, y)
            self.first_click_done = True

        if self.board.visible_board[y][x] == CELL_STATES.index('opened'):
            bombs_around = self.board.hidden_board[y][x]
            flags_around = 0
            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if self.board.in_range(i, j):
                        if self.board.visible_board[j][i] == CELL_STATES.index('flagged'):
                            flags_around += 1
            if flags_around == bombs_around:
                for i in range(x - 1, x + 2):
                    for j in range(y - 1, y + 2):
                        if self.board.in_range(i, j):
                            if self.board.visible_board[j][i] == CELL_STATES.index('closed'):
                                self.reveal(i, j)
        elif self.board.visible_board[y][x] == CELL_STATES.index('closed'):
            self.reveal(x, y)

    def on_right_click(self, x, y):
        if self.state != 'playing':
            return
        state = self.board.visible_board[y][x]
        if state == CELL_STATES.index('closed'):
            if self.flags < self.board.bombs_amount:
                self.board.visible_board[y][x] = CELL_STATES.index('flagged')
                self.flags += 1
        elif state == CELL_STATES.index('flagged'):
            self.board.visible_board[y][x] = CELL_STATES.index('closed')
            self.flags -= 1

    def check_win(self):
        if self.closed_cells == self.board.bombs_amount and self.state == 'playing':
            self.state = 'win'
            self.elapsed_time = time.time() - self.start_time
            self.reveal_all_cells()


def draw_board(screen, game, images):
    for x in range(game.board.cols):
        for y in range(game.board.rows):
            cell = game.board.visible_board[y][x]
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            if cell == CELL_STATES.index('closed'):
                screen.blit(images['closed'], rect)
            elif cell == CELL_STATES.index('flagged'):
                screen.blit(images['flagged'], rect)
            elif cell == CELL_STATES.index('bombed'):
                screen.blit(images['bombed'], rect)
            elif cell == CELL_STATES.index('nobomb'):
                screen.blit(images['noBomb'], rect)
            elif cell == CELL_STATES.index('opened'):
                num = game.board.hidden_board[y][x]
                if num == -1:
                    screen.blit(images['bomb'], rect)
                else:
                    screen.blit(images[f'num{num}'], rect)


def draw_ui(screen, font, flags, bombs, timer, width, height, reset_imgs, game_state):
    panel_top = height - UI_PANEL_HEIGHT - 50 + 5  # 50 — высота блока с кнопкой "Сложность"
    panel_left = 10
    panel_right = width - 10

    # Счётчик бомб слева
    bombs_text = font.render(f"Bomb: {bombs - flags}", True, BLACK)
    screen.blit(bombs_text, (panel_left, panel_top))

    # Кнопка reset по центру
    reset_img = reset_imgs['base']
    if game_state == 'win':
        reset_img = reset_imgs['win']
    elif game_state == 'lose':
        reset_img = reset_imgs['lose']

    reset_img = pygame.transform.smoothscale(reset_img, (40, 40))
    reset_rect = reset_img.get_rect(center=(width // 2, panel_top + 20))
    screen.blit(reset_img, reset_rect)

    # Таймер справа
    timer_text = font.render(f"Time: {int(timer)}", True, BLACK)
    timer_rect = timer_text.get_rect()
    screen.blit(timer_text, (panel_right - timer_rect.width, panel_top))

    return reset_rect


def draw_message(screen, font, text, width, height, win=False):
    color = BLACK if win else RED
    outline_color = BLACK
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(width // 2, height // 2))

    # Рисуем обводку - текст смещаем на 1 пиксель в 8 направлениях чёрным
    for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                   (0, -1), (0, 1),
                   (1, -1), (1, 0), (1, 1)]:
        outline_surface = font.render(text, True, outline_color)
        outline_rect = outline_surface.get_rect(center=(width // 2 + dx, height // 2 + dy))
        screen.blit(outline_surface, outline_rect)

    # Рисуем основной текст поверх обводки
    screen.blit(text_surface, text_rect)


def difficulty_menu(screen, font):
    menu_running = True
    selected = None
    width, height = 600, 400
    screen = pygame.display.set_mode((width, height))
    button_width = 200
    button_height = 60
    gap = 20
    total_height = len(DIFFICULTIES) * (button_height + gap) - gap
    start_y = (height - total_height) // 2

    buttons = []
    for i, level in enumerate(DIFFICULTIES.keys()):
        rect = pygame.Rect((width - button_width) // 2, start_y + i * (button_height + gap), button_width,
                           button_height)
        buttons.append((level, rect))
    while menu_running:
        screen.fill(WHITE)
        for level, rect in buttons:
            pygame.draw.rect(screen, BLUE, rect)
            text = font.render(level, True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for level, rect in buttons:
                    if rect.collidepoint(mx, my):
                        selected = level
                        menu_running = False
    return DIFFICULTIES[selected]


# ... твой код без изменений до main() ...

def main():
    pygame.init()
    font = pygame.font.SysFont(None, 30)
    big_font = pygame.font.SysFont(None, 50)

    # Начальный выбор сложности
    screen = pygame.display.set_mode((400, 300))
    cols, rows, bombs = difficulty_menu(screen, font)

    width = cols * CELL_SIZE
    DIFFICULTY_BUTTON_HEIGHT = 50
    height = rows * CELL_SIZE + UI_PANEL_HEIGHT + DIFFICULTY_BUTTON_HEIGHT
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Сапёр')

    # Загрузка основных иконок клеток
    image_names = ['bomb', 'bombed', 'closed', 'flagged', 'noBomb', 'opened'] + [f'num{i}' for i in range(9)]

    images = {}
    for name in image_names:
        path = f'res/images/{name}.png'
        try:
            images[name] = pygame.image.load(path).convert_alpha()
            images[name] = pygame.transform.scale(images[name], (CELL_SIZE, CELL_SIZE))
        except Exception as e:
            print(f"[ERROR] Failed to load {path}: {e}")

    # Загрузка изображений кнопки reset
    reset_imgs = {}
    for state_name in ['base', 'win', 'lose']:
        path = f'res/images/{state_name}.png'
        try:
            reset_imgs[state_name] = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"[ERROR] Failed to load reset image {path}: {e}")
            reset_imgs[state_name] = pygame.Surface((40, 40))  # Заглушка

    game = Game(cols, rows, bombs)
    clock = pygame.time.Clock()

    running = True
    while running:
        screen.fill(GRAY)

        timer = 0
        if game.start_time is not None and game.state == 'playing':
            timer = time.time() - game.start_time
        elif game.state in ('win', 'lose'):
            timer = game.elapsed_time

        # Отрисовка игрового поля
        draw_board(screen, game, images)

        # Отрисовка UI (счётчик бомб, кнопка reset, таймер)
        reset_rect = draw_ui(screen, font, game.flags, bombs, timer, width, height, reset_imgs, game.state)

        # Кнопка "Сложность"
        difficulty_button_x = 10
        difficulty_button_y = rows * CELL_SIZE + UI_PANEL_HEIGHT  # сразу под UI-панелью

        button_text = "Сложность"
        button_padding_x = 10
        button_padding_y = 5
        btn_surf = font.render(button_text, True, WHITE)
        btn_rect = btn_surf.get_rect()
        btn_rect.topleft = (difficulty_button_x + button_padding_x, difficulty_button_y + button_padding_y)
        button_rect = pygame.Rect(difficulty_button_x,
                                  difficulty_button_y,
                                  btn_rect.width + 2 * button_padding_x,
                                  btn_rect.height + 2 * button_padding_y)
        pygame.draw.rect(screen, BLUE, button_rect, border_radius=5)
        screen.blit(btn_surf, btn_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                mx, my = event.pos

                if reset_rect.collidepoint(mx, my):
                    game = Game(cols, rows, bombs)
                    continue

                if button_rect.collidepoint(mx, my):
                    # Открываем меню выбора сложности и обновляем игру и окно
                    cols, rows, bombs = difficulty_menu(screen, font)
                    width = cols * CELL_SIZE
                    height = rows * CELL_SIZE + UI_PANEL_HEIGHT + DIFFICULTY_BUTTON_HEIGHT
                    screen = pygame.display.set_mode((width, height))
                    game = Game(cols, rows, bombs)
                    continue

                if my < rows * CELL_SIZE:
                    cell_x = mx // CELL_SIZE
                    cell_y = my // CELL_SIZE
                    if event.button == 1:
                        game.on_left_click(cell_x, cell_y)
                    elif event.button == 3:
                        game.on_right_click(cell_x, cell_y)

        # Если игра окончена - выводим сообщение
        if game.state == 'win':
            draw_message(screen, big_font, "ПОБЕДА!", width, height, win=True)
        elif game.state == 'lose':
            draw_message(screen, big_font, "ПРОИГРЫШ!", width, height, win=False)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
