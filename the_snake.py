"""Змейка на pygame.

Игрок управляет змейкой, которая перемещается по сетке,
собирает Яблоки и растет. Либо поедает Яд и уменьшается.
"""
from random import randint

import pygame

# Константы для размеров поля и сетки:
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Направления движения:
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Цвета в формате RGB:
BOARD_BACKGROUND_COLOR = (0, 0, 0)
BORDER_COLOR = (93, 216, 228)
APPLE_COLOR = (255, 0, 0)
SNAKE_COLOR = (0, 255, 0)
POISON_COLOR = (128, 0, 128)

# Скорость движения змейки:
SPEED = 5

# Настройка игрового окна:
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pygame.display.set_caption('Змейка')
clock = pygame.time.Clock()


class GameObject:
    """Базовый класс игровых объектов."""

    def __init__(self, position=None, body_color=None):
        """Инициализирует атрибуты экземпляра класса.

        Принимает два параметра: позицию и цвет объекта.

        Args:
            position (tuple): Кортеж координат (x, y).
            body_color (tuple): Кортеж цвета (R, G, B).
        """
        if position is None:
            position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.position = position
        self.body_color = body_color

    def draw(self):
        """Рисует объект на экране. Будет реализован в дочерних классах."""
        pass


class Food(GameObject):
    """Базовый класс для съедобных объектов (Яблоко, Яд)."""

    def __init__(self, body_color):
        """Создает объект еды со случайной позицией.

        Args:
            body_color (tuple): Кортеж цвета (R, G, B).
        """
        super().__init__(body_color=body_color)
        self.randomize_position()

    def randomize_position(self, occupied=()):
        """Задает случайные координаты в пределах игрового поля.

        Координаты выровнены по сетке и не попадают в клетки из
        ``occupied`` (сегменты змейки, позиция другой еды).

        Args:
            occupied (iterable): Позиции (x, y), которые нужно
                исключить при выборе новой клетки.
        """
        occupied = set(occupied)
        while True:
            position = (
                randint(0, GRID_WIDTH - 1) * GRID_SIZE,
                randint(0, GRID_HEIGHT - 1) * GRID_SIZE,
            )
            if position not in occupied:
                self.position = position
                return

    def draw(self):
        """Рисует объект еды на экране в соответствии со своими атрибутами."""
        rect = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, rect)
        pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


class Apple(Food):
    """Игровой объект Яблоко, собираемый игроком."""

    def __init__(self):
        """Создает экземпляр яблока со случайной позицией."""
        super().__init__(body_color=APPLE_COLOR)


class Snake(GameObject):
    """Игровой объект Змейка, управляемый игроком."""

    def __init__(self):
        """Создает экземпляр Змейки с позицией в середине экрана."""
        super().__init__(body_color=SNAKE_COLOR)
        self.length = 1
        self.positions = [self.position]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None

    def get_head_position(self):
        """Возвращает координаты головы Змейки."""
        return self.positions[0]

    def move(self):
        """Вычисляет новую позицию головы и обновляет список сегментов тела.

        Использует оператор % для "замотки"/"телепорта" через границы поля.
        Удаляет хвостовой сегмент, если Змейка не выросла.
        """
        head = self.get_head_position()
        dx, dy = self.direction

        new_x = (head[0] + dx * GRID_SIZE) % SCREEN_WIDTH
        new_y = (head[1] + dy * GRID_SIZE) % SCREEN_HEIGHT
        self.positions.insert(0, (new_x, new_y))

        if len(self.positions) > self.length:
            self.last = self.positions.pop()
        else:
            self.last = None

    def draw(self):
        """Рисует тело и голову Змейки, стирает предыдущий хвост.

        Сначала стирается self.last — клетка, с которой Змейка
        «уползла», — чтобы не затереть Яблоко или Яд, которые могут
        оказаться в этой клетке и рисуются в этом же кадре поверх.
        """
        if self.last is not None:
            last_rect = pygame.Rect(self.last, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, last_rect)

        for position in self.positions[:-1]:
            rect = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, self.body_color, rect)
            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

        head_rect = pygame.Rect(self.positions[0], (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, head_rect)
        pygame.draw.rect(screen, BORDER_COLOR, head_rect, 1)

    def reset(self):
        """Возвращает змейку в начальное состояние (центр экрана)."""
        self.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.length = 1
        self.positions = [self.position]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None

    def update_direction(self):
        """Обновляет направление змейки после пользовательского ввода."""
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None


class Poison(Food):
    """Игровой объект Яд, вредящий змейке."""

    def __init__(self):
        """Создает экземпляр Яда со случайной позицией."""
        super().__init__(body_color=POISON_COLOR)


def handle_keys(game_object):
    """Обрабатывает события клавиатуры и обновляет направление движения.

    Считывает очередь событий pygame. При событии QUIT завершает игру.
    При нажатии стрелки сохраняет новое направление в
    game_object.next_direction, если оно не противоположно текущему
    game_object.direction — это предотвращает разворот на 180°.

    Args:
        game_object (Snake): Игровой объект с атрибутами direction и
        next_direction.

    Raises:
        SystemExit: Если получено событие ``pygame.QUIT``.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and game_object.direction != DOWN:
                game_object.next_direction = UP
            elif event.key == pygame.K_DOWN and game_object.direction != UP:
                game_object.next_direction = DOWN
            elif event.key == pygame.K_LEFT and game_object.direction != RIGHT:
                game_object.next_direction = LEFT
            elif event.key == pygame.K_RIGHT and game_object.direction != LEFT:
                game_object.next_direction = RIGHT


def main():
    """Создает игровые объекты и запускает основной игровой цикл.

    Обрабатывает ввод, движение змейки, столкновения с Яблоком
    и собственным телом, положение Яблока и Яда относительно змейки
    и друг друга, а также отрисовку состояния экрана.
    """
    snake = Snake()
    apple = Apple()
    poison = Poison()

    # Первичное размещение еды с учётом позиций змейки и друг друга.
    apple.randomize_position(snake.positions + [poison.position])
    poison.randomize_position(snake.positions + [apple.position])

    while True:
        clock.tick(SPEED)

        # 1. Ввод и смена направления.
        handle_keys(snake)
        snake.update_direction()

        snake.move()

        # 2. Проверка на съеденное Яблоко.
        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position(snake.positions + [poison.position])

        # 3. Проверка на съеденный Яд.
        if snake.get_head_position() == poison.position:
            if snake.length > 1:
                snake.length -= 1
                removed_segment = snake.positions.pop()
                rect = pygame.Rect(removed_segment, (GRID_SIZE, GRID_SIZE))
                pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, rect)

            poison.randomize_position(snake.positions + [apple.position])

        # 4. Проверка на столкновение Змейки с собой.
        if snake.get_head_position() in snake.positions[1:]:
            snake.reset()
            screen.fill(BOARD_BACKGROUND_COLOR)
            apple.randomize_position(snake.positions + [poison.position])
            poison.randomize_position(snake.positions + [apple.position])

        # 5. Отрисовка и обновление экрана.
        snake.draw()
        apple.draw()
        poison.draw()
        pygame.display.update()


if __name__ == '__main__':
    main()
