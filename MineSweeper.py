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
from typing import Dict, Tuple, List, Optional

# Константы
CELL_SIZE = 30
UI_PANEL_HEIGHT = 70
DIFFICULTY_BUTTON_HEIGHT = 50
FPS = 30

# Цвета
WHITE = (255, 255, 255)
GRAY = (192, 192, 192)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Состояния клеток
CELL_STATES = ['closed', 'opened', 'flagged', 'bombed', 'nobomb']

DIFFICULTIES = {
    'Легко': (9, 9, 10),
    'Средне': (16, 16, 40),
    'Сложно': (30, 16, 99)
}


class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.load_sounds()

    def load_sounds(self):
        base_path = os.path.dirname(__file__)
        sound_files = {
            'click': 'click.wav',
            'win': 'win.wav',
            'lose': 'lose.wav',
            'button': 'button.wav',
            'flag': 'flag.wav'
        }

        for name, filename in sound_files.items():
            try:
                path = os.path.join(base_path, 'res/sounds', filename)
                self.sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[ERROR] Failed to load sound {filename}: {e}")
                # Создаем заглушку
                self.sounds[name] = pygame.mixer.Sound(buffer=bytearray(100))

    def play(self, name: str):
        if name in self.sounds:
            self.sounds[name].play()


class ImageManager:
    def __init__(self):
        self.images = {}
        self.reset_imgs = {}
        self.load_images()

    def load_images(self):
        base_path = os.path.dirname(__file__)

        # Основные изображения клеток
        image_names = ['bomb', 'bombed', 'closed', 'flagged', 'noBomb', 'opened'] + [f'num{i}' for i in range(9)]

        for name in image_names:
            try:
                path = os.path.join(base_path, 'res/images', f"{name}.png")
                img = pygame.image.load(path).convert_alpha()
                self.images[name] = pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
            except Exception as e:
                print(f"[ERROR] Failed to load image {name}: {e}")
                # Создаем заглушку
                self.images[name] = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                self.images[name].fill((255, 0, 0, 128))

        # Изображения для кнопки reset
        for state_name in ['base', 'win', 'lose']:
            try:
                path = os.path.join(base_path, 'res/images', f"{state_name}.png")
                img = pygame.image.load(path).convert_alpha()
                self.reset_imgs[state_name] = img
            except Exception as e:
                print(f"[ERROR] Failed to load reset image {state_name}: {e}")
                self.reset_imgs[state_name] = pygame.Surface((40, 40), pygame.SRCALPHA)


class Board:
    def __init__(self, cols: int, rows: int, bombs_amount: int):
        self.cols = cols
        self.rows = rows
        self.bombs_amount = bombs_amount
        self.flags = 0
        self.visible_board = [[CELL_STATES.index('closed')] * cols for _ in range(rows)]
        self.hidden_board = [[0] * cols for _ in range(rows)]
        self.bombs = []

    def place_bombs(self, first_click_x: int, first_click_y: int):
        """Размещает бомбы на поле, исключая область вокруг первого клика"""
        possible_positions = [
            (x, y)
            for x in range(self.cols)
            for y in range(self.rows)
            if not (first_click_x - 1 <= x <= first_click_x + 1 and
                    first_click_y - 1 <= y <= first_click_y + 1)
        ]

        self.bombs = random.sample(possible_positions, self.bombs_amount)
        self._init_hidden_board()

    def _init_hidden_board(self):
        """Инициализирует скрытое поле с бомбами и числами"""
        for x, y in self.bombs:
            self.hidden_board[y][x] = -1

        for x in range(self.cols):
            for y in range(self.rows):
                if self.hidden_board[y][x] != -1:
                    self.hidden_board[y][x] = self._count_bombs_around(x, y)

    def _count_bombs_around(self, x: int, y: int) -> int:
        """Считает количество бомб вокруг клетки"""
        count = 0
        for i in range(max(0, x - 1), min(self.cols, x + 2)):
            for j in range(max(0, y - 1), min(self.rows, y + 2)):
                if self.hidden_board[j][i] == -1:
                    count += 1
        return count

    def in_range(self, x: int, y: int) -> bool:
        """Проверяет, находятся ли координаты в пределах поля"""
        return 0 <= x < self.cols and 0 <= y < self.rows


