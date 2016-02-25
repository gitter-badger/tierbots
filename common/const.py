from enum import Enum


__all__ = ('NaturalObjects', 'BuildingTypes', 'BotParts', 'Direction', 'NaturalMap')


class NaturalObjects(Enum):
    energy_source = 1
    energy_drop = 2


class BuildingTypes(Enum):
    cons_site = 1
    spawner = 2
    extension = 3
    radar = 4


class BotParts(Enum):
    # allows gathering/transporting energy, building structures
    # each part of this type increases gathering/building per tact, transporting capacity remains fixed though
    worker = 1

    # allows longer continuous movements, stamina improvement
    movement = 2

    # allows close combat, each part of this type increases damage
    melee = 3

    # allows ranged combat, each part of this type increases damage
    ranged = 4

    # allows healing, each part of this type increases healing rate
    heal = 5

    # increases protection
    armor = 6

    # allows transporting extra energy
    storage = 7

    # allows longer life
    life = 8


class Direction(Enum):
    north = 1
    north_east = 2
    east = 3
    south_east = 4
    south = 5
    south_west = 6
    west = 7
    north_west = 8

    up = 1
    up_right = 2
    right = 3
    down_right = 4
    down = 5
    down_left = 6
    left = 7
    up_left = 8


class NaturalMap(Enum):
    unknown = 0  # or invisible
    ground = 1
    natural_wall = 2
    artifical_wall = 3
    road = 4


class WorldSize:
    cell = 64
    corner_wall = 3
