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

'''
from os.path import join, isdir
from os import mkdir, listdir
import numpy
import pickle
from random import getrandbits

from common.const import NaturalMap, Filenames, DTypes, Entities, EntityTypes, Direction
from common.decay import param_by_zerotime, zerotime_by_param_change


class ServerState:
    '''
    size: (int, int)
    maxplayers: int
    naturalmap: numpy.array
    wallroad: numpy.array
    entities: {int: obj}
    players: {str: obj}
    time: int
    '''

    @classmethod
    def load(cls, foldername):
        assert isdir(foldername), 'Trying to load non-existent directory'
        o = cls(foldername)
        o.naturalmap = numpy.load(o._get_filename(Filenames.naturalmap), allow_pickle=False)
        o.wallroad = numpy.load(o._get_filename(Filenames.wallroad), allow_pickle=False)
        with open(o._get_filename(Filenames.pickled), 'rb') as f:
            data = pickle.load(f)
        for k, v in data.items():
            setattr(o, k, v)
        return o

    def save(self):
        numpy.save(self._get_filename(Filenames.naturalmap), self.naturalmap, allow_pickle=False)
        numpy.save(self._get_filename(Filenames.wallroad), self.wallroad, allow_pickle=False)
        with open(self._get_filename(Filenames.pickled), 'wb') as f:
            pickle.dump(f, {k: getattr(self, k) for k in (
                'size',
                'maxplayers',
                'time',
                'entities',
                'players',
            )})

    @staticmethod
    def _build_ground_index(naturalmap):
        # zero means invalid value, i.e. wall
        out = numpy.zeros(naturalmap.shape, dtype=DTypes.ground_index)
        idx = 1
        for x in range(naturalmap.shape[0]):
            for y in range(naturalmap.shape[1]):
                if naturalmap[x, y] == NaturalMap.ground:
                    out[x, y] = idx
                    idx += 1
        return out, idx

    @classmethod
    def create_new(cls, foldername, width, height):
        if isdir(foldername):
            assert not listdir(foldername), 'Directory must be empty to start new world'
        else:
            mkdir(foldername)

        from worldgen import generate_world

        o = cls(foldername)
        o.naturalmap, sources = generate_world(width, height)
        o.ground_index, gidx_len = cls._build_ground_index(o.naturalmap)
        o.wall_road_ext_times = numpy.zeros((gidx_len, ), dtype=DTypes.time)
        o.drop_ext_times = numpy.zeros((gidx_len, ), dtype=DTypes.time)

        maxplayers = len(sources) // 4
        o.players = [None for i in range(maxplayers)]
        o.time = 0

        o.entities = {}
        for source in sources:
            o.entities[o._allocate_entity_id()] = {
                'type': EntityTypes.source,
                'x': source[0],
                'y': source[1],
                'energy': Entities.source_max_energy,
            }

        o._build_caches()
        o.save()

        return o

    def __init__(self, foldername):
        self.foldername = foldername

    def _get_filename(self, en):
        return join(self.foldername, en.value)

    def _build_caches(self):
        self._ent_map = {(e.x, e.y): k for k, e in self.entities.items()}

    def _allocate_entity_id(self):
        while True:
            k = getrandbits(32)
            if k not in self.entities:
                self.entities[k] = None
                return k

    def _check_xy(self, x, y):
        if x < 0 or y < 0 or x >= self.naturalmap.shape[0] or y >= self.naturalmap.shape[1]:
            raise IndexError

    def move_entity(self, eid, dirc):
        # Doesn't check any constraints!
        e = self.entities[eid]
        dx, dy = Direction.offset(dirc)
        nx, ny = e['x'] + dx, e['y'] + dy
        self._check_xy(nx, ny)
        del self._ent_map[(e['x'], e['y'])]
        e['x'], e['y'] = nx, ny
        k = (nx, ny)
        assert k not in self._ent_map  # avoid overwriting any entity
        self._ent_map[k] = eid

    def place_new_entity(self, edata, x, y):
        self._check_xy(x, y)
        edata['x'], edata['y'] = x, y
        k = (x, y)
        assert k not in self._ent_map  # avoid overwriting any entity
        eid = self._allocate_entity_id()
        self.entities[eid] = edata
        self._ent_map[k] = eid
        return eid

    def remove_entity(self, eid):
        e = self.entities[eid]
        del self._ent_map[(e['x'], e['y'])]
        del self.entities[eid]

    def get_natural(self, x, y):
        self._check_xy(x, y)
        v, hp = self.naturalmap[x, y], 0
        if v == NaturalMap.artifical_wall or v == NaturalMap.road:
            death_time = self.wall_road_ext_times[self.ground_index[x, y]]
            if self.time >= death_time:
                v = NaturalMap.ground
                self.naturalmap[x, y] = NaturalMap.ground
            else:
                hp = param_by_zerotime(
                    self.time, death_time,
                    Entities.wall_decay if v == NaturalMap.artifical_wall else Entities.road_decay
                )
        return v, hp

    def change_natural(self, x, y, delta_hp):
        self._check_xy(x, y)
        v = self.naturalmap[x, y]
        if v != NaturalMap.artifical_wall and v != NaturalMap.road:
            return
        gi = self.ground_index[x, y]
        new_death_time = zerotime_by_param_change(
            self.time, self.wall_road_ext_times[gi],
            Entities.wall_decay if v == NaturalMap.artifical_wall else Entities.road_decay,
            delta_hp
        )
        if new_death_time <= self.time:
            self.naturalmap[x, y] = NaturalMap.ground

    def get_energy_drop(self, x, y):
        self._check_xy(x, y)
        death_time = self.drop_ext_times[self.ground_index[x, y]]
        return param_by_zerotime(self.time, death_time, Entities.drop_decay)

    def change_energy_drop(self, x, y, delta_energy):
        self._check_xy(x, y)
        gi = self.ground_index[x, y]
        self.drop_ext_times[gi] = zerotime_by_param_change(
            self.time, self.drop_ext_times[gi], Entities.drop_decay, delta_energy
        )

    def place_new_player_base(self, nickname, token):
        # must be invoked on first player's connection, not registration
        pass