class Game:
    def __init__(self, cols: int, rows: int, bombs_amount: int, difficulty: str):
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

    def reveal(self, x: int, y: int):
        """Открывает клетку и обрабатывает результат"""
        if not self.board.in_range(x, y) or self.board.visible_board[y][x] != CELL_STATES.index('closed'):
            return

        if not self.first_click_done:
            self.board.place_bombs(x, y)
            self.first_click_done = True
            self.start_time = time.time()

        self.board.visible_board[y][x] = CELL_STATES.index('opened')
        self.closed_cells -= 1

        if self.board.hidden_board[y][x] == -1:
            self._handle_bomb_reveal()
            return

        sound_manager.play('click')

        if self.board.hidden_board[y][x] == 0:
            self._reveal_adjacent_cells(x, y)

        self._check_win_condition()

    def _handle_bomb_reveal(self):
        """Обрабатывает открытие бомбы"""
        sound_manager.play('lose')
        self.state = 'lose'
        self.elapsed_time = time.time() - self.start_time
        self._reveal_all_cells()
        self._save_result('lose')

    def _reveal_adjacent_cells(self, x: int, y: int):
        """Рекурсивно открывает соседние пустые клетки"""
        for i in range(max(0, x - 1), min(self.cols, x + 2)):
            for j in range(max(0, y - 1), min(self.rows, y + 2)):
                if self.board.visible_board[j][i] == CELL_STATES.index('closed'):
                    self.reveal(i, j)

    def _reveal_all_cells(self):
        """Открывает все клетки (при проигрыше или победе)"""
        for y in range(self.rows):
            for x in range(self.cols):
                if self.board.visible_board[y][x] == CELL_STATES.index('closed'):
                    state = 'bombed' if self.board.hidden_board[y][x] == -1 else 'opened'
                    self.board.visible_board[y][x] = CELL_STATES.index(state)

    def _check_win_condition(self):
        """Проверяет условия победы"""
        if self.closed_cells == self.board.bombs_amount and self.state == 'playing':
            self.state = 'win'
            self.elapsed_time = time.time() - self.start_time
            self._reveal_all_cells()
            sound_manager.play('win')
            self._save_result('win')

    def _save_result(self, result: str):
        """Сохраняет результат игры"""
        if not self.result_saved:
            save_game_result(self.difficulty, result, self.elapsed_time)
            self.result_saved = True

    def on_left_click(self, x: int, y: int):
        """Обрабатывает левый клик мыши"""
        if self.state != 'playing':
            return

        if self.board.visible_board[y][x] == CELL_STATES.index('opened'):
            self._chord_click(x, y)
        else:
            self.reveal(x, y)

    def _chord_click(self, x: int, y: int):
        """Обрабатывает клик по уже открытой клетке (аккорд)"""
        bombs_around = self.board.hidden_board[y][x]
        flags_around = sum(
            1 for i in range(max(0, x - 1), min(self.cols, x + 2))
            for j in range(max(0, y - 1), min(self.rows, y + 2))
            if self.board.visible_board[j][i] == CELL_STATES.index('flagged')
        )

        if flags_around == bombs_around:
            for i in range(max(0, x - 1), min(self.cols, x + 2)):
                for j in range(max(0, y - 1), min(self.rows, y + 2)):
                    if self.board.visible_board[j][i] == CELL_STATES.index('closed'):
                        self.reveal(i, j)

    def on_right_click(self, x: int, y: int):
        """Обрабатывает правый клик мыши (установка/снятие флага)"""
        if self.state != 'playing':
            return

        sound_manager.play('flag')
        state = self.board.visible_board[y][x]

        if state == CELL_STATES.index('closed') and self.flags < self.board.bombs_amount:
            self.board.visible_board[y][x] = CELL_STATES.index('flagged')
            self.flags += 1
        elif state == CELL_STATES.index('flagged'):
            self.board.visible_board[y][x] = CELL_STATES.index('closed')
            self.flags -= 1


def draw_board(screen: pygame.Surface, game: Game, images: Dict[str, pygame.Surface]):
    """Отрисовывает игровое поле"""
    for x in range(game.board.cols):
        for y in range(game.board.rows):
            cell = game.board.visible_board[y][x]
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            if cell == CELL_STATES.index('opened'):
                num = game.board.hidden_board[y][x]
                img_key = 'bomb' if num == -1 else f'num{num}'
            else:
                img_key = CELL_STATES[cell]

            screen.blit(images[img_key], rect)


