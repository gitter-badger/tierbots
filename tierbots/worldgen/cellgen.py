import numpy
import random
from math import sqrt
import itertools

from ..const import Direction, WorldSize, NaturalMap, DTypes


def range_intersect(a1, b1, a2, b2):
    '''
    >>> range_intersect(0, 4, 1, 8)
    (1, 4)
    >>> range_intersect(0, 4, 7, 8)
    >>> range_intersect(1, 8, 0, 4)
    (1, 4)
    '''
    a = max(a1, a2)
    b = min(b1, b2)
    if a >= b:
        return None
    return (a, b)


def ensure_range(value, a, b):
    if value < a:
        return a
    if value >= b:
        return b - 1
    return value


def build_wall(cell):
    cell[:, 0] = NaturalMap.natural_wall
    cell[-1, :] = NaturalMap.natural_wall
    cell[:, -1] = NaturalMap.natural_wall
    cell[0, :] = NaturalMap.natural_wall


def make_random_exits(only_sides=None):
    r = []
    sch = (Direction.north, Direction.east, Direction.south, Direction.west) if only_sides is None else only_sides
    for i in range(0, random.randint(len(sch), len(sch) * 3)):
        if i < len(sch):
            side = sch[i]
        else:
            side = random.choice(sch)
        leng = random.randint(3, WorldSize.cell)
        mid = random.randint(WorldSize.corner_wall, WorldSize.cell - WorldSize.corner_wall - 1)
        mid -= leng // 2
        a, b = range_intersect(mid, mid + leng, WorldSize.corner_wall, WorldSize.cell - WorldSize.corner_wall)
        r.append((side, a, b))
    return r


def apply_exits(cell, exits):
    for side, a, b in exits:
        if side == Direction.north:
            cell[a:b, 0] = NaturalMap.ground
        elif side == Direction.east:
            cell[-1, a:b] = NaturalMap.ground
        elif side == Direction.south:
            cell[a:b, -1] = NaturalMap.ground
        else:
            cell[0, a:b] = NaturalMap.ground


def find_exits(row):
    changes = numpy.where(numpy.diff(row == NaturalMap.natural_wall))[0]
    r = []
    opn = None
    if row[0] == NaturalMap.ground:
        opn = 0
    for i in changes[:]:
        if opn is None:
            opn = i + 1
        else:
            r.append((opn, i + 1))
            opn = None
    if opn is not None:
        r.append((opn, WorldSize.cell))
    return r


