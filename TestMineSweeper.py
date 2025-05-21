import time
import unittest
import pygame
from unittest.mock import patch, MagicMock
import threading
import traceback
from solver import MinesweeperSolver

from MineSweeper import (
    draw_board,
    draw_ui,
    draw_message,
    difficulty_menu,
    show_statistics_window,
    main,
    Game,
    Board,
    CELL_STATES
)

class TestMinesweeperLogic(unittest.TestCase):

    def setUp(self):
        self.cols = 5
        self.rows = 5
        self.bombs = 3
        self.game = Game(self.cols, self.rows, self.bombs, 'Легко')
        self.mock_sound = MagicMock()
        pygame.init()


    def test_board_initialization(self):
        board = Board(4, 4, 2)
        self.assertEqual(board.cols, 4)
        self.assertEqual(board.rows, 4)
        self.assertEqual(board.bombs_amount, 2)
        self.assertEqual(len(board.bombs), 0)

    def test_place_bombs_excludes_first_click(self):
        board = Board(5, 5, 3)
        first_x, first_y = 2, 2
        board.place_bombs(first_x, first_y)
        for bx, by in board.bombs:
            self.assertFalse(abs(bx - first_x) <= 1 and abs(by - first_y) <= 1)

    def test_count_bombs_around(self):
        board = Board(3, 3, 0)
        board.bombs = [(0, 0), (1, 1)]
        count = board.count_bombs_around(1, 0)
        self.assertEqual(count, 2)

    def test_reveal_empty_cell_triggers_recursive_opening(self):
        game = Game(3, 3, 0, 'Легко')
        game.board.bombs = []
        game.board.init_hidden_board()

        for y in range(3):
            for x in range(3):
                if (x, y) != (1, 1):
                    game.board.hidden_board[y][x] = 0

        game.board.visible_board[1][1] = CELL_STATES.index('closed')

        game.reveal(2, 2)

        for y in range(3):
            for x in range(3):
                if (x, y) != (1, 1):
                    self.assertEqual(game.board.visible_board[y][x], CELL_STATES.index('opened'))

    def test_win_condition(self):
        game = Game(2, 2, 1, 'Легко')

        game.board.bombs = [(0, 0)]
        game.board.init_hidden_board()

        for y in range(2):
            for x in range(2):
                if (x, y) != (0, 0):
                    game.reveal(x, y)

        self.assertEqual(game.state, 'win')

    def test_lose_condition_on_bomb(self):
        game = Game(2, 2, 1, 'Легко')

        game.board.bombs = [(0, 0)]
        game.board.init_hidden_board()

        game.reveal(0, 0)

        self.assertEqual(game.state, 'lose')

    def test_reveal_already_opened_cell_does_nothing(self):
        game = Game(3, 3, 1, 'Легко')

        game.board.bombs = [(1, 1)]
        game.board.init_hidden_board()

        game.reveal(0, 0)

        initial_visible_state = game.board.visible_board[0][0]

        game.reveal(0, 0)
        self.assertEqual(game.board.visible_board[0][0], initial_visible_state)


    def test_flagging_and_unflagging_cell(self):
        game = Game(3, 3, 1, 'Легко')
        x, y = 1, 1

        # Установка флага на закрытую ячейку
        game.on_right_click(x, y)
        self.assertEqual(game.board.visible_board[y][x], CELL_STATES.index('flagged'))
        self.assertEqual(game.flags, 1)

        # Удаление флага с той же ячейки
        game.on_right_click(x, y)
        self.assertEqual(game.board.visible_board[y][x], CELL_STATES.index('closed'))
        self.assertEqual(game.flags, 0)


    def test_reveal_all_bombs_marks_bombed_cells(self):
        game = Game(3, 3, 2, 'Легко')
        # Расставляем бомбы вручную для предсказуемости теста
        game.board.bombs = [(0, 0), (2, 2)]
        game.board.init_hidden_board()

        # Обозначаем все клетки как закрытые перед вызовом reveal_all_bombs()
        for y in range(3):
            for x in range(3):
                if game.board.visible_board[y][x] != CELL_STATES.index('bombed'):
                    if (x, y) in game.board.bombs:
                        continue
                    else:
                        game.board.visible_board[y][x] = CELL_STATES.index('closed')

        game.reveal_all_bombs()

        for bx, by in [(0, 0), (2, 2)]:
            self.assertEqual(game.board.visible_board[by][bx], CELL_STATES.index('bombed'))


    def test_check_win_triggers_when_all_non_bomb_cells_opened(self):
        game = Game(2, 2, 1, 'Легко')
        # Расставляем бомбу в одной из клеток и подготовим доску
        game.board.bombs = [(0, 0)]
        game.board.init_hidden_board()

        # Открываем все кроме бомбы
        for y in range(2):
            for x in range(2):
                if (x, y) != (0, 0):
                    game.reveal(x, y)

        # После открытия всех безопасных клеток игра должна закончиться победой
        self.assertEqual(game.state, 'win')

    def tearDown(self):
        pygame.quit()

    @patch('pygame.Surface')
    @patch('pygame.Rect')
    @patch('pygame.sprite.Sprite')
    def test_draw_board(self, mock_sprite, mock_rect, mock_surface):
        # Создаем моковые изображения
        images = {
            'closed': MagicMock(),
            'flagged': MagicMock(),
            'bombed': MagicMock(),
            'noBomb': MagicMock(),
            'bomb': MagicMock(),
            'num0': MagicMock()
        }
        # Создаем моковый экран
        screen = MagicMock()
        # Создаем игру с простым состоянием доски
        game = Game(3, 3, 0, 'Легко')
        game.board.visible_board = [
            [CELL_STATES.index('closed')] * 3 for _ in range(3)
        ]
        game.board.hidden_board = [
            [0] * 3 for _ in range(3)
        ]
        # Вызов функции
        draw_board(screen, game, images)
        # Проверяем что blit вызвано нужное количество раз
        self.assertTrue(screen.blit.called)

    def test_draw_ui_win_and_lose(self):
        screen = MagicMock()
        font = MagicMock()

        # Создаем реальные поверхности для изображений
        mock_base_img = pygame.Surface((50, 50))
        mock_win_img = pygame.Surface((50, 50))
        mock_lose_img = pygame.Surface((50, 50))

        reset_imgs = {
            'base': mock_base_img,
            'win': mock_win_img,
            'lose': mock_lose_img
        }
        width = 300
        height = 400

        # Тест при статусе win
        reset_rect_win = draw_ui(screen, font, 1, 10, 5.0, width, height, reset_imgs, 'win', 5)
        self.assertIsNotNone(reset_rect_win)

        # Тест при статусе lose
        reset_rect_lose = draw_ui(screen, font, 1, 10, 5.0, width, height, reset_imgs, 'lose', 5)
        self.assertIsNotNone(reset_rect_lose)

    def test_draw_message_win_and_loss(self):
        screen = MagicMock()
        font = MagicMock()

        # Тест победы (win=True)
        draw_message(screen, font, "Victory", 400, 300, win=True)

        # Тест проигрыша (win=False)
        draw_message(screen, font, "Game Over", 400, 300, win=False)

        self.assertTrue(screen.blit.called)


    def test_difficulty_menu_selection(self):
        width, height = 600, 400
        screen = pygame.display.set_mode((width, height))

        font = MagicMock()
        font.render.return_value = pygame.Surface((100, 30))

        selected_level = difficulty_menu(screen, font)

        print(f"Выбран уровень сложности: {selected_level}")


    @patch('threading.Thread')
    @patch('tkinter.Tk')
    def test_show_statistics_window_starts_thread(self, mock_tk, mock_thread):
        show_statistics_window()
        self.assertTrue(mock_thread.called)

    @patch('pygame.display.set_mode')
    @patch('pygame.font.SysFont')
    @patch('pygame.image.load')
    @patch('pygame.mixer.Sound')
    def test_main_flow_initialization(self, mock_sound, mock_image_load, mock_sysfont, mock_set_mode):
        mock_display_surface = pygame.Surface((600, 400))
        mock_reset_img = pygame.Surface((50, 50))
        mock_button_img = pygame.Surface((100, 50))
        mock_background = pygame.Surface((600, 400))
        mock_logo = pygame.Surface((200, 100))
        mock_title = pygame.Surface((300, 50))
        mock_game_over_img = pygame.Surface((200, 50))
        mock_win_img = pygame.Surface((200, 50))

        mock_set_mode.return_value = mock_display_surface

        with patch('pygame.display.flip') as mock_flip:
            mock_flip.side_effect = lambda: None

            def load_side_effect(path):
                if 'reset' in path:
                    return mock_reset_img
                elif 'button' in path:
                    return mock_button_img
                elif 'background' in path:
                    return mock_background
                elif 'logo' in path:
                    return mock_logo
                elif 'title' in path:
                    return mock_title
                elif 'game_over' in path:
                    return mock_game_over_img
                elif 'win' in path:
                    return mock_win_img
                else:
                    return MagicMock()

            mock_image_load.side_effect = load_side_effect

            with patch('pygame.draw.rect') as mock_draw_rect, \
                    patch('pygame.transform.smoothscale') as mock_smoothscale:

                mock_draw_rect.side_effect = lambda surf, color, rect: None

                def dummy_smoothscale(image, size):
                    return image

                mock_smoothscale.side_effect = dummy_smoothscale

                def run_main():
                    try:
                        main()
                    except Exception:
                        traceback.print_exc()

                mock_font = MagicMock()
                mock_font.render.return_value = pygame.Surface((100, 30))
                mock_sysfont.return_value = mock_font
                thread = threading.Thread(target=run_main)
                thread.start()

                time.sleep(2)

                self.assertTrue(thread.is_alive(), "Поток завершился раньше времени")

    @patch('pygame.display.set_mode')
    @patch('pygame.font.SysFont')
    @patch('pygame.image.load')
    @patch('pygame.mixer.Sound')
    def test_game_flow(self, mock_mixer_init, mock_sound_load, mock_font_sysfont, mock_set_mode):
        # Мокаем все необходимые компоненты
        mock_mixer_init.return_value = None
        mock_sound = MagicMock()
        mock_sound_load.return_value = mock_sound
        mock_font = MagicMock()
        mock_font_sysfont.return_value = mock_font

        mock_screen = MagicMock()
        mock_set_mode.return_value = mock_screen

        def run():
            try:
                main()
            except SystemExit:
                pass  # pygame.quit вызывает sys.exit()

        thread = threading.Thread(target=run)
        thread.start()

        time.sleep(1)

        pygame.event.post(pygame.event.Event(pygame.QUIT))

        thread.join(timeout=2)
        self.assertFalse(thread.is_alive(), "Игра не завершилась корректно")

    @patch('pygame.display.set_mode')
    @patch('pygame.font.SysFont')
    @patch('pygame.image.load')
    @patch('pygame.mixer.Sound')
    def test_click_on_board(self, mock_mixer_init, mock_sound_load, mock_font_sysfont, mock_set_mode):
        mock_mixer_init.return_value = None
        mock_sound = MagicMock()
        mock_sound_load.return_value = mock_sound
        mock_font = MagicMock()
        mock_font_sysfont.return_value = mock_font

        mock_screen = MagicMock()
        mock_set_mode.return_value = mock_screen

        def run():
            try:
                main()
            except SystemExit:
                pass

        thread = threading.Thread(target=run)
        thread.start()

        time.sleep(1)

        event_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (15, 15), 'button': 1})
        pygame.event.post(event_down)

        time.sleep(0.5)

        # Имитируем закрытие окна
        pygame.event.post(pygame.event.Event(pygame.QUIT))

        thread.join(timeout=2)

    @patch('pygame.display.set_mode')
    @patch('pygame.font.SysFont')
    @patch('pygame.image.load')
    @patch('pygame.mixer.Sound')
    def test_right_click_flagging(self, mock_mixer_init, mock_sound_load, mock_font_sysfont, mock_set_mode):
        mock_mixer_init.return_value = None
        mock_sound = MagicMock()
        mock_sound_load.return_value = mock_sound

        def sound_play():
            pass

        mock_sound.play.side_effect = sound_play

        mock_screen = MagicMock()
        mock_set_mode.return_value = mock_screen

        def run():
            try:
                main()
            except SystemExit:
                pass

        thread = threading.Thread(target=run)

        thread.start()

        time.sleep(1)


        event_right_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (50, 50), 'button': 3})

        pygame.event.post(event_right_click)

        time.sleep(0.5)

        pygame.event.post(pygame.event.Event(pygame.QUIT))
        thread.join(timeout=2)


    #Test solver
    def test_no_opened_cells(self):
        visible = [
            [0, 0],
            [0, 0]
        ]
        hidden = [
            [0, 1],
            [1, 2]
        ]
        solver = MinesweeperSolver(visible, hidden)
        actions = solver.solve_step()
        self.assertEqual(actions, [], "Должен вернуть пустой список, если нет открытых ячеек.")



    def test_subset_neighbors_leads_to_mine(self):
        # Тест на ситуацию с подмножествами соседних клеток для мин
        visible = [
            [CELL_STATES.index('opened'), 0],
            [CELL_STATES.index('opened'), 0]
        ]

        hidden = [
            [2, 1],
            [2, 1]
        ]

        solver = MinesweeperSolver(visible, hidden)
        actions = solver.solve_step()

        flags = [act for act in actions if act[0] == 'flag']

        self.assertTrue(any((x == 1 and y == 1) for _, x, y in flags) or
                        any((x == 0 and y == 1) for _, x, y in flags),
                        "Должен быть флаг на одной из предполагаемых мин.")

if __name__ == '__main__':
    unittest.main()