def draw_ui(screen: pygame.Surface, font: pygame.font.Font, game: Game,
            reset_imgs: Dict[str, pygame.Surface]) -> pygame.Rect:
    """Отрисовывает интерфейс и возвращает rect кнопки reset"""
    panel_top = game.rows * CELL_SIZE + 5

    # Счётчик бомб
    bombs_text = font.render(f"Bomb: {game.board.bombs_amount - game.flags}", True, BLACK)
    screen.blit(bombs_text, (10, panel_top))

    # Кнопка reset
    reset_img = reset_imgs['win'] if game.state == 'win' else (
        reset_imgs['lose'] if game.state == 'lose' else reset_imgs['base']
    )
    reset_img = pygame.transform.smoothscale(reset_img, (40, 40))
    reset_rect = reset_img.get_rect(center=(screen.get_width() // 2, panel_top + 20))
    screen.blit(reset_img, reset_rect)

    # Таймер
    timer = game.elapsed_time if game.state in ('win', 'lose') else (
        time.time() - game.start_time if game.start_time else 0
    )
    timer_text = font.render(f"Time: {int(timer)}", True, BLACK)
    screen.blit(timer_text, (screen.get_width() - timer_text.get_width() - 10, panel_top))

    return reset_rect


def draw_message(screen: pygame.Surface, font: pygame.font.Font, text: str, win: bool = False):
    """Отрисовывает сообщение о победе/проигрыше с обводкой"""
    color = BLACK if win else RED
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

    # Обводка
    for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        outline = font.render(text, True, BLACK)
        screen.blit(outline, (text_rect.x + dx, text_rect.y + dy))

    screen.blit(text_surface, text_rect)


def difficulty_menu(screen: pygame.Surface, font: pygame.font.Font) -> Tuple[str, Tuple[int, int, int]]:
    """Отображает меню выбора сложности"""
    width, height = 600, 400
    screen = pygame.display.set_mode((width, height))
    button_width, button_height = 200, 60
    gap = 20

    buttons = []
    start_y = (height - (len(DIFFICULTIES) * (button_height + gap) - gap)) // 2

    for i, level in enumerate(DIFFICULTIES):
        rect = pygame.Rect(
            (width - button_width) // 2,
            start_y + i * (button_height + gap),
            button_width,
            button_height
        )
        buttons.append((level, rect))

    while True:
        screen.fill(WHITE)

        for level, rect in buttons:
            pygame.draw.rect(screen, BLUE, rect, border_radius=5)
            text = font.render(level, True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                for level, rect in buttons:
                    if rect.collidepoint(pos):
                        sound_manager.play('button')
                        return level, DIFFICULTIES[level]


def save_game_result(difficulty: str, result: str, duration: float):
    """Сохраняет результат игры в БД"""
    try:
        conn = sqlite3.connect("minesweeper_stats.db")
        cursor = conn.cursor()

        now = datetime.datetime.now().isoformat()
        cursor.execute('''
                       INSERT INTO game_stats (date, difficulty, result, duration)
                       VALUES (?, ?, ?, ?)
                       ''', (now, difficulty, result, duration))

        conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to save game result: {e}")
    finally:
        conn.close()


def show_statistics_window():
    """Показывает окно статистики в отдельном потоке"""

    def run_stats_window():
        try:
            root = tk.Tk()
            root.title("🏆 Статистика лучших результатов")
            root.geometry("500x500")

            conn = sqlite3.connect("minesweeper_stats.db")

            for i, (difficulty, title) in enumerate({
                                                        'Легко': 'Легкий',
                                                        'Средне': 'Средний',
                                                        'Сложно': 'Сложный'
                                                    }.items()):
                label = tk.Label(root, text=f"🏅 {title}", font=("Arial", 12, "bold"))
                label.pack(pady=(10 if i == 0 else 5, 0))

                df = pd.read_sql_query(f'''
                    SELECT date, duration FROM game_stats
                    WHERE result = "win" AND difficulty = ?
                    ORDER BY duration ASC
                    LIMIT 5
                ''', conn, params=(difficulty,))

                tree = ttk.Treeview(root, columns=("date", "duration"), show="headings", height=5)
                tree.heading("date", text="Дата")
                tree.heading("duration", text="Время (сек)")

                for _, row in df.iterrows():
                    tree.insert("", "end", values=(row["date"], round(row["duration"], 2)))

                tree.pack(pady=5)

            conn.close()
            root.mainloop()
        except Exception as e:
            print(f"[ERROR] Stats window error: {e}")

    import threading
    threading.Thread(target=run_stats_window, daemon=True).start()


def create_button(screen: pygame.Surface, font: pygame.font.Font, text: str, x: int, y: int, padding_x: int = 10,
                  padding_y: int = 5) -> pygame.Rect:
    """Создает кнопку и возвращает её rect"""
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect()

    button_rect = pygame.Rect(
        x,
        y,
        text_rect.width + 2 * padding_x,
        text_rect.height + 2 * padding_y
    )

    pygame.draw.rect(screen, BLUE, button_rect, border_radius=5)
    screen.blit(text_surf, (x + padding_x, y + padding_y))

    return button_rect


def main():
    """Основная функция игры"""
    pygame.init()

    temp_screen = pygame.display.set_mode((600, 400))
    font = pygame.font.SysFont(None, 30)

    # Инициализация менеджеров ресурсов
    global sound_manager, image_manager
    sound_manager = SoundManager()
    image_manager = ImageManager()

    # Теперь вызываем меню выбора сложности
    difficulty_str, (cols, rows, bombs) = difficulty_menu(temp_screen, font)

    # Шрифты
    font = pygame.font.SysFont(None, 30)
    big_font = pygame.font.SysFont(None, 50)

    # Выбор сложности
    difficulty_str, (cols, rows, bombs) = difficulty_menu(pygame.display.set_mode((400, 300)), font)

    # Настройка окна
    width = cols * CELL_SIZE
    height = rows * CELL_SIZE + UI_PANEL_HEIGHT + DIFFICULTY_BUTTON_HEIGHT + 50
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Сапёр')

    # Инициализация игры
    game = Game(cols, rows, bombs, difficulty_str)
    clock = pygame.time.Clock()

    running = True
    while running:
        screen.fill(GRAY)

        # Отрисовка
        draw_board(screen, game, image_manager.images)
        reset_rect = draw_ui(screen, font, game, image_manager.reset_imgs)

        # Кнопки интерфейса
        button_y = game.rows * CELL_SIZE + UI_PANEL_HEIGHT
        difficulty_rect = create_button(screen, font, "Сложность", 10, button_y)

        stats_text = "Stats"
        stats_rect = create_button(
            screen, font, stats_text,
            screen.get_width() - (font.size(stats_text)[0] + 20) - 10,
            button_y
        )

        solve_rect = create_button(
            screen, font, "Solve",
            stats_rect.x,
            stats_rect.y + stats_rect.height + 10
        )

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if event.button == 1:
                    if reset_rect.collidepoint(pos):
                        sound_manager.play('button')
                        game = Game(cols, rows, bombs, difficulty_str)
                    elif difficulty_rect.collidepoint(pos):
                        sound_manager.play('button')
                        difficulty_str, (cols, rows, bombs) = difficulty_menu(screen, font)
                        width = cols * CELL_SIZE
                        height = rows * CELL_SIZE + UI_PANEL_HEIGHT + DIFFICULTY_BUTTON_HEIGHT + 50
                        screen = pygame.display.set_mode((width, height))
                        game = Game(cols, rows, bombs, difficulty_str)
                    elif stats_rect.collidepoint(pos):
                        sound_manager.play('button')
                        show_statistics_window()
                    elif solve_rect.collidepoint(pos):
                        sound_manager.play('button')
                        solver = MinesweeperSolver(game.board.visible_board, game.board.hidden_board)
                        for action, x, y in solver.solve_step():
                            if action == 'open':
                                game.on_left_click(x, y)
                            elif action == 'flag':
                                game.on_right_click(x, y)
                    elif pos[1] < game.rows * CELL_SIZE:
                        game.on_left_click(pos[0] // CELL_SIZE, pos[1] // CELL_SIZE)

                elif event.button == 3 and pos[1] < game.rows * CELL_SIZE:
                    game.on_right_click(pos[0] // CELL_SIZE, pos[1] // CELL_SIZE)

        # Сообщение о результате игры
        if game.state == 'win':
            draw_message(screen, big_font, "ПОБЕДА!", True)
        elif game.state == 'lose':
            draw_message(screen, big_font, "ПРОИГРЫШ!", False)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    sound_manager = None
    image_manager = None
    main()