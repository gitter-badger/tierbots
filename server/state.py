'''
State includes:

- World map (including walls and roads, using NaturalMap codes), numpy array.
- Wall/road health status (calculated death time), numpy array.
- List of entities (NaturalObjects, Building, Bot)
- Player database with authentication data
- Current time (tick counter)

Full state data must be loaded by server into RAM, so we don't need any SQL solution.

Tick counter starts from 0 on each server restart. DON'T save any timestamps into files,
instead calculate current values.

Player records:
    ID: int
    name: str
    pubkey: binary
    map_offset: (int, int) | None (if player never was active)
'''
from os.path import join, isdir
from os import mkdir, listdir
import numpy
import pickle
from random import getrandbits

from common.const import NaturalMap, WorldSize, Filenames, DTypes


class ServerState:
    '''
    size: (int, int)
    maxplayers: int
    worldmap: numpy.array
    wallroad: numpy.array
    entities: {int: obj}
    players: {str: obj}
    time: int
    '''

    @classmethod
    def load(cls, foldername):
        assert isdir(foldername), 'Trying to load non-existent directory'
        o = cls(foldername)
        o.worldmap = numpy.load(o._get_filename(Filenames.worldmap), allow_pickle=False)
        o.wallroad = numpy.load(o._get_filename(Filenames.wallroad), allow_pickle=False)
        with open(o._get_filename(Filenames.pickled), 'rb') as f:
            data = pickle.load(f)
        for k, v in data.items():
            setattr(o, k, v)
        return o

    def save(self):
        numpy.save(self._get_filename(Filenames.worldmap), self.worldmap, allow_pickle=False)
        numpy.save(self._get_filename(Filenames.wallroad), self.wallroad, allow_pickle=False)
        with open(self._get_filename(Filenames.pickled), 'wb') as f:
            pickle.dump(f, {k: getattr(self, k) for k in (
                'size',
                'maxplayers',
                'time',
                'entities',
                'players',
            )})

    @classmethod
    def create_new(cls, foldername, width, height):
        if isdir(foldername):
            assert not listdir(foldername), 'Directory must be empty to start new world'
        else:
            mkdir(foldername)

        o = cls(foldername)
        o.size = (WorldSize.cell * width, WorldSize.cell * height)
        o.maxplayers = width * height
        o.worldmap = numpy.full(o.size, NaturalMap.ground, dtype=DTypes.worldmap)
        o.wallroad = numpy.zeros(o.size, dtype=DTypes.wallroad)
        o.entities = {}
        o.players = {}
        o.time = 0
        o._build_caches()

        return o

    def __init__(self, foldername):
        self.foldername = foldername

    def _get_filename(self, en):
        return join(self.foldername, en.value)

    def _build_caches(self):
        self._ent_map = {(e.x, e.y): e for e in self.entities.values()}

    def allocate_entity_id(self):
        while True:
            k = getrandbits(32)
            if k not in self.entities:
                self.entities[k] = None
                return k

    def place_new_player(self, nickname, token):
        # must be invoked on first player's connection, not registration
        pass
