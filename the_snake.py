"""Змейка на pygame.

Игрок управляет Змейкой, которая перемещается по сетке,
собирает Яблоки и растет. Либо поедает Яд и уменьшается.
"""
# Заставляет Python хранить аннотации как строки, не вычисляя их
from __future__ import annotations

from random import randint, choice
from typing import Final, Iterable, Optional

import pygame

# Псевдонимы типов для читаемых сигнатур:
Point = tuple[int, int]
Color = tuple[int, int, int]
Direction = tuple[int, int]

# Константы для размеров поля и сетки:
SCREEN_WIDTH: Final[int] = 640
SCREEN_HEIGHT: Final[int] = 480
GRID_SIZE: Final[int] = 20
GRID_WIDTH: Final[int] = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT: Final[int] = SCREEN_HEIGHT // GRID_SIZE

# Направления движения:
UP: Final[Direction] = (0, -1)
DOWN: Final[Direction] = (0, 1)
LEFT: Final[Direction] = (-1, 0)
RIGHT: Final[Direction] = (1, 0)

TURN_KEYS: Final[dict[tuple[int, Direction], Direction]] = {
    (pygame.K_UP, LEFT): UP,
    (pygame.K_UP, RIGHT): UP,
    (pygame.K_DOWN, LEFT): DOWN,
    (pygame.K_DOWN, RIGHT): DOWN,
    (pygame.K_LEFT, UP): LEFT,
    (pygame.K_LEFT, DOWN): LEFT,
    (pygame.K_RIGHT, UP): RIGHT,
    (pygame.K_RIGHT, DOWN): RIGHT,
}

# Цвета в формате RGB:
BOARD_BACKGROUND_COLOR: Final[Color] = (0, 0, 0)
BORDER_COLOR: Final[Color] = (93, 216, 228)
APPLE_COLOR: Final[Color] = (255, 0, 0)
SNAKE_COLOR: Final[Color] = (0, 255, 0)
POISON_COLOR: Final[Color] = (128, 0, 128)

# Скорость движения Змейки:
SPEED: Final[int] = 5

# Настройка игрового окна:
pygame.init()
screen: pygame.Surface = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32
)
pygame.display.set_caption('Змейка')
clock: pygame.time.Clock = pygame.time.Clock()


class GameObject:
    """Базовый класс игровых объектов."""

    position: Point
    body_color: Optional[Color]

    def __init__(
        self,
        position: Optional[Point] = None,
        body_color: Optional[Color] = None,
    ) -> None:
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

    def draw(self) -> None:
        """Рисует объект на экране. Будет реализован в дочерних классах."""


