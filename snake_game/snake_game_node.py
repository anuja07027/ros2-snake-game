#!/usr/bin/env python3

import random

import pygame
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SnakeGameNode(Node):

    def __init__(self):
        super().__init__('snake_game_node')

        # ROS publisher
        self.score_publisher = self.create_publisher(
            String,
            '/snake/score',
            10
        )

        self.status_publisher = self.create_publisher(
            String,
            '/snake/status',
            10
        )

        # Pygame initialization
        pygame.init()

        self.cell_size = 20
        self.grid_width = 30
        self.grid_height = 20

        self.screen_width = self.grid_width * self.cell_size
        self.screen_height = self.grid_height * self.cell_size

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )

        pygame.display.set_caption("ROS 2 Snake Game")

        self.clock = pygame.time.Clock()
        self.game_speed = 10

        # Colors
        self.background = (20, 20, 20)
        self.snake_color = (50, 200, 50)
        self.food_color = (220, 50, 50)
        self.text_color = (255, 255, 255)

        # Game state
        self.snake = [
            (self.grid_width // 2, self.grid_height // 2),
            (self.grid_width // 2 - 1, self.grid_height // 2),
            (self.grid_width // 2 - 2, self.grid_height // 2)
        ]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.food = self.generate_food()

        self.score = 0
        self.game_over = False

        self.timer = self.create_timer(
            1.0 / self.game_speed,
            self.game_loop
        )

        self.publish_status("Game started")

    # -------------------------------------------------
    # Generate food
    # -------------------------------------------------

    def generate_food(self):

        while True:

            food = (
                random.randint(0, self.grid_width - 1),
                random.randint(0, self.grid_height - 1)
            )

            if food not in self.snake:
                return food

    # -------------------------------------------------
    # Publish score
    # -------------------------------------------------

    def publish_score(self):

        message = String()
        message.data = f"Score: {self.score}"

        self.score_publisher.publish(message)

    # -------------------------------------------------
    # Publish game status
    # -------------------------------------------------

    def publish_status(self, status):

        message = String()
        message.data = status

        self.status_publisher.publish(message)

    # -------------------------------------------------
    # Keyboard control
    # -------------------------------------------------

    def handle_keyboard(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.game_over = True
                self.publish_status("Game closed")

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_UP:
                    if self.direction != (0, 1):
                        self.next_direction = (0, -1)

                elif event.key == pygame.K_DOWN:
                    if self.direction != (0, -1):
                        self.next_direction = (0, 1)

                elif event.key == pygame.K_LEFT:
                    if self.direction != (1, 0):
                        self.next_direction = (-1, 0)

                elif event.key == pygame.K_RIGHT:
                    if self.direction != (-1, 0):
                        self.next_direction = (1, 0)

                elif event.key == pygame.K_r:

                    if self.game_over:
                        self.reset_game()

    # -------------------------------------------------
    # Move snake
    # -------------------------------------------------

    def move_snake(self):

        self.direction = self.next_direction

        head_x, head_y = self.snake[0]

        dx, dy = self.direction

        new_head = (
            head_x + dx,
            head_y + dy
        )

        # Wall collision
        if (
            new_head[0] < 0
            or new_head[0] >= self.grid_width
            or new_head[1] < 0
            or new_head[1] >= self.grid_height
        ):

            self.game_over = True
            self.publish_status("Game Over - Wall collision")
            return

        # Self collision
        if new_head in self.snake:

            self.game_over = True
            self.publish_status("Game Over - Self collision")
            return

        # Add new head
        self.snake.insert(0, new_head)

        # Food collision
        if new_head == self.food:

            self.score += 1

            self.food = self.generate_food()

            self.publish_score()

        else:

            self.snake.pop()

    # -------------------------------------------------
    # Draw game
    # -------------------------------------------------

    def draw_game(self):

        self.screen.fill(self.background)

        # Draw snake
        for segment in self.snake:

            x, y = segment

            rectangle = pygame.Rect(
                x * self.cell_size,
                y * self.cell_size,
                self.cell_size,
                self.cell_size
            )

            pygame.draw.rect(
                self.screen,
                self.snake_color,
                rectangle
            )

        # Draw food
        food_x, food_y = self.food

        food_rectangle = pygame.Rect(
            food_x * self.cell_size,
            food_y * self.cell_size,
            self.cell_size,
            self.cell_size
        )

        pygame.draw.rect(
            self.screen,
            self.food_color,
            food_rectangle
        )

        # Score
        font = pygame.font.Font(None, 30)

        score_text = font.render(
            f"Score: {self.score}",
            True,
            self.text_color
        )

        self.screen.blit(
            score_text,
            (10, 10)
        )

        # Game Over screen
        if self.game_over:

            game_over_font = pygame.font.Font(None, 50)

            game_over_text = game_over_font.render(
                "GAME OVER - Press R",
                True,
                self.text_color
            )

            text_rectangle = game_over_text.get_rect(
                center=(
                    self.screen_width // 2,
                    self.screen_height // 2
                )
            )

            self.screen.blit(
                game_over_text,
                text_rectangle
            )

        pygame.display.flip()

    # -------------------------------------------------
    # Reset game
    # -------------------------------------------------

    def reset_game(self):

        self.snake = [
            (self.grid_width // 2, self.grid_height // 2),
            (self.grid_width // 2 - 1, self.grid_height // 2),
            (self.grid_width // 2 - 2, self.grid_height // 2)
        ]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.score = 0

        self.food = self.generate_food()

        self.game_over = False

        self.publish_score()
        self.publish_status("Game restarted")

    # -------------------------------------------------
    # Main game loop
    # -------------------------------------------------

    def game_loop(self):

        if not rclpy.ok():
            return

        self.handle_keyboard()

        if not self.game_over:

            self.move_snake()

        self.draw_game()


def main(args=None):

    rclpy.init(args=args)

    node = SnakeGameNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        pygame.quit()

        rclpy.shutdown()


if __name__ == '__main__':
    main()