def point_dist(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    return sqrt(d[0] * d[0] + d[1] * d[1])


def build_road_graph(cell):
    exits = []
    exits.extend((Direction.north, a, b) for a, b in find_exits(cell[:, 0]))
    exits.extend((Direction.east, a, b) for a, b in find_exits(cell[WorldSize.cell - 1, :]))
    exits.extend((Direction.south, a, b) for a, b in find_exits(cell[:, WorldSize.cell - 1]))
    exits.extend((Direction.west, a, b) for a, b in find_exits(cell[0, :]))

    def make_side_point(side, x):
        if side == Direction.north:
            return (x, 0)
        elif side == Direction.east:
            return (WorldSize.cell - 1, x)
        elif side == Direction.south:
            return (x, WorldSize.cell - 1)
        else:
            return (0, x)

    # build roads between all exits
    points = []

    def add_point(x, y, **attr):
        p = {
            # 'id': len(points),
            'xy': (x, y),
            'neigh': set(),
        }
        p.update(attr)
        points.append(p)
        return len(points) - 1

    def connect_points(aidx, bidx):
        a, b = points[aidx], points[bidx]
        a['neigh'].add(bidx)
        b['neigh'].add(aidx)

    def disconnect_points(aidx, bidx):
        a, b = points[aidx], points[bidx]
        a['neigh'].discard(bidx)
        b['neigh'].discard(aidx)

    def split_chord(aidx, bidx):
        a, b = points[aidx], points[bidx]
        ap, bp = a['xy'], b['xy']
        mid = (
            (ap[0] + bp[0]) // 2,
            (ap[1] + bp[1]) // 2,
        )
        mid_id = add_point(mid[0], mid[1])
        disconnect_points(aidx, bidx)
        connect_points(aidx, mid_id)
        connect_points(bidx, mid_id)
        return mid_id

    def find_closest_notfixed_point_ids(my_id, x, y, n=1):
        me = (x, y)
        return list(map(lambda x: x[0], sorted(
            filter(lambda x: 'fixed' not in x[1] and x[0] != my_id, enumerate(points)),
            key=lambda p: point_dist(me, p[1]['xy'])
        )[:n]))

    def detect_group(group, point_idx):
        for idx in points[point_idx]['neigh']:
            if idx in group:
                continue
            group.add(idx)
            detect_group(group, idx)

    def detect_groups():
        all_idx = set(range(len(points)))
        groups = []
        while all_idx:
            sid = all_idx.pop()
            group = {sid}
            detect_group(group, sid)
            all_idx -= group
            groups.append(group)
        return groups

    def find_closest_group(my_id, groups):
        my_group = groups[my_id]
        min_dist, result = None, None
        for i, gr in enumerate(groups):
            if i == my_id:
                continue

            for aidx, bidx in itertools.product(my_group, gr):
                a = points[aidx]['xy']
                b = points[bidx]['xy']
                d = point_dist(a, b)
                if min_dist is None or d < min_dist:
                    min_dist = d
                    result = (aidx, bidx, i)
        return result

    def dijkstra(aidx, bidx):
        finished = set()
        not_finished = {aidx}
        mindist = {aidx: 0}
        while True:
            kdist, kidx = None, None
            for i in not_finished:
                if kdist is None or mindist[i] < kdist:
                    kdist, kidx = mindist[i], i

            if kidx == bidx:
                return mindist[kidx]

            kp = points[kidx]
            for midx in kp['neigh']:
                if midx in finished:
                    continue
                if midx not in mindist:
                    not_finished.add(midx)
                mp = points[midx]
                d = point_dist(kp['xy'], mp['xy'])
                if midx not in mindist or kdist + d < mindist[midx]:
                    mindist[midx] = kdist + d
            finished.add(kidx)
            not_finished.discard(kidx)

    # add points on exits
    for e in exits:
        if e[2] - e[1] < 10:
            base, end, size = (e[2] + e[1]) // 2, e[2], int((e[2] - e[1]) / 2)
        else:
            base, end, size = e[1] + 2, e[2] - 2, 3
        for i in range(base, end, 5):
            ppos = make_side_point(e[0], i)
            add_point(ppos[0], ppos[1], fixed=True, size=size)

    # add random nonfixed points
    not_fixed_ids = set()
    for change_i in range(random.randint(8, 30)):
        x = random.randint(WorldSize.corner_wall, WorldSize.cell - WorldSize.corner_wall - 1)
        y = random.randint(WorldSize.corner_wall, WorldSize.cell - WorldSize.corner_wall - 1)
        not_fixed_ids.add(add_point(x, y))

    # connect all points to nearest
    for aidx, pt in enumerate(points):
        bidx = find_closest_notfixed_point_ids(aidx, pt['xy'][0], pt['xy'][1])[0]
        connect_points(aidx, bidx)

    # join all connected groups
    groups = detect_groups()
    groups = [g & not_fixed_ids for g in groups]
    while len(groups) > 1:
        aidx, bidx, gid = find_closest_group(0, groups)
        connect_points(aidx, bidx)
        groups[0].update(groups[gid])
        groups.pop(gid)

    # connect some far points
    for change_i in range(random.randint(0, 8)):
        max_rate, join = None, None
        for aidx, bidx in itertools.combinations(not_fixed_ids, 2):
            ap, bp = points[aidx], points[bidx]
            direct_d = point_dist(ap['xy'], bp['xy'])
            path_d = dijkstra(aidx, bidx)
            rate = path_d - direct_d
            if max_rate is None or rate > max_rate:
                max_rate = rate
                join = (aidx, bidx)
        if join is None:
            break
        connect_points(*join)

    # assign point sizes
    for pt in points:
        if 'fixed' in pt:
            continue
        else:
            l = len(pt['neigh'])
            pt['size'] = random.randint(max(1, l // 2), max(2, l))

    # split and shift long chords
    worked = set()
    for aidx, ap in enumerate(points):
        for bidx in ap['neigh']:
            bp = points[bidx]
            key = aidx, bidx if aidx > bidx else bidx, aidx
            if key in worked:
                continue
            dist = point_dist(ap['xy'], bp['xy'])
            # continue
            if dist < WorldSize.cell / 6:
                continue
            midx = split_chord(aidx, bidx)
            mp = points[midx]
            old_xy = mp['xy']
            k = round(dist / 2.5)
            mp['xy'] = (
                ensure_range(
                    old_xy[0] + random.randint(-k, k), WorldSize.corner_wall,
                    WorldSize.cell - WorldSize.corner_wall - 1
                ),
                ensure_range(
                    old_xy[1] + random.randint(-k, k), WorldSize.corner_wall,
                    WorldSize.cell - WorldSize.corner_wall - 1
                ),
            )
            mp['size'] = (ap['size'] + bp['size']) // 2

    return points


def remove_circle(cell, cx, cy, radius):
    radius2 = radius * radius
    xa, xb = range_intersect(1, WorldSize.cell - 1, cx - radius, cx + radius + 1)
    ya, yb = range_intersect(1, WorldSize.cell - 1, cy - radius, cy + radius + 1)
    for x in range(xa, xb):
        for y in range(ya, yb):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy > radius2:
                continue
            cell[x, y] = NaturalMap.ground


def remove_walls_along_path(cell, a, b, a_diam, b_diam):
    remove_circle(cell, a[0], a[1], a_diam)
    remove_circle(cell, b[0], b[1], b_diam)
    i, d = 0, point_dist(a, b)
    if d == 0:
        return
    dx = (b[0] - a[0]) / d
    dy = (b[1] - a[1]) / d
    dd = (b_diam - a_diam) / d
    while i < d:
        x = round(i * dx + a[0])
        y = round(i * dy + a[1])
        diam = round(i * dd + a_diam)
        remove_circle(cell, x, y, diam)
        i += 1


def remove_walls_all_graph(cell, points):
    worked = set()
    for aidx, pt in enumerate(points):
        for bidx in pt['neigh']:
            key = aidx, bidx if aidx > bidx else bidx, aidx
            if key in worked:
                continue
            worked.add(key)
            pt2 = points[bidx]
            remove_walls_along_path(
                cell,
                pt['xy'], pt2['xy'],
                pt['size'], pt2['size']
            )


def debug_draw_cell(cell, roads):
    from PIL import Image, ImageDraw

    PIX_SIZE = 12
    out = Image.new('RGB', (WorldSize.cell * PIX_SIZE, WorldSize.cell * PIX_SIZE))
    draw = ImageDraw.Draw(out)
    draw.rectangle((
        0, 0,
        WorldSize.cell * PIX_SIZE, WorldSize.cell * PIX_SIZE,
    ), fill=(255, 255, 255))

    for y in range(WorldSize.cell):
        for x in range(WorldSize.cell):
            if cell[x, y] == NaturalMap.ground:
                continue
            draw.rectangle((
                x * PIX_SIZE, y * PIX_SIZE,
                (x + 1) * PIX_SIZE, (y + 1) * PIX_SIZE,
            ), fill=(0, 0, 0), outline=(128, 128, 128))

    def scale_point(xy):
        return (
            xy[0] * PIX_SIZE + PIX_SIZE // 2,
            xy[1] * PIX_SIZE + PIX_SIZE // 2,
        )

    for ptA in roads:
        for pid in ptA['neigh']:
            ptB = roads[pid]
            draw.line([
                scale_point(ptA['xy']),
                scale_point(ptB['xy']),
            ], fill=(255, 0, 0), width=PIX_SIZE // 2)
    for ptA in roads:
        x, y = ptA['xy']
        # col = (0, 128, 0) if ptA['size'] > 0 else (0, 0, 128)
        draw.rectangle((
            x * PIX_SIZE, y * PIX_SIZE,
            (x + 1) * PIX_SIZE, (y + 1) * PIX_SIZE,
        ), fill=(0, 128, 0), outline=(128, 128, 128))
    for i, ptA in enumerate(roads):
        x, y = ptA['xy']
        draw.text((x * PIX_SIZE, y * PIX_SIZE), str(i), fill=(0, 0, 0))

    out.show()


def make_cell(exits=None, exit_sides=None, _debug=False):
    cell = numpy.full((WorldSize.cell, WorldSize.cell), NaturalMap.natural_wall, dtype=DTypes.naturalmap)
    build_wall(cell)
    if exits is None:
        exits = make_random_exits(only_sides=exit_sides)
    apply_exits(cell, exits)
    roads = build_road_graph(cell)
    remove_walls_all_graph(cell, roads)
    if _debug:
        debug_draw_cell(cell, roads)
        # debug_draw_cell(cell, [])
    return cell