class Food(GameObject):
    """Базовый класс для съедобных объектов (Яблоко, Яд)."""

    def __init__(self, body_color: Color) -> None:
        """Создает объект еды со случайной позицией.

        Args:
            body_color (tuple): Кортеж цвета (R, G, B).
        """
        super().__init__(body_color=body_color)
        self.randomize_position()

    def randomize_position(self, occupied: Iterable[Point] = ()) -> None:
        """Задает случайные координаты в пределах игрового поля.

        Координаты выровнены по сетке и не попадают в клетки из
        occupied (сегменты Змейки, позиция другой еды).

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

    def draw(self) -> None:
        """Рисует объект еды на экране в соответствии со своими атрибутами."""
        rect = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, rect)
        pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


class Apple(Food):
    """Игровой объект Яблоко, собираемый игроком."""

    def __init__(self) -> None:
        """Создает экземпляр Яблока со случайной позицией."""
        super().__init__(body_color=APPLE_COLOR)


class Snake(GameObject):
    """Игровой объект Змейка, управляемый игроком."""

    body_color: Color
    positions: list[Point]
    length: int
    direction: Direction
    next_direction: Optional[Direction]
    last: Optional[Point]

    def __init__(self) -> None:
        """Создает экземпляр Змейки с позицией в середине экрана."""
        super().__init__(body_color=SNAKE_COLOR)
        self.reset()

    def get_head_position(self) -> Point:
        """Возвращает координаты головы Змейки."""
        return self.positions[0]

    def move(self) -> None:
        """Вычисляет новую позицию головы и обновляет список сегментов тела.

        Использует оператор % для "замотки"/"телепорта" через границы поля.
        Удаляет хвостовой сегмент, если Змейка не выросла.
        """
        head_x, head_y = self.get_head_position()
        dx, dy = self.direction

        new_x = (head_x + dx * GRID_SIZE) % SCREEN_WIDTH
        new_y = (head_y + dy * GRID_SIZE) % SCREEN_HEIGHT
        self.positions.insert(0, (new_x, new_y))

        if len(self.positions) > self.length:
            self.last = self.positions.pop()
        else:
            self.last = None

    def draw(self) -> None:
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

        head_rect = pygame.Rect(
            self.get_head_position(),
            (GRID_SIZE, GRID_SIZE)
        )
        pygame.draw.rect(screen, self.body_color, head_rect)
        pygame.draw.rect(screen, BORDER_COLOR, head_rect, 1)

    def reset(self) -> None:
        """Возвращает Змейку в начальное состояние (центр экрана)."""
        self.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.length = 1
        self.positions = [self.position]
        self.direction = choice((RIGHT, LEFT, DOWN, UP))
        self.next_direction = None
        self.last = None

    def update_direction(self) -> None:
        """Обновляет направление Змейки после пользовательского ввода."""
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None


class Poison(Food):
    """Игровой объект Яд, вредящий Змейке."""

    def __init__(self) -> None:
        """Создает экземпляр Яда со случайной позицией."""
        super().__init__(body_color=POISON_COLOR)


def handle_keys(game_object: Snake) -> None:
    """Обрабатывает события клавиатуры и обновляет направление движения.

    Считывает очередь событий pygame. При событии QUIT завершает игру.
    При нажатии стрелки ищет пару (клавиша, текущее направление) в
    TURN_KEYS и сохраняет найденное направление в
    game_object.next_direction. Разворот на 180° в словаре отсутствует,
    поэтому соответствующее нажатие игнорируется.

    Args:
        game_object (Snake): Игровой объект с атрибутами direction и
            next_direction.

    Raises:
        SystemExit: Если получено событие pygame.QUIT.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        elif event.type == pygame.KEYDOWN:
            new_direction = TURN_KEYS.get((event.key, game_object.direction))
            if new_direction is not None:
                game_object.next_direction = new_direction


def main() -> None:
    """Создает игровые объекты и запускает основной игровой цикл.

    Обрабатывает ввод, движение Змейки, столкновения с Яблоком
    и собственным телом, положение Яблока и Яда относительно Змейки
    и друг друга, а также отрисовку состояния экрана.
    """
    snake = Snake()
    apple = Apple()
    poison = Poison()

    apple.randomize_position(snake.positions + [poison.position])
    poison.randomize_position(snake.positions + [apple.position])

    while True:
        clock.tick(SPEED)

        # 1. Ввод и смена направления.
        handle_keys(snake)
        snake.update_direction()

        snake.move()
        head_position = snake.get_head_position()
        # 2. Проверка на съеденное Яблоко.
        if head_position == apple.position:
            snake.length += 1
            apple.randomize_position(snake.positions + [poison.position])

        # 3. Проверка на съеденный Яд.
        if head_position == poison.position:
            if snake.length > 1:
                snake.length -= 1
                removed_segment = snake.positions.pop()
                rect = pygame.Rect(removed_segment, (GRID_SIZE, GRID_SIZE))
                pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, rect)

            poison.randomize_position(snake.positions + [apple.position])

        # 4. Проверка на столкновение Змейки с собой.
        if head_position in snake.positions[1:]:
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
