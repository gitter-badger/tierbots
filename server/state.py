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
        return x >= 0 and y >= 0 and x < self.naturalmap.shape[0] and y < self.naturalmap.shape[1]

    def place_new_entity(self, edata, x, y):
        '''
        Returns None if placing isn't possible. ID otherwise.
        '''
        k = (x, y)
        if not self._check_xy(x, y) or k in self._ent_map:
            return None
        edata['x'], edata['y'] = k
        eid = self._allocate_entity_id()
        self.entities[eid] = edata
        self._ent_map[k] = eid
        return eid

    def get_entity(self, x, y):
        '''
        Returns entity ID if entity exists there. None otherwise.
        '''
        return self._ent_map.get((x, y))

    def get_entity_by_id(self, eid):
        '''
        ID must be valid.
        Returns copied dict instance.
        '''
        return self.entities[eid].copy()

    def change_entity_prop(self, eid, key, value):
        '''
        ID must be valid.
        Don't attempt to change position.
        '''
        assert key != 'x' and key != 'y'
        self.entities[eid][key] = value

    def move_entity(self, eid, dirc):
        '''
        ID must be valid.
        Returns bool if success. Checks if there is other entity, but doesn't check walls.
        '''
        e = self.entities[eid]
        dx, dy = Direction.offset(dirc)
        k = e['x'] + dx, e['y'] + dy
        if not self._check_xy(*k) or k in self._ent_map:
            return False
        del self._ent_map[(e['x'], e['y'])]  # removing old link
        e['x'], e['y'] = k
        self._ent_map[k] = eid
        return True

    def remove_entity(self, eid):
        '''
        ID must be valid.
        '''
        e = self.entities[eid]
        del self._ent_map[(e['x'], e['y'])]
        del self.entities[eid]

    def get_natural(self, x, y):
        '''
        Returns type of NaturalMap object along with HP (None if object doesn't support HP).
        '''
        if not self._check_xy(x, y):
            return NaturalMap.natural_wall, None
        v, hp = self.naturalmap[x, y], None
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

    def change_natural_hp(self, x, y, delta_hp):
        '''
        Applies HP delta to NaturalMap object.
        Silently skips action on wrong conditions.
        Can also remove object.
        Returns bool of success.
        '''
        if not self._check_xy(x, y):
            return False
        v = self.naturalmap[x, y]
        if v != NaturalMap.artifical_wall and v != NaturalMap.road:
            return False
        gi = self.ground_index[x, y]
        new_death_time = zerotime_by_param_change(
            self.time, self.wall_road_ext_times[gi],
            Entities.wall_decay if v == NaturalMap.artifical_wall else Entities.road_decay,
            delta_hp
        )
        if new_death_time <= self.time:
            self.naturalmap[x, y] = NaturalMap.ground
        return True

    def set_natural_type(self, x, y, otype, hp):
        '''
        Creates (replaces) NaturalMap object with initial HP.
        Can't replace natural walls.
        Returns bool of success.
        '''
        if otype not in (NaturalMap.artifical_wall, NaturalMap.road):
            return False
        if hp <= 0 or not self._check_xy(x, y):
            return False
        v = self.naturalmap[x, y]
        if v == NaturalMap.natural_wall:
            return False
        self.naturalmap[x, y] = otype
        self.wall_road_ext_times[self.ground_index[x, y]] = zerotime_by_param_change(
            self.time, self.time,
            Entities.wall_decay if otype == NaturalMap.artifical_wall else Entities.road_decay,
            hp
        )
        return True

    def get_energy_drop(self, x, y):
        '''
        Returns energy of drop. None means energy drop doesn't exist.
        '''
        if not self._check_xy(x, y):
            return None
        death_time = self.drop_ext_times[self.ground_index[x, y]]
        val = param_by_zerotime(self.time, death_time, Entities.drop_decay)
        return val if val > 0 else None

    def change_energy_drop(self, x, y, delta_energy):
        '''
        Changes energy drop by amount of energy. Can also create or remove drop.
        '''
        if not self._check_xy(x, y):
            return
        gi = self.ground_index[x, y]
        self.drop_ext_times[gi] = zerotime_by_param_change(
            self.time, self.drop_ext_times[gi], Entities.drop_decay, delta_energy
        )

    def place_new_player_base(self, nickname, token):
        # must be invoked on first player's connection, not registration
        pass
