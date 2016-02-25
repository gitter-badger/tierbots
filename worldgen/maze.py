from random import randint
import numpy


def fill_unassigned(row):
    '''
    >>> a = numpy.array([1, 0, 5, 5, 0, 2])
    >>> fill_unassigned(a)
    >>> a
    array([1, 3, 5, 5, 4, 2])
    '''
    usednums, c = set(row), 1
    for i, x in enumerate(row):
        if x != 0:
            continue
        while c in usednums:
            c += 1
        row[i] = c
        usednums.add(c)


def join_sets(row, a, b):
    '''
    >>> a = numpy.array([1, 1, 2, 2, 3, 2])
    >>> join_sets(a, 1, 2)
    >>> a
    array([1, 1, 1, 1, 3, 1])
    '''
    row[numpy.where(row == b)[0]] = a


def make_bottom_walls(row):
    sets = {}
    for x in row:
        sets[x] = sets.get(x, 0) + 1
    guarded = {k: randint(0, v - 1) for k, v in sets.items()}
    bwalls = numpy.zeros(row.shape, dtype='bool')
    for i, x in enumerate(row):
        sets[x] -= 1
        if guarded[x] == sets[x]:
            continue
        if randint(0, 1):
            bwalls[i] = True
    return bwalls


def genmaze_eller(cellcount, heightcount):
    #     0   1
    # +xxx+xxx+xxx+
    # x   |   |   x
    # +---+---+---+  0
    # x   |   |   x
    # +xxx+xxx+xxx+

    all_right_walls = numpy.zeros((cellcount - 1, heightcount), dtype=numpy.bool_)
    all_bottom_walls = numpy.zeros((cellcount, heightcount - 1), dtype=numpy.bool_)

    row = numpy.arange(1, cellcount + 1, dtype=numpy.int16)
    rwalls = numpy.zeros((cellcount - 1,), dtype=numpy.bool_)
    rwalls_req = numpy.zeros(rwalls.shape, dtype=numpy.bool_)
    for y in range(heightcount):
        fill_unassigned(row)
        rwalls[:] = False
        rwalls_req[:] = False
        for x in range(cellcount - 1):
            if row[x] == row[x + 1]:
                rwalls_req[x] = True
                continue
            if randint(0, 1):
                rwalls[x] = True
            else:
                join_sets(row, row[x], row[x + 1])

        if y == heightcount - 1:  # last row condition
            break
        all_right_walls[:, y] = rwalls_req | rwalls

        bwalls = make_bottom_walls(row)
        all_bottom_walls[:, y] = bwalls
        row[bwalls] = 0

    # walls in last row
    for x in range(cellcount - 1):
        if row[x + 1] != row[x]:
            rwalls[x] = False
            join_sets(row, row[x], row[x + 1])
    all_right_walls[:, heightcount - 1] = rwalls | rwalls_req

    return {
        'width': cellcount,
        'height': heightcount,
        'rwalls': all_right_walls,
        'bwalls': all_bottom_walls,
    }


def debug_draw_maze(maze):
    from PIL import Image, ImageDraw

    WorldSize.cell = 20
    w, h = maze['width'], maze['height']
    img = Image.new('RGB', (w * WorldSize.cell, h * WorldSize.cell))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, w * WorldSize.cell - 1, h * WorldSize.cell - 1), fill=(0, 0, 0))
    for y in range(h):
        for x in range(w - 1):
            if maze['rwalls'][x, y]:
                draw.line((
                    x * WorldSize.cell + WorldSize.cell, y * WorldSize.cell,
                    x * WorldSize.cell + WorldSize.cell, y * WorldSize.cell + WorldSize.cell
                ), fill=(255, 255, 255))
    for y in range(h - 1):
        for x in range(w):
            if maze['bwalls'][x, y]:
                draw.line((
                    x * WorldSize.cell, y * WorldSize.cell + WorldSize.cell,
                    x * WorldSize.cell + WorldSize.cell, y * WorldSize.cell + WorldSize.cell
                ), fill=(255, 255, 255))
    img.show()


if __name__ == '__main__':
    maze = genmaze_eller(30, 30)
    debug_draw_maze(maze)
