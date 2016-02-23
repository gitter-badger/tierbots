from enum import Enum
from typing import Iterable, TypeVar
import numpy


class NaturalObjects(Enum):
    energy_source = 1


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


class Positionable:
    # without sector logic, just absolute value relative to original spawn place
    @property
    def x(self) -> int:
        pass

    @property
    def y(self) -> int:
        pass


class Healthable:
    @property
    def hp(self) -> int:
        pass

    @property
    def max_hp(self) -> int:
        pass


class EnergyStorage:
    @property
    def energy(self) -> int:
        pass

    @property
    def max_energy(self) -> int:
        pass


class EnergyDrop(Positionable):
    @property
    def energy(self) -> int:
        pass


class EnergySource(Positionable, EnergyStorage):
    pass


class Bot(Positionable, Healthable):
    @property
    def part_config(self) -> Iterable[BotParts]:
        pass


class Building(Positionable, Healthable):
    # hp slowly fades when owner user is offline
    pass


class Enemy:
    @property
    def playername(self) -> str:
        pass


class EnemyBot(Bot, Enemy):
    pass


class EnemyConstructionSite(Building, Enemy):
    pass


class EnemyBuilding(Building, Enemy):
    @property
    def btype(self) -> BuildingTypes:
        pass


class MyConstructionSite(Building):
    # note: this is not a watcher
    @property
    def btype(self) -> BuildingTypes:
        pass

    @property
    def buildpoints(self) -> int:
        pass

    @property
    def cost(self) -> int:
        pass


class Watcher:
    # use NaturalMap constants
    @property
    def natural_map(self) -> numpy.array:
        pass

    @property
    def energy_drops_around(self) -> Iterable[EnergyDrop]:
        pass

    # 0 means no wall in this cell
    # any value N>0 means there is a wall with N health points
    @property
    def walls_around(self) -> numpy.array:
        pass

    # 0 means no road in this cell
    # any value N>0 means there is a road with N health points
    @property
    def roads_around(self) -> numpy.array:
        pass

    @property
    def enemy_bots_around(self) -> Iterable[EnemyBot]:
        pass

    AnyEnemyBuilding = TypeVar('AnyEnemyBuilding', EnemyConstructionSite, EnemyBuilding)

    @property
    def enemy_buildings_around(self) -> Iterable[AnyEnemyBuilding]:
        pass


class MyBot(Bot, Watcher, EnergyStorage):
    # decreasing value, when reaches zero bot dies
    @property
    def lifetime(self) -> int:
        pass

    @property
    def stamina(self) -> int:
        pass

    @property
    def max_stamina(self) -> int:
        pass

    def move(self, direction: Direction):
        pass

    def suicide(self):
        pass

    def gather(self, direction: Direction):
        pass

    def put(self, direction: Direction):
        pass

    def place_building(self, direction: Direction, building_type: BuildingTypes):
        pass

    def build(self, direction: Direction):
        pass

    def slay(self, direction: Direction):
        pass

    def shoot(self, dx: int, dy: int):
        pass

    def heal(self, direction: Direction):
        pass


class MyBuilding(Building, Watcher):
    pass


class SpawnerBuilding(MyBuilding, EnergyStorage):
    # allows spawning bots, can use Extensions in 30 block radius
    @property
    def busy_until(self) -> int:
        pass

    def build_bot(self, parts: Iterable[BotParts]):
        pass


class ExtensionBuilding(MyBuilding, EnergyStorage):
    # allows spawning better bots
    pass


class MyBuildingWithOperator(MyBuilding):
    @property
    def operator_bot(self) -> MyBot:
        pass


class Radar(MyBuildingWithOperator):
    # big range wall-through watcher, requires bot inside
    pass


class World:
    @property
    def time(self) -> int:
        pass

    @property
    def my_bots(self) -> Iterable[MyBot]:
        pass

    @property
    def my_buildings(self) -> Iterable[MyBuilding]:
        pass
