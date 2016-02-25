from .maze import genmaze_eller
from random import random
from .cellgen import make_cell, make_random_exits

from common.const import Direction, WorldSize, NaturalMap


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
                sds.append(Direction.east)
            if not bottom:
                sds.append(Direction.south)

            exits.extend(make_random_exits(only_sides=tuple(sds)))

            right_exit = [(Direction.west, a, b) for side, a, b in exits if side == Direction.east]
            bottom_exits[x] = [(Direction.north, a, b) for side, a, b in exits if side == Direction.south]

            cells[(x, y)] = make_cell(exits=exits)
        print('{}%'.format(y * 100 // height))
    return cells


def setup_sources(cells):
    for cell in cells.values():
        x


def render_generated_world(cells, width, height):
    from PIL import Image, ImageDraw

    out = Image.new('RGB', (WorldSize.cell * width, WorldSize.cell * height))
    draw = ImageDraw.Draw(out)
    draw.rectangle((
        0, 0,
        WorldSize.cell * width, WorldSize.cell * height,
    ), fill=(255, 255, 255))

    for y in range(height):
        draw.line((0, y * WorldSize.cell, width * WorldSize.cell, y * WorldSize.cell), fill=(200, 255, 200))
    for x in range(width):
        draw.line((x * WorldSize.cell, 0, x * WorldSize.cell, height * WorldSize.cell), fill=(200, 255, 200))

    for y in range(height):
        for x in range(width):
            cell = cells[(x, y)]
            for cy in range(WorldSize.cell):
                for cx in range(WorldSize.cell):
                    if cell[cx, cy] != NaturalMap.natural_wall:
                        continue
                    out.putpixel((
                        x * WorldSize.cell + cx,
                        y * WorldSize.cell + cy,
                    ), (0, 0, 0))

    out.show()


if __name__ == '__main__':
    width, height = 16, 16
    cells = make_full_world(width, height)
    render_generated_world(cells, width, height)
