from .maze import genmaze_eller
from random import random, sample, randrange
from .cellgen import make_cell, make_random_exits
import numpy

from common.const import Direction, WorldSize, NaturalMap, DTypes


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
    result = []
    ofs = WorldSize.source_min_border_offset
    for xy, cell in cells.items():
        cg = cell == NaturalMap.ground
        cg_comb = cg.copy()

        cg_comb[:-1, :] |= cg[1:, :]
        cg_comb[1:, :] |= cg[:-1, :]
        cg_comb[:, :-1] |= cg[:, 1:]
        cg_comb[:, 1:] |= cg[:, :-1]

        cg_comb[:-1, :-1] |= cg[1:, 1:]
        cg_comb[:-1, 1:] |= cg[1:, :-1]
        cg_comb[1:, :-1] |= cg[:-1, 1:]
        cg_comb[1:, 1:] |= cg[:-1, :-1]

        possible_places = (cell == NaturalMap.natural_wall) & cg_comb
        if ofs > 0:
            possible_places = possible_places[ofs:-ofs, ofs:-ofs]
        indices_x, indices_y = numpy.where(possible_places)

        scount = min(randrange(*WorldSize.sources_per_cell), len(indices_x))
        if scount <= 0:
            continue
        result.extend(map(
            lambda idx: (
                xy[0] * WorldSize.cell + indices_x[idx] + ofs,
                xy[1] * WorldSize.cell + indices_y[idx] + ofs,
            ),
            sample(range(len(indices_x)), scount)
        ))
    return result


def glue_parts_together(cells, cell_width, cell_height):
    output = numpy.empty((WorldSize.cell * cell_width, WorldSize.cell * cell_height), dtype=DTypes.worldmap)
    for xy, cell in cells.items():
        ox, oy = xy[0] * WorldSize.cell, xy[1] * WorldSize.cell
        output[ox:ox + WorldSize.cell, oy:oy + WorldSize.cell] = cell
    return output


def render_generated_world(cells, sources=[]):
    from PIL import Image, ImageDraw

    GROUND_COLOR = (80, 80, 80)
    GRID_COLOR = (255, 255, 255, 10)
    WALL_COLOR = (0, 0, 0)
    SOURCE_COLOR = (255, 255, 0)

    out = Image.new('RGBA', (cells.shape[0], cells.shape[1]))
    draw = ImageDraw.Draw(out)
    draw.rectangle((
        0, 0,
        cells.shape[0], cells.shape[1],
    ), fill=GROUND_COLOR)

    for y in range(cells.shape[1]):
        for x in range(cells.shape[0]):
            if cells[x, y] != NaturalMap.natural_wall:
                continue
            out.putpixel((x, y), WALL_COLOR)

    for x, y in sources:
        out.putpixel((x, y), SOURCE_COLOR)

    grid_layer = Image.new('RGBA', (cells.shape[0], cells.shape[1]))
    grid_draw = ImageDraw.Draw(grid_layer)
    for y in range(0, cells.shape[1], WorldSize.cell):
        grid_draw.line((0, y, cells.shape[0], y), fill=GRID_COLOR)
    for x in range(0, cells.shape[0], WorldSize.cell):
        grid_draw.line((x, 0, x, cells.shape[1]), fill=GRID_COLOR)

    return Image.alpha_composite(out, grid_layer)


def generate_world(cell_width, cell_height):
    cells = make_full_world(cell_width, cell_height)
    sources = setup_sources(cells)
    mp = glue_parts_together(cells, cell_width, cell_height)
    return mp, sources


if __name__ == '__main__':
    wmap, sources = generate_world(16, 16)
    im = render_generated_world(wmap, sources=sources)
    # im.show()
    im.save('map.png')
