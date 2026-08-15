#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <time.h>
#include "../maze_core.h"

static Maze maze;
static int state_menu = 1, player_x, player_y, steps, minimum_steps;
static int show_solution = 0, level = 1;
static const int level_cols[4] = {15, 23, 31, 39};
static const int level_rows[4] = {9, 13, 17, 21};

static void new_game(HWND hwnd, int selected) {
    level = selected;
    maze_generate(&maze, level_cols[level - 1], level_rows[level - 1]);
    maze_choose_farthest_end(&maze);
    player_x = maze.start_x; player_y = maze.start_y;
    steps = 0; show_solution = 0; state_menu = 0;
    minimum_steps = maze_shortest_path(&maze, maze.start_x, maze.start_y,
                                       maze.end_x, maze.end_y, 0, 0);
    InvalidateRect(hwnd, 0, TRUE);
}

static void finish(HWND hwnd) {
    char message[256];
    int extra = steps - minimum_steps;
    sprintf(message, "Hai completato il labirinto!\n\nPassi effettuati: %d\n"
            "Minimo necessario: %d\nPassi in piu': %d", steps, minimum_steps, extra);
    MessageBoxA(hwnd, message, "Bravo!", MB_OK | MB_ICONINFORMATION);
    state_menu = 1;
    InvalidateRect(hwnd, 0, TRUE);
}

static void move_player(HWND hwnd, int direction) {
    if (maze_can_move(&maze, player_x, player_y, direction)) {
        player_x += maze_dx[direction]; player_y += maze_dy[direction]; ++steps;
        if (player_x == maze.end_x && player_y == maze.end_y) finish(hwnd);
        else InvalidateRect(hwnd, 0, TRUE);
    }
}

static void draw_centered(HDC dc, RECT rect, const char *text, int y) {
    RECT line = rect; line.top = y; line.bottom = y + 40;
    DrawTextA(dc, text, -1, &line, DT_CENTER | DT_SINGLELINE | DT_VCENTER);
}

static void paint_menu(HDC dc, RECT rect) {
    HFONT title = CreateFontA(42, 0, 0, 0, FW_BOLD, 0, 0, 0, ANSI_CHARSET,
                              0, 0, CLEARTYPE_QUALITY, FF_MODERN, "Consolas");
    HFONT normal = CreateFontA(25, 0, 0, 0, FW_NORMAL, 0, 0, 0, ANSI_CHARSET,
                               0, 0, CLEARTYPE_QUALITY, FF_MODERN, "Consolas");
    SetBkMode(dc, TRANSPARENT); SetTextColor(dc, RGB(255, 220, 70));
    SelectObject(dc, title); draw_centered(dc, rect, "LABIRINTO", 70);
    SelectObject(dc, normal); SetTextColor(dc, RGB(225, 240, 255));
    draw_centered(dc, rect, "Scegli il livello di difficolta'", 150);
    draw_centered(dc, rect, "1. FACILE", 220);
    draw_centered(dc, rect, "2. MEDIO", 270);
    draw_centered(dc, rect, "3. DIFFICILE", 320);
    draw_centered(dc, rect, "4. DIFFICILISSIMO", 370);
    SetTextColor(dc, RGB(130, 160, 180));
    draw_centered(dc, rect, "Frecce: movimento  |  F1: soluzione  |  Esc: menu", 460);
    DeleteObject(title); DeleteObject(normal);
}

