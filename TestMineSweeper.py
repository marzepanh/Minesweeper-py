import unittest
from unittest.mock import patch, MagicMock
import random

# Импортируйте ваши классы и функции из файла MineSweeper.py
from MineSweeper import Board, Game, save_game_result, CELL_STATES


class TestMinesweeperLogic(unittest.TestCase):

    def setUp(self):
        # Создаем небольшую доску для тестов
        self.cols = 5
        self.rows = 5
        self.bombs = 3
        self.game = Game(self.cols, self.rows, self.bombs, 'Легко')

    def test_board_initialization(self):
        board = Board(4, 4, 2)
        self.assertEqual(board.cols, 4)
        self.assertEqual(board.rows, 4)
        self.assertEqual(board.bombs_amount, 2)
        # Изначально бомбы не размещены
        self.assertEqual(len(board.bombs), 0)

    def test_place_bombs_excludes_first_click(self):
        board = Board(5, 5, 3)
        first_x, first_y = 2, 2
        board.place_bombs(first_x, first_y)
        # Проверяем что бомбы не расположены в соседних клетках с первой кликом
        for bx, by in board.bombs:
            self.assertFalse(abs(bx - first_x) <= 1 and abs(by - first_y) <= 1)

    def test_count_bombs_around(self):
        board = Board(3, 3, 0)
        # Расставим бомбы вручную
        board.bombs = [(0, 0), (1, 1)]
        count = board.count_bombs_around(1, 0)
        self.assertEqual(count, 2)

    def test_reveal_empty_cell_triggers_recursive_opening(self):
        game = Game(3, 3, 0, 'Легко')
        game.board.bombs = []
        game.board.init_hidden_board()

        # Установим число вокруг (1,1) равное 0 для вызова рекурсии
        for y in range(3):
            for x in range(3):
                if (x, y) != (1, 1):
                    game.board.hidden_board[y][x] = 0

        # Обозначим клетку (1,1) как закрытую и открытую только (1,1)
        game.board.visible_board[1][1] = CELL_STATES.index('closed')

        # Открываем клетку (2,2), которая должна вызвать рекурсивное открытие соседних клеток
        game.reveal(2, 2)

        # Проверяем что соседние клетки открыты
        for y in range(3):
            for x in range(3):
                if (x, y) != (1, 1):
                    self.assertEqual(game.board.visible_board[y][x], CELL_STATES.index('opened'))

    def test_win_condition(self):
        game = Game(2, 2, 1, 'Легко')

        # Расставим бомбу в одной из клеток и подготовим доску
        game.board.bombs = [(0, 0)]
        game.board.init_hidden_board()

        # Открываем все клетки кроме бомбы
        for y in range(2):
            for x in range(2):
                if (x, y) != (0, 0):
                    game.reveal(x, y)

        # Проверяем что игра завершилась победой
        self.assertEqual(game.state, 'win')

    def test_lose_condition_on_bomb(self):
        game = Game(2, 2, 1, 'Легко')

        # Расставим бомбу и подготовим доску
        game.board.bombs = [(0, 0)]
        game.board.init_hidden_board()

        # Открываем клетку с бомбой
        game.reveal(0, 0)

        # Проверяем что состояние игры - проигрыш
        self.assertEqual(game.state, 'lose')

    def test_reveal_already_opened_cell_does_nothing(self):
        game = Game(3, 3, 1, 'Легко')

        # Расставим бомбу и подготовим доску
        game.board.bombs = [(1, 1)]
        game.board.init_hidden_board()

        # Открываем клетку (0 ,0)
        game.reveal(0, 0)

        initial_visible_state = game.board.visible_board[0][0]

        # Попытка открыть уже открытую клетку не должна менять состояние или вызывать ошибку
        # В текущей логике ничего не происходит — просто проверяем что состояние осталось тем же

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


if __name__ == '__main__':
    unittest.main()