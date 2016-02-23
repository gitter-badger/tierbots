from .maze import genmaze_eller
from random import random
from .cellgen import make_cell, make_random_exits
from .const import *


def raze_maze_walls(maze, prob=0.5):
    for y in range(maze['height']):
        for x in range(maze['width'] - 1):
            if maze['rwalls'][x, y] and random() < prob:
                maze['rwalls'][x, y] = False
    for y in range(maze['height'] - 1):
        for x in range(maze['width']):
            if maze['bwalls'][x, y] and random() < prob:
                maze['bwalls'][x, y] = False


def make_full_world(width, height):
    from PIL import Image, ImageDraw

    maze = genmaze_eller(width, height)
    raze_maze_walls(maze, 0.4)

    bottom_exits = {i: [] for i in range(width)}
    cells = {}
    for y in range(height):
        right_exit = []
        for x in range(width):
            right = maze['rwalls'][x, y] if x < width - 1 else True
            bottom = maze['bwalls'][x, y] if y < height - 1 else True

            exits = []
            exits.extend(right_exit)
            exits.extend(bottom_exits[x])

            sds = []
            if not right:
                sds.append(EAST)
            if not bottom:
                sds.append(SOUTH)

            exits.extend(make_random_exits(only_sides=tuple(sds)))

            right_exit = [(WEST, a, b) for side, a, b in exits if side == EAST]
            bottom_exits[x] = [(NORTH, a, b) for side, a, b in exits if side == SOUTH]

            cells[(x, y)] = make_cell(exits=exits)
        print('{}%'.format(y * 100 // height))

    out = Image.new('RGB', (CELL_SIZE * width, CELL_SIZE * height))
    draw = ImageDraw.Draw(out)
    draw.rectangle((
        0, 0,
        CELL_SIZE * width, CELL_SIZE * height,
    ), fill=(255, 255, 255))

    for y in range(height):
        draw.line((0, y * CELL_SIZE, width * CELL_SIZE, y * CELL_SIZE), fill=(200, 255, 200))
    for x in range(width):
        draw.line((x * CELL_SIZE, 0, x * CELL_SIZE, height * CELL_SIZE), fill=(200, 255, 200))

    for y in range(height):
        for x in range(width):
            cell = cells[(x, y)]
            for cy in range(CELL_SIZE):
                for cx in range(CELL_SIZE):
                    if not cell[cx, cy]:
                        continue
                    out.putpixel((
                        x * CELL_SIZE + cx,
                        y * CELL_SIZE + cy,
                    ), (0, 0, 0))

    out.show()