static void paint_game(HDC dc, RECT rect) {
    int x, y, cell, ox, oy, maze_w, maze_h, px, py;
    int path[MAX_CELLS], path_len, cx, cy, i;
    char status[160];
    HPEN wall_pen = CreatePen(PS_SOLID, 2, RGB(45, 220, 145));
    HPEN solution_pen = CreatePen(PS_SOLID, 4, RGB(240, 65, 65));
    HBRUSH player_brush = CreateSolidBrush(RGB(50, 125, 240));
    HBRUSH end_brush = CreateSolidBrush(RGB(255, 220, 60));
    HFONT font = CreateFontA(19, 0, 0, 0, FW_BOLD, 0, 0, 0, ANSI_CHARSET,
                             0, 0, CLEARTYPE_QUALITY, FF_MODERN, "Consolas");
    cell = (rect.right - 50) / maze.cols;
    if (cell > (rect.bottom - 130) / maze.rows) cell = (rect.bottom - 130) / maze.rows;
    maze_w = cell * maze.cols; maze_h = cell * maze.rows;
    ox = (rect.right - maze_w) / 2; oy = 70 + (rect.bottom - 120 - maze_h) / 2;
    SetBkMode(dc, TRANSPARENT); SelectObject(dc, font); SetTextColor(dc, RGB(220, 240, 255));
    sprintf(status, "Livello %d   Passi: %d   Minimo: %d", level, steps, minimum_steps);
    draw_centered(dc, rect, status, 15);

    if (show_solution) {
        path_len = maze_shortest_path(&maze, player_x, player_y, maze.end_x, maze.end_y,
                                      path, MAX_CELLS);
        SelectObject(dc, solution_pen); cx = player_x; cy = player_y;
        MoveToEx(dc, ox + cx * cell + cell / 2, oy + cy * cell + cell / 2, 0);
        for (i = 0; i < path_len; ++i) {
            cx += maze_dx[path[i]]; cy += maze_dy[path[i]];
            LineTo(dc, ox + cx * cell + cell / 2, oy + cy * cell + cell / 2);
        }
    }
    SelectObject(dc, wall_pen);
    for (y = 0; y < maze.rows; ++y) for (x = 0; x < maze.cols; ++x) {
        int l = ox + x * cell, t = oy + y * cell;
        if (maze.walls[y][x] & WALL_UP) { MoveToEx(dc, l, t, 0); LineTo(dc, l + cell, t); }
        if (maze.walls[y][x] & WALL_RIGHT) { MoveToEx(dc, l + cell, t, 0); LineTo(dc, l + cell, t + cell); }
        if (maze.walls[y][x] & WALL_DOWN) { MoveToEx(dc, l, t + cell, 0); LineTo(dc, l + cell, t + cell); }
        if (maze.walls[y][x] & WALL_LEFT) { MoveToEx(dc, l, t, 0); LineTo(dc, l, t + cell); }
    }
    px = ox + maze.end_x * cell + cell / 2; py = oy + maze.end_y * cell + cell / 2;
    SelectObject(dc, end_brush); Ellipse(dc, px - cell / 4, py - cell / 4, px + cell / 4, py + cell / 4);
    px = ox + player_x * cell + cell / 2; py = oy + player_y * cell + cell / 2;
    SelectObject(dc, player_brush); Ellipse(dc, px - cell / 3, py - cell / 3, px + cell / 3, py + cell / 3);
    DeleteObject(wall_pen); DeleteObject(solution_pen); DeleteObject(player_brush);
    DeleteObject(end_brush); DeleteObject(font);
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    PAINTSTRUCT ps; HDC dc; RECT rect;
    switch (msg) {
    case WM_KEYDOWN:
        if (state_menu && wp >= '1' && wp <= '4') new_game(hwnd, (int)(wp - '0'));
        else if (!state_menu) {
            if (wp == VK_UP) move_player(hwnd, 0);
            else if (wp == VK_RIGHT) move_player(hwnd, 1);
            else if (wp == VK_DOWN) move_player(hwnd, 2);
            else if (wp == VK_LEFT) move_player(hwnd, 3);
            else if (wp == VK_F1) { show_solution = !show_solution; InvalidateRect(hwnd, 0, TRUE); }
            else if (wp == VK_ESCAPE) { state_menu = 1; InvalidateRect(hwnd, 0, TRUE); }
        }
        return 0;
    case WM_PAINT:
        dc = BeginPaint(hwnd, &ps); GetClientRect(hwnd, &rect);
        FillRect(dc, &rect, (HBRUSH)GetStockObject(BLACK_BRUSH));
        if (state_menu) paint_menu(dc, rect); else paint_game(dc, rect);
        EndPaint(hwnd, &ps); return 0;
    case WM_DESTROY: PostQuitMessage(0); return 0;
    }
    return DefWindowProc(hwnd, msg, wp, lp);
}

int WINAPI WinMain(HINSTANCE instance, HINSTANCE previous, LPSTR cmd, int show) {
    WNDCLASSA wc; HWND hwnd; MSG msg;
    (void)previous; (void)cmd; srand((unsigned int)time(0));
    ZeroMemory(&wc, sizeof(wc)); wc.lpfnWndProc = window_proc; wc.hInstance = instance;
    wc.lpszClassName = "LabirintoCWindow"; wc.hCursor = LoadCursor(0, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)GetStockObject(BLACK_BRUSH);
    if (!RegisterClassA(&wc)) return 1;
    hwnd = CreateWindowA(wc.lpszClassName, "Labirinto C - Endrigi Software",
                         WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
                         1000, 760, 0, 0, instance, 0);
    if (!hwnd) return 1;
    ShowWindow(hwnd, show); UpdateWindow(hwnd);
    while (GetMessage(&msg, 0, 0, 0) > 0) { TranslateMessage(&msg); DispatchMessage(&msg); }
    return (int)msg.wParam;
}
