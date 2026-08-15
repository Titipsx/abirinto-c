#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "../maze_core.h"

static Maze maze;
static int px, py, steps, minimum_steps;

static void mode_80x50(void) {
    union REGS r;
    r.x.ax = 0x0003; int86(0x10, &r, &r);
    r.x.ax = 0x1112; r.h.bl = 0; int86(0x10, &r, &r);
}

static void put_at(int x, int y, int color, int ch) {
    gotoxy(x + 1, y + 1); textcolor(color); putch(ch);
}

static void draw_maze(int solution) {
    int x, y, sx, sy, i, n, path[MAX_CELLS];
    clrscr();
    textcolor(LIGHTGREEN); gotoxy(1, 1);
    cprintf("* INIZIO  @ FINE  Passi:%d  Minimo:%d  F1 soluzione  F10 uscita", steps, minimum_steps);
    for (y = 0; y < maze.rows; ++y) for (x = 0; x < maze.cols; ++x) {
        sx = x * 2; sy = y * 2 + 2;
        if (maze.walls[y][x] & WALL_UP) { put_at(sx, sy, GREEN, 219); put_at(sx + 1, sy, GREEN, 219); }
        if (maze.walls[y][x] & WALL_LEFT) put_at(sx, sy + 1, GREEN, 219);
        put_at(sx + 2, sy, GREEN, 219); put_at(sx + 2, sy + 1, GREEN, 219);
        put_at(sx, sy + 2, GREEN, 219); put_at(sx + 1, sy + 2, GREEN, 219); put_at(sx + 2, sy + 2, GREEN, 219);
        if (!(maze.walls[y][x] & WALL_RIGHT)) put_at(sx + 2, sy + 1, BLACK, ' ');
        if (!(maze.walls[y][x] & WALL_DOWN)) put_at(sx + 1, sy + 2, BLACK, ' ');
    }
    if (solution) {
        x = px; y = py;
        n = maze_shortest_path(&maze, px, py, maze.end_x, maze.end_y, path, MAX_CELLS);
        for (i = 0; i < n; ++i) {
            put_at(x * 2 + 1, y * 2 + 3, LIGHTRED, '.');
            x += maze_dx[path[i]]; y += maze_dy[path[i]];
        }
    }
    put_at(maze.start_x * 2 + 1, maze.start_y * 2 + 3, RED, '*');
    put_at(maze.end_x * 2 + 1, maze.end_y * 2 + 3, YELLOW, '@');
    put_at(px * 2 + 1, py * 2 + 3, LIGHTCYAN, '*');
}

static int choose_level(void) {
    int c;
    clrscr(); textcolor(YELLOW); gotoxy(28, 5); cprintf("LABIRINTO");
    textcolor(WHITE); gotoxy(20, 9); cprintf("Scegli il livello:");
    gotoxy(24, 12); cprintf("1. FACILE"); gotoxy(24, 14); cprintf("2. MEDIO");
    gotoxy(24, 16); cprintf("3. DIFFICILE"); gotoxy(24, 18); cprintf("4. DIFFICILISSIMO");
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
                else if (key == 68) { textmode(C80); clrscr(); return 0; }
                if (direction >= 0 && maze_can_move(&maze, px, py, direction)) {
                    px += maze_dx[direction]; py += maze_dy[direction]; ++steps; draw_maze(solution);
                    if (px == maze.end_x && py == maze.end_y) break;
                }
            } else if (key == 27) break;
        }
        if (px == maze.end_x && py == maze.end_y) {
            gotoxy(1, 49); textcolor(YELLOW);
            cprintf("BRAVO! Passi:%d  Minimo:%d  In piu':%d. Premi un tasto.",
                    steps, minimum_steps, steps - minimum_steps); getch();
        }
    }
}
