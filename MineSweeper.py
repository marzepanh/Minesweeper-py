import sys

import pygame
import random
import time
import os
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk
import pandas as pd
from solver import MinesweeperSolver

# Инициализация микшера
pygame.mixer.init()

# Путь к папке со звуками
base_path = os.path.dirname(__file__)
sound_path = lambda name: os.path.join(base_path, 'res/sounds', name)

# Загрузка звуков
click_sound = pygame.mixer.Sound(sound_path('click.wav'))
win_sound = pygame.mixer.Sound(sound_path('win.wav'))
boom_sound = pygame.mixer.Sound(sound_path('lose.wav'))
button_sound = pygame.mixer.Sound(sound_path('button.wav'))
flag_sound = pygame.mixer.Sound(sound_path('flag.wav'))

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
    def __init__(self, cols, rows, bombs_amount, difficulty):
        self.board = Board(cols, rows, bombs_amount)
        self.cols = cols
        self.rows = rows
        self.flags = 0
        self.closed_cells = cols * rows
        self.state = 'playing'
        self.start_time = None
        self.elapsed_time = 0
        self.first_click_done = False
        self.result_saved = False
        self.difficulty = difficulty

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
            boom_sound.play()
            self.state = 'lose'
            self.elapsed_time = time.time() - self.start_time  # фиксируем время при проигрыше
            self.reveal_all_cells()
            if not self.result_saved:
                save_game_result(self.difficulty, 'lose', self.elapsed_time)
                print(f"[LOG] Saved result: {self.difficulty}, {self.state}, {self.elapsed_time}")
                self.result_saved = True
            return

        click_sound.play()  # 🔈 Воспроизведение звука открытия

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
        flag_sound.play()
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
            win_sound.play()  # 🔈 Звук победы
            if not self.result_saved:
                save_game_result(self.difficulty, 'win', self.elapsed_time)
                print(f"[LOG] Saved result: {self.difficulty}, {self.state}, {self.elapsed_time}")
                self.result_saved = True


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


def draw_ui(screen, font, flags, bombs, timer, width, height, reset_imgs, game_state, rows):
    panel_top = rows * CELL_SIZE + 5  # UI прямо под игровым полем

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
    #screen = pygame.display.set_mode((width, height))
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
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for level, rect in buttons:
                    if rect.collidepoint(mx, my):
                        button_sound.play()
                        selected = level
                        menu_running = False
    return selected, DIFFICULTIES[selected]


def save_game_result(difficulty, result, duration):
    conn = sqlite3.connect("minesweeper_stats.db")
    cursor = conn.cursor()

    now = datetime.datetime.now().isoformat()
    cursor.execute('''
                   INSERT INTO game_stats (date, difficulty, result, duration)
                   VALUES (?, ?, ?, ?)
                   ''', (now, difficulty, result, duration))

    conn.commit()
    conn.close()

import threading

def show_statistics_window():
    def run_stats_window():
        stats_window = tk.Tk()  # Было Toplevel(), но Toplevel требует уже активного Tk
        stats_window.title("🏆 Статистика лучших результатов")
        stats_window.geometry("500x500")

        conn = sqlite3.connect("minesweeper_stats.db")

        difficulties = ['Легко', 'Средне', 'Сложно']
        titles = {'Легко': 'Легкий', 'Средне': 'Средний', 'Сложно': 'Сложный'}

        for i, difficulty in enumerate(difficulties):
            label = tk.Label(stats_window, text=f"🏅 {titles[difficulty]}", font=("Arial", 12, "bold"))
            label.pack(pady=(10 if i == 0 else 5, 0))

            df = pd.read_sql_query(f'''
                SELECT date, duration FROM game_stats
                WHERE result = "win" AND difficulty = ?
                ORDER BY duration ASC
                LIMIT 5
            ''', conn, params=(difficulty,))



            tree = ttk.Treeview(stats_window, columns=("date", "duration"), show="headings", height=5)
            tree.heading("date", text="Дата")
            tree.heading("duration", text="Время (сек)")

            if df.empty:
                print(f"Нет данных для сложности {difficulty}")
            else:
                for _, row in df.iterrows():
                    tree.insert("", "end", values=(row["date"], round(row["duration"], 2)))

            tree.pack(pady=5)

        conn.close()
        stats_window.mainloop()  # ОБЯЗАТЕЛЬНО!


    # Запускаем окно статистики в отдельном потоке, чтобы не блокировать pygame
    threading.Thread(target=run_stats_window, daemon=True).start()




