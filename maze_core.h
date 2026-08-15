#ifndef MAZE_CORE_H
#define MAZE_CORE_H

#include <stdlib.h>

#define MAX_COLS 39
#define MAX_ROWS 21
#define MAX_CELLS (MAX_COLS * MAX_ROWS)

#define WALL_UP    1
#define WALL_RIGHT 2
#define WALL_DOWN  4
#define WALL_LEFT  8

typedef struct {
    int cols, rows;
    unsigned char walls[MAX_ROWS][MAX_COLS];
    int start_x, start_y, end_x, end_y;
} Maze;

static int maze_dx[4] = {0, 1, 0, -1};
static int maze_dy[4] = {-1, 0, 1, 0};
static int maze_bit[4] = {WALL_UP, WALL_RIGHT, WALL_DOWN, WALL_LEFT};
static int maze_opposite[4] = {2, 3, 0, 1};

static int maze_inside(Maze *m, int x, int y) {
    return x >= 0 && x < m->cols && y >= 0 && y < m->rows;
}

static int maze_can_move(Maze *m, int x, int y, int direction) {
    return maze_inside(m, x, y) && !(m->walls[y][x] & maze_bit[direction]);
}

static void maze_generate(Maze *m, int cols, int rows) {
    static int visited[MAX_ROWS][MAX_COLS];
    static int stack_x[MAX_CELLS], stack_y[MAX_CELLS];
    int x, y, nx, ny, top, i, count, direction, choices[4];

    m->cols = cols;
    m->rows = rows;
    for (y = 0; y < rows; ++y) {
        for (x = 0; x < cols; ++x) {
            m->walls[y][x] = WALL_UP | WALL_RIGHT | WALL_DOWN | WALL_LEFT;
            visited[y][x] = 0;
        }
    }

    m->start_x = rand() % cols;
    m->start_y = rand() % rows;
    top = 0;
    stack_x[0] = m->start_x;
    stack_y[0] = m->start_y;
    visited[m->start_y][m->start_x] = 1;

    while (top >= 0) {
        x = stack_x[top];
        y = stack_y[top];
        count = 0;
        for (i = 0; i < 4; ++i) {
            nx = x + maze_dx[i];
            ny = y + maze_dy[i];
            if (maze_inside(m, nx, ny) && !visited[ny][nx]) choices[count++] = i;
        }
        if (!count) {
            --top;
            continue;
        }
        direction = choices[rand() % count];
        nx = x + maze_dx[direction];
        ny = y + maze_dy[direction];
        m->walls[y][x] &= (unsigned char)~maze_bit[direction];
        m->walls[ny][nx] &= (unsigned char)~maze_bit[maze_opposite[direction]];
        visited[ny][nx] = 1;
        ++top;
        stack_x[top] = nx;
        stack_y[top] = ny;
    }
}

/* BFS: restituisce la lunghezza minima; path_dir può essere NULL. */
static int maze_shortest_path(Maze *m, int sx, int sy, int ex, int ey,
                              int *path_dir, int max_path) {
    static int qx[MAX_CELLS], qy[MAX_CELLS];
    static int previous[MAX_ROWS][MAX_COLS];
    static int distance[MAX_ROWS][MAX_COLS];
    static int reverse[MAX_CELLS];
    int head = 0, tail = 0, x, y, nx, ny, d, p, length = 0, i;

    for (y = 0; y < m->rows; ++y)
        for (x = 0; x < m->cols; ++x) {
            previous[y][x] = -2;
            distance[y][x] = -1;
        }
    qx[tail] = sx; qy[tail++] = sy;
    previous[sy][sx] = -1;
    distance[sy][sx] = 0;
    while (head < tail) {
        x = qx[head]; y = qy[head++];
        if (x == ex && y == ey) break;
        for (d = 0; d < 4; ++d) if (maze_can_move(m, x, y, d)) {
            nx = x + maze_dx[d]; ny = y + maze_dy[d];
            if (previous[ny][nx] == -2) {
                previous[ny][nx] = maze_opposite[d];
                distance[ny][nx] = distance[y][x] + 1;
                qx[tail] = nx; qy[tail++] = ny;
            }
        }
    }
    if (distance[ey][ex] < 0) return -1;
    x = ex; y = ey;
    while (!(x == sx && y == sy) && length < MAX_CELLS) {
        p = previous[y][x];
        reverse[length++] = maze_opposite[p];
        x += maze_dx[p]; y += maze_dy[p];
    }
    if (path_dir && length <= max_path)
        for (i = 0; i < length; ++i) path_dir[i] = reverse[length - 1 - i];
    return length;
}

static void maze_choose_farthest_end(Maze *m) {
    int x, y, distance, best = -1;
    m->end_x = m->start_x; m->end_y = m->start_y;
    for (y = 0; y < m->rows; ++y)
        for (x = 0; x < m->cols; ++x) {
            distance = maze_shortest_path(m, m->start_x, m->start_y, x, y, 0, 0);
            if (distance > best) {
                best = distance; m->end_x = x; m->end_y = y;
            }
        }
}

#endif
