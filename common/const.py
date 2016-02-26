from enum import IntEnum, Enum
import numpy


class EntityTypes(IntEnum):
    source = 1
    bot = 2
    construction_site = 3
    spawner = 4
    extension = 5
    radar = 6


class ConstructionTypes(IntEnum):
    wall = 1
    road = 2
    spawner = EntityTypes.spawner
    extension = EntityTypes.extension
    radar = EntityTypes.radar


class BotParts(Enum):
    # allows gathering/transporting energy, building structures
    # each part of this type increases gathering/building per tact, transporting capacity remains fixed though
    worker = (1, {'energy': 10})

    # allows longer continuous movements, stamina improvement
    movement = (2, {'stamina': 10})

    # allows close combat, each part of this type increases damage
    melee = (3, {'melee': 3})

    # allows ranged combat, each part of this type increases damage
    ranged = (4, {'ranged': 2})

    # allows healing, each part of this type increases healing rate
    heal = (5, {'heal': 2})

    # increases protection
    tough = (6, {'hp': 10})

    # allows transporting extra energy
    storage = (7, {'energy': 20})

    def __init__(self, ident, params):
        self.hp = params.get('hp', 5)
        self.energy = params.get('energy', 0)
        self.stamina = params.get('stamina', 0)
        self.melee = params.get('melee', 0)
        self.ranged = params.get('ranged', 0)
        self.heal = params.get('heal', 0)

    @staticmethod
    def max_hp(config):
        return sum(part.hp for part in config)

    @staticmethod
    def _iter_hp(config, hp, attr):
        # TODO: may be simpler logic here? with equal HP of each part?
        # TODO: support config bytes instead list
        p, r = 0, 0
        for part in config:
            r += getattr(part, attr)
            p += part.hp
            if p >= hp:
                break
        return r

    @classmethod
    def max_energy(cls, config, hp):
        return cls._iter_hp(config, hp, 'energy')

    @classmethod
    def max_stamina(cls, config, hp):
        return cls._iter_hp(config, hp, 'stamina')

    @classmethod
    def melee_attack(cls, config, hp):
        return cls._iter_hp(config, hp, 'melee')

    @classmethod
    def ranged_attack(cls, config, hp):
        return cls._iter_hp(config, hp, 'ranged')

    @classmethod
    def heal_effect(cls, config, hp):
        return cls._iter_hp(config, hp, 'heal')


class Direction(IntEnum):
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

    @classmethod
    def offset(cls, value):
        if value == cls.up:
            return (0, -1)
        elif value == cls.up_right:
            return (1, -1)
        elif value == cls.right:
            return (1, 0)
        elif value == cls.down_right:
            return (1, 1)
        elif value == cls.down:
            return (0, 1)
        elif value == cls.down_left:
            return (-1, 1)
        elif value == cls.left:
            return (-1, 0)
        elif value == cls.up_left:
            return (-1, -1)


class NaturalMap(IntEnum):
    # Possible values of naturalmap array
    unknown = 0  # or invisible
    ground = 1
    natural_wall = 2
    artifical_wall = 3
    road = 4


class WorldSize:
    cell = 64
    corner_wall = 3

    sources_per_cell = (2, 5)
    source_min_border_offset = 1


class Filenames:
    naturalmap = 'naturalmap.npy'
    ground_index = 'gindex.npy'
    wall_road_ext_times = 'wallroad.npy'
    drop_ext_times = 'drops.npy'
    pickled = 'data.pickle'


class DTypes:
    naturalmap = numpy.uint8
    ground_index = numpy.uint32
    time = numpy.uint32


class Entities:
    source_max_energy = 2000
    source_growth = 0.5

    bot_lifetime = 3000
    offline_building_lifetime = 3000

    road_decay = 0.1
    wall_decay = 0.1
    drop_decay = 0.1