def main():
    pygame.init()
    font = pygame.font.SysFont(None, 30)
    big_font = pygame.font.SysFont(None, 50)

    # Начальный выбор сложности
    screen = pygame.display.set_mode((400, 300))
    difficulty_str, (cols, rows, bombs) = difficulty_menu(screen, font)

    width = cols * CELL_SIZE
    difficulty_button_height = 50
    height = rows * CELL_SIZE + UI_PANEL_HEIGHT + difficulty_button_height + 50
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

    game = Game(cols, rows, bombs, difficulty_str)
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
        reset_rect = draw_ui(screen, font, game.flags, bombs, timer, width, height, reset_imgs, game.state, game.rows)

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

        # Кнопка "Статистика"
        stats_text = "Stats"
        stats_surf = font.render(stats_text, True, WHITE)
        stats_rect = stats_surf.get_rect()

        # Позиционируем кнопку от правого края
        button_padding_x = 10  # тот же padding
        button_padding_y = 5
        stats_button_width = stats_rect.width + 2 * button_padding_x
        stats_button_height = stats_rect.height + 2 * button_padding_y
        stats_button_x = screen.get_width() - stats_button_width - 10  # 10 px отступ от правого края
        stats_button_y = difficulty_button_y  # на том же уровне

        stats_rect.topleft = (stats_button_x + button_padding_x, stats_button_y + button_padding_y)
        stats_button_rect = pygame.Rect(stats_button_x,
                                        stats_button_y,
                                        stats_button_width,
                                        stats_button_height)
        pygame.draw.rect(screen, BLUE, stats_button_rect, border_radius=5)
        screen.blit(stats_surf, stats_rect)

        # ---- Добавляем кнопку "Решить" ----

        solve_text = "Solve"
        solve_surf = font.render(solve_text, True, WHITE)
        solve_rect = solve_surf.get_rect()

        solve_button_width = solve_rect.width + 2 * button_padding_x
        solve_button_height = solve_rect.height + 2 * button_padding_y

        # Располагаем под кнопкой "Статистика" с отступом 10 пикселей по вертикали
        solve_button_x = stats_button_x
        solve_button_y = stats_button_y + stats_button_height + 10

        solve_rect.topleft = (solve_button_x + button_padding_x, solve_button_y + button_padding_y)
        solve_button_rect = pygame.Rect(solve_button_x, solve_button_y, solve_button_width, solve_button_height)

        pygame.draw.rect(screen, BLUE, solve_button_rect, border_radius=5)
        screen.blit(solve_surf, solve_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                mx, my = event.pos

                if reset_rect.collidepoint(mx, my):
                    button_sound.play()
                    game = Game(cols, rows, bombs, difficulty_str)
                    continue

                if stats_rect.collidepoint(mx, my):
                    button_sound.play()
                    show_statistics_window()
                    continue

                if solve_rect.collidepoint(mx, my):
                    button_sound.play()
                    solver = MinesweeperSolver(game.board.visible_board, game.board.hidden_board)
                    actions = solver.solve_step()

                    for action, x, y in actions:

                        if action == 'open':
                            game.on_left_click(x, y)
                        elif action == 'flag':
                            game.on_right_click(x, y)
                    continue

                if button_rect.collidepoint(mx, my):
                    button_sound.play()  # 🔈 Воспроизведение звука при нажатии на "Сложность"
                    # Открываем меню выбора сложности и обновляем игру и окно
                    difficulty_str, (cols, rows, bombs) = difficulty_menu(screen, font)
                    width = cols * CELL_SIZE
                    height = rows * CELL_SIZE + UI_PANEL_HEIGHT + difficulty_button_height + 50
                    screen = pygame.display.set_mode((width, height))
                    game = Game(cols, rows, bombs, difficulty_str)
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