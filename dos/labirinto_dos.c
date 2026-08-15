#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "../maze_core.h"

static Maze maze;
static int px, py, steps, minimum_steps;

#define C_BLACK       0
#define C_GREEN       2
#define C_RED         4
#define C_YELLOW      6
#define C_WHITE       7
#define C_LIGHTRED   12
#define C_LIGHTGREEN 10
#define C_LIGHTCYAN  11

static void mode_80x50(void) {
    union REGS r;
    r.x.ax = 0x0003; int86(0x10, &r, &r);
    r.x.ax = 0x1112; r.h.bl = 0; int86(0x10, &r, &r);
}

static void mode_80x25(void) {
    union REGS r;
    r.x.ax = 0x0003; int86(0x10, &r, &r);
}

static void put_at(int x, int y, int color, int ch) {
    unsigned short __far *video = (unsigned short __far *)MK_FP(0xB800, 0);
    if (x >= 0 && x < 80 && y >= 0 && y < 50)
        video[y * 80 + x] = (unsigned short)(((color & 15) << 8) | (ch & 255));
}

static void clear_screen(void) {
    int x, y;
    for (y = 0; y < 50; ++y)
        for (x = 0; x < 80; ++x) put_at(x, y, C_BLACK, ' ');
}

static void text_at(int x, int y, int color, const char *text) {
    while (*text && x < 80) put_at(x++, y, color, *text++);
}

static void draw_maze(int solution) {
    int x, y, sx, sy, i, n, path[MAX_CELLS];
    char status[80];
    clear_screen();
    sprintf(status, "* INIZIO  @ FINE  Passi:%d  Minimo:%d  F1 soluzione  F10 uscita",
            steps, minimum_steps);
    text_at(0, 0, C_LIGHTGREEN, status);
    for (y = 0; y < maze.rows; ++y) for (x = 0; x < maze.cols; ++x) {
        sx = x * 2; sy = y * 2 + 2;
        if (maze.walls[y][x] & WALL_UP) { put_at(sx, sy, C_GREEN, 219); put_at(sx + 1, sy, C_GREEN, 219); }
        if (maze.walls[y][x] & WALL_LEFT) put_at(sx, sy + 1, C_GREEN, 219);
        put_at(sx + 2, sy, C_GREEN, 219); put_at(sx + 2, sy + 1, C_GREEN, 219);
        put_at(sx, sy + 2, C_GREEN, 219); put_at(sx + 1, sy + 2, C_GREEN, 219); put_at(sx + 2, sy + 2, C_GREEN, 219);
        if (!(maze.walls[y][x] & WALL_RIGHT)) put_at(sx + 2, sy + 1, C_BLACK, ' ');
        if (!(maze.walls[y][x] & WALL_DOWN)) put_at(sx + 1, sy + 2, C_BLACK, ' ');
    }
    if (solution) {
        x = px; y = py;
        n = maze_shortest_path(&maze, px, py, maze.end_x, maze.end_y, path, MAX_CELLS);
        for (i = 0; i < n; ++i) {
            put_at(x * 2 + 1, y * 2 + 3, C_LIGHTRED, '.');
            x += maze_dx[path[i]]; y += maze_dy[path[i]];
        }
    }
    put_at(maze.start_x * 2 + 1, maze.start_y * 2 + 3, C_RED, '*');
    put_at(maze.end_x * 2 + 1, maze.end_y * 2 + 3, C_YELLOW, '@');
    put_at(px * 2 + 1, py * 2 + 3, C_LIGHTCYAN, '*');
}

static int choose_level(void) {
    int c;
    clear_screen(); text_at(28, 4, C_YELLOW, "LABIRINTO");
    text_at(20, 8, C_WHITE, "Scegli il livello:");
    text_at(24, 11, C_WHITE, "1. FACILE"); text_at(24, 13, C_WHITE, "2. MEDIO");
    text_at(24, 15, C_WHITE, "3. DIFFICILE"); text_at(24, 17, C_WHITE, "4. DIFFICILISSIMO");
    do c = getch(); while (c < '1' || c > '4');
    return c - '0';
}

int main(void) {
    int level, key, direction, solution;
    int cols[4] = {15, 23, 31, 39}, rows[4] = {9, 13, 17, 21};
    srand((unsigned int)time(0)); mode_80x50();
    for (;;) {
        level = choose_level(); maze_generate(&maze, cols[level - 1], rows[level - 1]);
        maze_choose_farthest_end(&maze); px = maze.start_x; py = maze.start_y; steps = 0; solution = 0;
        minimum_steps = maze_shortest_path(&maze, px, py, maze.end_x, maze.end_y, 0, 0);
        draw_maze(solution);
        for (;;) {
            key = getch();
            if (key == 0 || key == 224) {
                key = getch(); direction = -1;
                if (key == 72) direction = 0; else if (key == 77) direction = 1;
                else if (key == 80) direction = 2; else if (key == 75) direction = 3;
                else if (key == 59) { solution = !solution; draw_maze(solution); }
                else if (key == 68) { mode_80x25(); return 0; }
                if (direction >= 0 && maze_can_move(&maze, px, py, direction)) {
                    px += maze_dx[direction]; py += maze_dy[direction]; ++steps; draw_maze(solution);
                    if (px == maze.end_x && py == maze.end_y) break;
                }
            } else if (key == 27) break;
        }
        if (px == maze.end_x && py == maze.end_y) {
            char result[80];
            sprintf(result, "BRAVO! Passi:%d  Minimo:%d  In piu':%d. Premi un tasto.",
                    steps, minimum_steps, steps - minimum_steps);
            text_at(0, 48, C_YELLOW, result); getch();
        }
    }
}
