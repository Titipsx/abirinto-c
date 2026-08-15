import asyncio
import math
import random
from collections import deque

import pygame


WIDTH, HEIGHT = 960, 720
TOP_BAR = 78
BOTTOM_BAR = 132
FPS = 60
AUTO_INTERVALS = {1: 520, 2: 300, 3: 150}

BLACK = (8, 12, 18)
NAVY = (15, 25, 38)
GREEN = (39, 224, 151)
GREEN_DARK = (21, 115, 83)
YELLOW = (255, 221, 79)
RED = (255, 83, 83)
WHITE = (238, 245, 255)
GRAY = (135, 153, 173)
BLUE = (57, 128, 237)

LEVELS = {
    "1": ("FACILE", 15, 9),
    "2": ("MEDIO", 23, 13),
    "3": ("DIFFICILE", 31, 17),
    "4": ("DIFFICILISSIMO", 39, 21),
}


class Maze:
    """Perfect maze generated with randomized depth-first search."""

    DIRECTIONS = (
        (0, -1, 0, 2),  # up / down
        (1, 0, 1, 3),   # right / left
        (0, 1, 2, 0),
        (-1, 0, 3, 1),
    )

    def __init__(self, cols, rows, min_dead_ends=0,
                 min_dead_end_length=0, min_dead_end_turns=0):
        self.cols = cols
        self.rows = rows
        self.start = (0, 0)
        self.min_dead_ends = min_dead_ends
        self.min_dead_end_length = min_dead_end_length
        self.min_dead_end_turns = min_dead_end_turns
        self.walls = []
        self.generate_with_dead_ends()
        self.end = self.farthest_cell(self.start)

    def generate_with_dead_ends(self):
        """Keeps the best connected maze until the requested dead ends exist."""
        best_walls = None
        best_count = -1
        for _attempt in range(120):
            self.walls = [[[True, True, True, True]
                           for _ in range(self.cols)] for _ in range(self.rows)]
            self.generate()
            count = self.qualified_dead_end_count()
            if count > best_count:
                best_count = count
                best_walls = [[cell[:] for cell in row] for row in self.walls]
            if count >= self.min_dead_ends:
                return
        self.walls = best_walls

    def generate(self):
        visited = {self.start}
        stack = [self.start]
        while stack:
            x, y = stack[-1]
            choices = []
            for dx, dy, wall, opposite in self.DIRECTIONS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in visited:
                    choices.append((nx, ny, wall, opposite))
            if not choices:
                stack.pop()
                continue
            nx, ny, wall, opposite = random.choice(choices)
            self.walls[y][x][wall] = False
            self.walls[ny][nx][opposite] = False
            visited.add((nx, ny))
            stack.append((nx, ny))

    def neighbours(self, cell):
        x, y = cell
        for dx, dy, wall, _ in self.DIRECTIONS:
            if not self.walls[y][x][wall]:
                yield x + dx, y + dy

    def dead_end_count(self):
        return sum(1 for y in range(self.rows) for x in range(self.cols)
                   if sum(not wall for wall in self.walls[y][x]) == 1)

    def dead_end_route_stats(self, cell):
        route = self.path(self.start, cell)
        directions = [(b[0] - a[0], b[1] - a[1])
                      for a, b in zip(route, route[1:])]
        turns = sum(first != second
                    for first, second in zip(directions, directions[1:]))
        return len(directions), turns

    def qualified_dead_end_count(self):
        count = 0
        for y in range(self.rows):
            for x in range(self.cols):
                cell = (x, y)
                if len(list(self.neighbours(cell))) != 1:
                    continue
                length, turns = self.dead_end_route_stats(cell)
                if (length >= self.min_dead_end_length and
                        turns >= self.min_dead_end_turns):
                    count += 1
        return count

    def farthest_cell(self, start):
        queue = deque([(start, 0)])
        visited = {start}
        farthest = start
        while queue:
            cell, _distance = queue.popleft()
            farthest = cell
            for nxt in self.neighbours(cell):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, _distance + 1))
        return farthest

    def path(self, start, end):
        queue = deque([start])
        previous = {start: None}
        while queue:
            cell = queue.popleft()
            if cell == end:
                break
            for nxt in self.neighbours(cell):
                if nxt not in previous:
                    previous[nxt] = cell
                    queue.append(nxt)
        result = []
        cell = end
        while cell is not None:
            result.append(cell)
            cell = previous[cell]
        return list(reversed(result))

    def can_move(self, cell, direction):
        x, y = cell
        dx, dy, wall, _ = self.DIRECTIONS[direction]
        if self.walls[y][x][wall]:
            return cell
        return x + dx, y + dy


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Labirinto - Endrigi Software")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("consolas", 34, bold=True)
        self.font = pygame.font.SysFont("consolas", 22, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 17)
        self.wall_textures = [self.make_wall_texture(index) for index in range(4)]
        self.state = "menu"
        self.mode_3d = False
        self.level_key = "2"
        self.maze = None
        self.player = (0, 0)
        self.steps = 0
        self.optimal_steps = 0
        self.solution_visible = False
        self.won = False
        self.facing = 1
        self.solution_auto = False
        self.solution_speed = 1
        self.auto_path = []
        self.auto_index = 0
        self.last_auto_tick = 0
        self.buttons = {}

    def make_wall_texture(self, variant):
        """Procedural dungeon stones: no external image assets required."""
        size = 64
        texture = pygame.Surface((size, size))
        palettes = (
            ((38, 43, 40), (100, 106, 96), (48, 91, 58)),
            ((44, 39, 36), (116, 99, 86), (65, 84, 48)),
            ((34, 41, 47), (89, 105, 113), (39, 76, 62)),
            ((45, 42, 32), (119, 112, 82), (73, 96, 46)),
        )
        mortar, base, moss = palettes[variant]
        texture.fill(mortar)
        brick_h = 16
        for row, y in enumerate(range(0, size, brick_h)):
            offset = -16 if (row + variant) % 2 else 0
            for x in range(offset, size, 32):
                rect = pygame.Rect(x + 2, y + 2, 29, brick_h - 3)
                variation = ((row * 19 + x * 7 + variant * 13) % 25) - 12
                stone = tuple(max(35, channel + variation) for channel in base)
                pygame.draw.rect(texture, stone, rect, border_radius=2)
                highlight = tuple(min(180, channel + 33) for channel in stone)
                shadow = tuple(max(25, channel - 42) for channel in stone)
                pygame.draw.line(texture, highlight, (rect.left + 2, rect.top + 2),
                                 (rect.right - 2, rect.top + 2), 1)
                pygame.draw.line(texture, shadow, (rect.left + 2, rect.bottom - 2),
                                 (rect.right - 2, rect.bottom - 2), 1)
                # Small cracks and moss give each block a dungeon look.
                if (row + x // 16) % 3 == 0:
                    pygame.draw.line(texture, (53, 58, 53), rect.center,
                                     (rect.centerx + 5, rect.centery + 4), 1)
                if (row * 5 + x + variant) % 4 == 0:
                    pygame.draw.circle(texture, moss,
                                       (rect.left + 6, rect.bottom - 3), 2)
                if variant == 2 and (row + x) % 3 == 0:
                    pygame.draw.line(texture, (62, 77, 86), rect.topleft,
                                     (rect.centerx, rect.bottom - 2), 1)
        return texture

    def new_game(self, level_key=None):
        if level_key:
            self.level_key = level_key
        _name, cols, rows = LEVELS[self.level_key]
        level = int(self.level_key)
        self.maze = Maze(cols, rows,
                         min_dead_ends=level * 3,
                         min_dead_end_length=level * 5,
                         min_dead_end_turns=level * 2)
        self.player = self.maze.start
        self.steps = 0
        self.solution_visible = False
        self.won = False
        self.facing = 1
        self.solution_auto = False
        self.solution_speed = 1
        self.auto_path = []
        self.auto_index = 0
        self.optimal_steps = len(self.maze.path(self.maze.start, self.maze.end)) - 1
        self.state = "play"

    def move(self, direction):
        if self.state != "play" or self.won:
            return
        new_position = self.maze.can_move(self.player, direction)
        if new_position != self.player:
            self.player = new_position
            self.steps += 1
            self.won = self.player == self.maze.end

    def move_3d(self, forward=True):
        direction = self.facing if forward else (self.facing + 2) % 4
        self.move(direction)

    def turn_3d(self, clockwise=True):
        if self.state == "play" and not self.won:
            self.facing = (self.facing + (1 if clockwise else -1)) % 4

    def start_auto_solution(self):
        if self.state != "play" or self.won:
            return
        self.solution_visible = True
        self.auto_path = self.maze.path(self.player, self.maze.end)
        self.auto_index = 1
        self.solution_auto = len(self.auto_path) > 1
        self.last_auto_tick = pygame.time.get_ticks()

    def update_auto_solution(self):
        if not self.solution_auto or self.won:
            return
        now = pygame.time.get_ticks()
        if now - self.last_auto_tick < AUTO_INTERVALS[self.solution_speed]:
            return
        self.last_auto_tick = now
        if self.auto_index >= len(self.auto_path):
            self.solution_auto = False
            return
        target = self.auto_path[self.auto_index]
        dx = target[0] - self.player[0]
        dy = target[1] - self.player[1]
        direction_by_delta = {(0, -1): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3}
        target_direction = direction_by_delta[(dx, dy)]
        if self.facing != target_direction:
            clockwise_distance = (target_direction - self.facing) % 4
            self.facing = (self.facing + (1 if clockwise_distance <= 2 else -1)) % 4
            return
        self.move(target_direction)
        self.auto_index += 1
        if self.won or self.auto_index >= len(self.auto_path):
            self.solution_auto = False

    def maze_geometry(self):
        available_w = WIDTH - 50
        available_h = HEIGHT - TOP_BAR - BOTTOM_BAR - 20
        cell = max(8, min(available_w // self.maze.cols, available_h // self.maze.rows))
        maze_w = cell * self.maze.cols
        maze_h = cell * self.maze.rows
        ox = (WIDTH - maze_w) // 2
        oy = TOP_BAR + (available_h - maze_h) // 2
        return ox, oy, cell

    def draw_text(self, text, font, color, center):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=center)
        self.screen.blit(surface, rect)

    def draw_button(self, key, rect, label, color=GREEN_DARK):
        self.buttons[key] = pygame.Rect(rect)
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, GREEN, rect, 2, border_radius=10)
        self.draw_text(label, self.font, WHITE, pygame.Rect(rect).center)

    def draw_menu(self):
        self.screen.fill(BLACK)
        self.draw_text("LABIRINTO", self.title_font, YELLOW, (WIDTH // 2, 90))
        self.draw_text("Versione Python del gioco originale", self.small_font, GRAY, (WIDTH // 2, 132))
        self.draw_text("Scegli il livello di difficoltà", self.font, WHITE, (WIDTH // 2, 195))
        self.buttons.clear()
        for index, (key, (name, cols, rows)) in enumerate(LEVELS.items()):
            x = WIDTH // 2 - 190
            y = 235 + index * 72
            self.draw_button("level_" + key, (x, y, 380, 54), f"{key}. {name}  ({cols}×{rows})")
        mode_color = BLUE if self.mode_3d else GREEN_DARK
        mode_label = "MODALITÀ 3D: ACCESA" if self.mode_3d else "MODALITÀ 3D: SPENTA"
        self.draw_button("toggle_3d", (WIDTH // 2 - 190, 535, 380, 54), mode_label, mode_color)
        self.draw_text("Tastiera: premi anche 1, 2, 3 o 4", self.small_font, GRAY, (WIDTH // 2, 620))

    def draw_maze(self):
        ox, oy, cell = self.maze_geometry()
        for y in range(self.maze.rows):
            for x in range(self.maze.cols):
                left, top = ox + x * cell, oy + y * cell
                walls = self.maze.walls[y][x]
                if walls[0]:
                    pygame.draw.line(self.screen, GREEN, (left, top), (left + cell, top), 2)
                if walls[1]:
                    pygame.draw.line(self.screen, GREEN, (left + cell, top), (left + cell, top + cell), 2)
                if walls[2]:
                    pygame.draw.line(self.screen, GREEN, (left, top + cell), (left + cell, top + cell), 2)
                if walls[3]:
                    pygame.draw.line(self.screen, GREEN, (left, top), (left, top + cell), 2)

        if self.solution_visible:
            points = [(ox + x * cell + cell // 2, oy + y * cell + cell // 2)
                      for x, y in self.maze.path(self.player, self.maze.end)]
            if len(points) > 1:
                pygame.draw.lines(self.screen, RED, False, points, max(2, cell // 5))

        sx, sy = self.maze.start
        ex, ey = self.maze.end
        self.draw_text("*", self.font, RED, (ox + sx * cell + cell // 2, oy + sy * cell + cell // 2))
        self.draw_text("@", self.font, YELLOW, (ox + ex * cell + cell // 2, oy + ey * cell + cell // 2))
        px, py = self.player
        radius = max(4, cell // 3)
        pygame.draw.circle(self.screen, BLUE, (ox + px * cell + cell // 2, oy + py * cell + cell // 2), radius)
        pygame.draw.circle(self.screen, WHITE, (ox + px * cell + cell // 2, oy + py * cell + cell // 2), radius, 2)

    def draw_controls(self):
        self.buttons.clear()
        y = HEIGHT - 112
        size = 48
        center_x = 130
        self.draw_button("up", (center_x, y, size, size), "↑")
        self.draw_button("left", (center_x - 55, y + 52, size, size), "↶" if self.mode_3d else "←")
        self.draw_button("down", (center_x, y + 52, size, size), "↓")
        self.draw_button("right", (center_x + 55, y + 52, size, size), "↷" if self.mode_3d else "→")
        solution_label = (f"AUTO ×{self.solution_speed}" if self.solution_auto
                          else "SOLUZIONE")
        self.draw_button("solution", (350, y + 22, 200, 54), solution_label,
                         RED if self.solution_visible else GREEN_DARK)
        self.draw_button("new", (575, y + 22, 145, 54), "NUOVO")
        self.draw_button("menu", (745, y + 22, 140, 54), "MENU")

    def draw_play(self):
        if self.mode_3d:
            self.draw_play_3d()
            return
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, NAVY, (0, 0, WIDTH, TOP_BAR))
        level_name = LEVELS[self.level_key][0]
        self.draw_text(f"* INIZIO   @ FINE   LIVELLO: {level_name}", self.font, GREEN, (WIDTH // 2, 25))
        self.draw_text(f"PASSI: {self.steps}", self.small_font, WHITE, (WIDTH // 2, 55))
        self.draw_maze()
        pygame.draw.rect(self.screen, NAVY, (0, HEIGHT - BOTTOM_BAR, WIDTH, BOTTOM_BAR))
        self.draw_controls()
        if self.won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 165))
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, NAVY, (210, 215, 540, 280), border_radius=18)
            pygame.draw.rect(self.screen, YELLOW, (210, 215, 540, 280), 3, border_radius=18)
            self.draw_text("BRAVO!", self.title_font, YELLOW, (WIDTH // 2, 260))
            self.draw_text(f"Passi effettuati: {self.steps}", self.font, WHITE, (WIDTH // 2, 315))
            self.draw_text(f"Minimo necessario: {self.optimal_steps}", self.font, GREEN, (WIDTH // 2, 355))
            extra = self.steps - self.optimal_steps
            result = "PERCORSO PERFETTO!" if extra == 0 else f"Passi in più: {extra}"
            self.draw_text(result, self.font, YELLOW if extra == 0 else RED, (WIDTH // 2, 400))
            self.draw_text("Premi INVIO o tocca NUOVO", self.small_font, GRAY, (WIDTH // 2, 455))

    def occupancy_grid(self):
        """Turns cell walls into a dense grid suitable for ray casting."""
        grid_w = self.maze.cols * 2 + 1
        grid_h = self.maze.rows * 2 + 1
        grid = [[1 for _ in range(grid_w)] for _ in range(grid_h)]
        for y in range(self.maze.rows):
            for x in range(self.maze.cols):
                gx, gy = x * 2 + 1, y * 2 + 1
                grid[gy][gx] = 0
                for dx, dy, wall, _ in self.maze.DIRECTIONS:
                    if not self.maze.walls[y][x][wall]:
                        grid[gy + dy][gx + dx] = 0
        return grid

    def cast_ray(self, grid, px, py, angle, max_distance=80.0):
        step = 0.035
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        distance = 0.0
        while distance < max_distance:
            rx, ry = px + cos_a * distance, py + sin_a * distance
            gx, gy = int(rx), int(ry)
            if gy < 0 or gy >= len(grid) or gx < 0 or gx >= len(grid[0]) or grid[gy][gx]:
                return distance, rx, ry, gx, gy
            distance += step
        rx, ry = px + cos_a * max_distance, py + sin_a * max_distance
        return max_distance, rx, ry, int(rx), int(ry)

    def draw_side_passage_cues(self, view):
        """Light near an opening and shadow near a closed lateral wall."""
        left_open = self.maze.can_move(self.player, (self.facing - 1) % 4) != self.player
        right_open = self.maze.can_move(self.player, (self.facing + 1) % 4) != self.player
        cue = pygame.Surface(view.size, pygame.SRCALPHA)
        width = min(190, view.width // 3)
        for side, is_open in (("left", left_open), ("right", right_open)):
            for band in range(width):
                strength = 1.0 - band / width
                if is_open:
                    color = (255, 193, 90, int(72 * strength))
                else:
                    color = (0, 0, 0, int(110 * strength))
                x = band if side == "left" else view.width - 1 - band
                pygame.draw.line(cue, color, (x, 0), (x, view.height))
        self.screen.blit(cue, view.topleft)

    def draw_goal_diamond(self, view, grid, player_x, player_y, base_angle, fov):
        goal_x = self.maze.end[0] * 2 + 1.5
        goal_y = self.maze.end[1] * 2 + 1.5
        dx, dy = goal_x - player_x, goal_y - player_y
        distance = math.hypot(dx, dy)
        if distance < .05:
            return
        angle = math.atan2(dy, dx)
        difference = (angle - base_angle + math.pi) % (2 * math.pi) - math.pi
        if abs(difference) > fov * .56:
            return
        wall_distance, _hx, _hy, _gx, _gy = self.cast_ray(
            grid, player_x, player_y, angle, max_distance=distance + .5)
        if wall_distance < distance - .28:
            return

        screen_x = view.centerx + int((difference / (fov / 2)) * (view.width / 2))
        pulse = 1.0 + math.sin(pygame.time.get_ticks() * .009) * .10
        size = int(max(12, min(180, view.height * .72 / max(.55, distance))) * pulse)
        center_y = int(view.y + view.height * .52 + math.sin(pygame.time.get_ticks() * .005) * 5)
        glow = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        gc = glow.get_rect().center
        for radius, alpha in ((size, 20), (int(size * .72), 35), (int(size * .48), 60)):
            pygame.draw.circle(glow, (92, 223, 255, alpha), gc, max(1, radius))
        self.screen.blit(glow, (screen_x - glow.get_width() // 2,
                               center_y - glow.get_height() // 2))
        half = size // 2
        points = ((screen_x, center_y - half),
                  (screen_x + half, center_y),
                  (screen_x, center_y + half),
                  (screen_x - half, center_y))
        pygame.draw.polygon(self.screen, (89, 225, 255), points)
        pygame.draw.polygon(self.screen, WHITE, points, max(1, size // 15))
        pygame.draw.polygon(self.screen, (189, 250, 255),
                            ((screen_x, center_y - half),
                             (screen_x, center_y),
                             (screen_x - half, center_y)))
        sparkle = max(5, size // 3)
        pygame.draw.line(self.screen, WHITE, (screen_x - sparkle, center_y - half),
                         (screen_x + sparkle, center_y - half), 2)
        pygame.draw.line(self.screen, WHITE, (screen_x, center_y - half - sparkle),
                         (screen_x, center_y - half + sparkle), 2)

    def draw_dungeon_background(self, view, horizon):
        # Uneven vaulted darkness above the player.
        ceiling_height = horizon - view.y
        for band in range(ceiling_height):
            depth = band / max(1, ceiling_height)
            color = (int(12 + depth * 18), int(15 + depth * 20), int(16 + depth * 18))
            pygame.draw.line(self.screen, color, (view.x, view.y + band),
                             (view.right, view.y + band))
        for x in range(view.x, view.right, 90):
            pygame.draw.line(self.screen, (24, 28, 27), (x, view.y),
                             (view.x + view.width // 2, horizon), 1)

        # Perspective flagstones on the floor.
        pygame.draw.rect(self.screen, (45, 42, 36),
                         (view.x, horizon, view.width, view.bottom - horizon))
        vanishing_x = view.centerx
        for x in range(view.x - view.width, view.right + view.width, 72):
            pygame.draw.line(self.screen, (24, 25, 23), (vanishing_x, horizon),
                             (x, view.bottom), 2)
            pygame.draw.line(self.screen, (78, 72, 60), (vanishing_x + 1, horizon),
                             (x + 2, view.bottom), 1)
        floor_h = view.bottom - horizon
        for index in range(1, 14):
            ratio = index / 14
            y = horizon + int(floor_h * ratio * ratio)
            pygame.draw.line(self.screen, (22, 24, 22), (view.x, y), (view.right, y), 3)
            pygame.draw.line(self.screen, (83, 76, 63), (view.x, y + 2), (view.right, y + 2), 1)

        # A warm central glow makes nearby stonework easier to read.
        glow = pygame.Surface((view.width, view.height), pygame.SRCALPHA)
        for radius, alpha in ((250, 10), (170, 12), (90, 15)):
            pygame.draw.circle(glow, (255, 184, 77, alpha),
                               (view.width // 2, view.height // 2), radius)
        self.screen.blit(glow, view.topleft)

    def draw_minimap(self, rect):
        pygame.draw.rect(self.screen, NAVY, rect)
        margin = 12
        cell = min((rect.width - margin * 2) / self.maze.cols,
                   (rect.height - margin * 2) / self.maze.rows)
        ox = rect.x + (rect.width - cell * self.maze.cols) / 2
        oy = rect.y + (rect.height - cell * self.maze.rows) / 2
        for y in range(self.maze.rows):
            for x in range(self.maze.cols):
                left, top = ox + x * cell, oy + y * cell
                walls = self.maze.walls[y][x]
                if walls[0]: pygame.draw.line(self.screen, GREEN, (left, top), (left + cell, top), 1)
                if walls[1]: pygame.draw.line(self.screen, GREEN, (left + cell, top), (left + cell, top + cell), 1)
                if walls[2]: pygame.draw.line(self.screen, GREEN, (left, top + cell), (left + cell, top + cell), 1)
                if walls[3]: pygame.draw.line(self.screen, GREEN, (left, top), (left, top + cell), 1)
        if self.solution_visible:
            points = [(ox + (x + .5) * cell, oy + (y + .5) * cell)
                      for x, y in self.maze.path(self.player, self.maze.end)]
            if len(points) > 1:
                pygame.draw.lines(self.screen, RED, False, points, 2)
        ex, ey = self.maze.end
        pygame.draw.circle(self.screen, YELLOW, (int(ox + (ex + .5) * cell), int(oy + (ey + .5) * cell)), max(2, int(cell / 3)))
        px, py = self.player
        cx, cy = ox + (px + .5) * cell, oy + (py + .5) * cell
        pygame.draw.circle(self.screen, BLUE, (int(cx), int(cy)), max(3, int(cell / 3)))
        angles = (-math.pi / 2, 0, math.pi / 2, math.pi)
        angle = angles[self.facing]
        pygame.draw.line(self.screen, WHITE, (cx, cy), (cx + math.cos(angle) * cell, cy + math.sin(angle) * cell), 2)

    def draw_play_3d(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, NAVY, (0, 0, WIDTH, TOP_BAR))
        level_name = LEVELS[self.level_key][0]
        auto_status = f"   AUTO ×{self.solution_speed} (SPAZIO cambia)" if self.solution_auto else ""
        self.draw_text(f"LABIRINTO 3D   {level_name}   PASSI: {self.steps}{auto_status}",
                       self.small_font if self.solution_auto else self.font,
                       GREEN, (WIDTH // 2, 38))

        view = pygame.Rect(245, TOP_BAR, WIDTH - 245, HEIGHT - TOP_BAR - BOTTOM_BAR)
        horizon = view.y + view.height // 2
        self.draw_dungeon_background(view, horizon)

        grid = self.occupancy_grid()
        player_x = self.player[0] * 2 + 1.5
        player_y = self.player[1] * 2 + 1.5
        base_angles = (-math.pi / 2, 0, math.pi / 2, math.pi)
        base_angle = base_angles[self.facing]
        fov = math.radians(60)
        ray_width = 3
        rays = view.width // ray_width + 1
        for column in range(rays):
            offset = (column / max(1, rays - 1) - .5) * fov
            distance, hit_x, hit_y, grid_x, grid_y = self.cast_ray(
                grid, player_x, player_y, base_angle + offset)
            corrected = max(.12, distance * math.cos(offset))
            wall_height = min(view.height * 1.35, view.height * 1.25 / corrected)
            x = view.x + column * ray_width
            # Select the texture coordinate from the side of the block hit.
            frac_x, frac_y = hit_x % 1.0, hit_y % 1.0
            if min(frac_x, 1 - frac_x) < min(frac_y, 1 - frac_y):
                texture = self.wall_textures[(grid_x * 11 + (grid_y // 4) * 7) % 4]
                texture_x = int(frac_y * texture.get_width())
                side_shadow = .82
            else:
                texture = self.wall_textures[(grid_y * 13 + (grid_x // 4) * 5) % 4]
                texture_x = int(frac_x * texture.get_width())
                side_shadow = 1.0
            texture_x = max(0, min(texture.get_width() - 1, texture_x))
            strip = texture.subsurface((texture_x, 0, 1, texture.get_height()))
            scaled = pygame.transform.scale(strip, (ray_width + 1, max(1, int(wall_height))))
            light = max(42, min(255, int(280 / (1 + corrected * .11) * side_shadow)))
            scaled.fill((light, light, max(28, int(light * .91))), special_flags=pygame.BLEND_RGB_MULT)
            self.screen.blit(scaled, (x, int(horizon - wall_height / 2)))

        self.draw_side_passage_cues(view)
        self.draw_goal_diamond(view, grid, player_x, player_y, base_angle, fov)

        self.draw_text("MAPPA", self.small_font, WHITE, (122, 94))
        self.draw_minimap(pygame.Rect(8, 108, 229, view.height - 38))
        pygame.draw.rect(self.screen, NAVY, (0, HEIGHT - BOTTOM_BAR, WIDTH, BOTTOM_BAR))
        self.draw_controls()

        if self.won:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 165))
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, NAVY, (210, 215, 540, 280), border_radius=18)
            pygame.draw.rect(self.screen, YELLOW, (210, 215, 540, 280), 3, border_radius=18)
            self.draw_text("BRAVO!", self.title_font, YELLOW, (WIDTH // 2, 260))
            self.draw_text(f"Passi effettuati: {self.steps}", self.font, WHITE, (WIDTH // 2, 315))
            self.draw_text(f"Minimo necessario: {self.optimal_steps}", self.font, GREEN, (WIDTH // 2, 355))
            extra = self.steps - self.optimal_steps
            result = "PERCORSO PERFETTO!" if extra == 0 else f"Passi in più: {extra}"
            self.draw_text(result, self.font, YELLOW if extra == 0 else RED, (WIDTH // 2, 400))
            self.draw_text("Premi INVIO o tocca NUOVO", self.small_font, GRAY, (WIDTH // 2, 455))

    def handle_click(self, position):
        for key, rect in self.buttons.items():
            if rect.collidepoint(position):
                if key.startswith("level_"):
                    self.new_game(key[-1])
                elif key == "toggle_3d":
                    self.mode_3d = not self.mode_3d
                elif key == "up":
                    self.solution_auto = False
                    self.move_3d(True) if self.mode_3d else self.move(0)
                elif key == "right":
                    self.solution_auto = False
                    self.turn_3d(True) if self.mode_3d else self.move(1)
                elif key == "down":
                    self.solution_auto = False
                    self.move_3d(False) if self.mode_3d else self.move(2)
                elif key == "left":
                    self.solution_auto = False
                    self.turn_3d(False) if self.mode_3d else self.move(3)
                elif key == "solution":
                    if self.mode_3d:
                        self.start_auto_solution()
                    else:
                        self.solution_visible = not self.solution_visible
                elif key == "new":
                    self.new_game()
                elif key == "menu":
                    self.state = "menu"
                return

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_click(event.pos)
        if event.type == pygame.KEYDOWN:
            if self.state == "menu" and event.unicode in LEVELS:
                self.new_game(event.unicode)
            elif self.state == "play":
                if self.mode_3d:
                    if event.key == pygame.K_SPACE and self.solution_auto:
                        self.solution_speed = self.solution_speed % 3 + 1
                        self.last_auto_tick = pygame.time.get_ticks()
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.solution_auto = False
                        self.move_3d(True)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.solution_auto = False
                        self.move_3d(False)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.solution_auto = False
                        self.turn_3d(False)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.solution_auto = False
                        self.turn_3d(True)
                    elif event.key in (pygame.K_F1, pygame.K_h):
                        self.start_auto_solution()
                    elif event.key in (pygame.K_RETURN, pygame.K_n):
                        self.new_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                    return True
                key_to_direction = {
                    pygame.K_UP: 0,
                    pygame.K_RIGHT: 1,
                    pygame.K_DOWN: 2,
                    pygame.K_LEFT: 3,
                    pygame.K_w: 0,
                    pygame.K_d: 1,
                    pygame.K_s: 2,
                    pygame.K_a: 3,
                }
                if event.key in key_to_direction:
                    self.move(key_to_direction[event.key])
                elif event.key in (pygame.K_F1, pygame.K_h):
                    self.solution_visible = not self.solution_visible
                elif event.key in (pygame.K_RETURN, pygame.K_n):
                    self.new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
        return True

    async def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                running = self.handle_event(event)
            self.update_auto_solution()
            if self.state == "menu":
                self.draw_menu()
            else:
                self.draw_play()
            pygame.display.flip()
            self.clock.tick(FPS)
            await asyncio.sleep(0)
        pygame.quit()


async def main():
    await Game().run()


if __name__ == "__main__":
    asyncio.run(main())
