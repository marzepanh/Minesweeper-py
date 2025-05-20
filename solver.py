from itertools import combinations

CELL_STATES = ['closed', 'opened', 'flagged', 'bombed', 'nobomb']

class MinesweeperSolver:
    def __init__(self, visible_board, hidden_board):
        self.visible = visible_board
        self.hidden = hidden_board
        self.rows = len(visible_board)
        self.cols = len(visible_board[0]) if self.rows > 0 else 0

    def in_range(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows

    def neighbors(self, x, y):
        for nx in range(x - 1, x + 2):
            for ny in range(y - 1, y + 2):
                if (nx, ny) != (x, y) and self.in_range(nx, ny):
                    yield (nx, ny)

    def solve_step(self):
        actions = []
        known_safe = set()
        known_mines = set()

        for y in range(self.rows):
            for x in range(self.cols):
                if self.visible[y][x] == CELL_STATES.index('opened'):
                    num = self.hidden[y][x]
                    if num <= 0:
                        continue

                    flagged = 0
                    closed = []
                    for nx, ny in self.neighbors(x, y):
                        state = self.visible[ny][nx]
                        if state == CELL_STATES.index('flagged'):
                            flagged += 1
                        elif state == CELL_STATES.index('closed'):
                            closed.append((nx, ny))

                    # Обычные эвристики
                    if flagged == num:
                        known_safe.update(closed)
                    if flagged + len(closed) == num:
                        known_mines.update(closed)

        # Добавим логические выводы на основе групп
        opened_cells = [
            (x, y) for y in range(self.rows) for x in range(self.cols)
            if self.visible[y][x] == CELL_STATES.index('opened') and self.hidden[y][x] > 0
        ]

        for (x1, y1), (x2, y2) in combinations(opened_cells, 2):
            n1 = set((nx, ny) for nx, ny in self.neighbors(x1, y1)
                     if self.visible[ny][nx] == CELL_STATES.index('closed'))
            n2 = set((nx, ny) for nx, ny in self.neighbors(x2, y2)
                     if self.visible[ny][nx] == CELL_STATES.index('closed'))

            f1 = sum(1 for nx, ny in self.neighbors(x1, y1)
                     if self.visible[ny][nx] == CELL_STATES.index('flagged'))
            f2 = sum(1 for nx, ny in self.neighbors(x2, y2)
                     if self.visible[ny][nx] == CELL_STATES.index('flagged'))

            m1 = self.hidden[y1][x1] - f1
            m2 = self.hidden[y2][x2] - f2

            if n1 and n2:
                if n1.issubset(n2) and m1 == m2:
                    # n2 - n1 точно безопасны
                    known_safe.update(n2 - n1)
                elif n2.issubset(n1) and m2 == m1:
                    known_safe.update(n1 - n2)
                elif n1.issubset(n2) and (m2 - m1) == len(n2 - n1):
                    known_mines.update(n2 - n1)
                elif n2.issubset(n1) and (m1 - m2) == len(n1 - n2):
                    known_mines.update(n1 - n2)

        # Преобразуем в действия
        for (x, y) in known_safe:
            actions.append(('open', x, y))
        for (x, y) in known_mines:
            actions.append(('flag', x, y))

        # Удаляем дубли
        unique_actions = []
        seen = set()
        for act in actions:
            if (act[0], act[1], act[2]) not in seen:
                unique_actions.append(act)
                seen.add((act[0], act[1], act[2]))

        return unique_actions
