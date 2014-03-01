import random
from collections import defaultdict

from rgkit import rg
from rgkit.settings import AttrDict


class GameState(object):
    def __init__(self, settings, use_start=False, turn=0,
                 next_robot_id=0, seed=None, symmetric=False):
        self._settings = settings

        if seed is None:
            seed = random.randint(0, self._settings.max_seed)
        self._seed = str(seed)
        self._spawn_random = random.Random(self._seed + 's')
        self._attack_random = random.Random(self._seed + 'a')

        self.robots = {}
        self.turn = turn
        self._next_robot_id = next_robot_id

        if use_start:
            for loc in self._settings.start1:
                self.add_robot(loc, 0)
            for loc in self._settings.start2:
                self.add_robot(loc, 1)

        self.symmetric = symmetric
        if symmetric:
            self._get_spawn_locations = self._get_spawn_locations_symmetric
        else:
            self._get_spawn_locations = self._get_spawn_locations_random

    def add_robot(self, loc, player_id, hp=None, robot_id=None):
        if hp is None:
            hp = self._settings.robot_hp

        if robot_id is None:
            robot_id = self._next_robot_id
            self._next_robot_id += 1

        self.robots[loc] = AttrDict({
            'location': loc,
            'hp': hp,
            'player_id': player_id,
            'robot_id': robot_id
        })

    def remove_robot(self, loc):
        if self.is_robot(loc):
            del self.robots[loc]

    def is_robot(self, loc):
        return loc in self.robots

    def _get_spawn_locations_symmetric(self):
        def symmetric_loc(loc):
            return (self._settings.board_size - 1 - loc[0],
                    self._settings.board_size - 1 - loc[1])
        locs1 = []
        locs2 = []
        while len(locs1) < self._settings.spawn_per_player:
            loc = self._spawn_random.choice(self._settings.spawn_coords)
            sloc = symmetric_loc(loc)
            if loc not in locs1 and loc not in locs2:
                if sloc not in locs1 and sloc not in locs2:
                    locs1.append(loc)
                    locs2.append(sloc)
        return locs1, locs2

    def _get_spawn_locations_random(self):
        # see http://stackoverflow.com/questions/2612648/reservoir-sampling
        locations = []
        per_player = self._settings.spawn_per_player
        count = per_player * 2
        n = 0
        for loc in self._settings.spawn_coords:
            n += 1
            if len(locations) < count:
                locations.append(loc)
            else:
                s = int(self._spawn_random.random() * n)
                if s < count:
                    locations[s] = loc
        self._spawn_random.shuffle(locations)
        return locations[:per_player], locations[per_player:]

    # actions = {loc: action}
    # all actions must be valid
    # delta = [AttrDict{
    #    'loc': loc,
    #    'hp': hp,
    #    'player_id': player_id,
    #    'loc_end': loc_end,
    #    'hp_end': hp_end
    # }]
    def get_delta(self, actions, spawn=True):
        delta = []

        def dest(loc):
            if actions[loc][0] == 'move':
                return actions[loc][1]
            else:
                return loc

        hitpoints = defaultdict(lambda: set())

        def stuck(loc):
            # we are not moving anywhere
            # inform others
            old_hitpoints = hitpoints[loc]
            hitpoints[loc] = set([loc])

            for rival in old_hitpoints:
                if rival != loc:
                    stuck(rival)

        for loc in self.robots:
            hitpoints[dest(loc)].add(loc)

        for loc in self.robots:
            if len(hitpoints[dest(loc)]) > 1 or (self.is_robot(dest(loc)) and
                                                 dest(loc) != loc and
                                                 dest(dest(loc)) == loc):
                # we've got a problem
                stuck(loc)

        # calculate new locations
        for loc, robot in self.robots.iteritems():
            if actions[loc][0] == 'move' and loc in hitpoints[loc]:
                new_loc = loc
            else:
                new_loc = dest(loc)

            delta.append(AttrDict({
                'loc': loc,
                'hp': robot.hp,
                'player_id': robot.player_id,
                'loc_end': new_loc,
                'hp_end': robot.hp  # will be adjusted later
            }))

        # {loc: set(robots collided with loc}
        collisions = defaultdict(lambda: set())
        for loc in self.robots:
            for loc2 in hitpoints[dest(loc)]:
                collisions[loc].add(loc2)
                collisions[loc2].add(loc)

        # {loc: [damage_dealt_by_player_0, damage_dealt_by_player_1]}
        damage_map = defaultdict(lambda: [0, 0])

        for loc, robot in self.robots.iteritems():
            actor_id = robot.player_id

            if actions[loc][0] == 'attack':
                target = actions[loc][1]
                damage = self._attack_random.randint(
                    *self._settings.attack_range)
                damage_map[target][actor_id] += damage

            if actions[loc][0] == 'suicide':
                damage_map[loc][1 - actor_id] += self._settings.robot_hp

                damage = self._settings.suicide_damage
                for target in rg.locs_around(loc):
                    damage_map[target][actor_id] += damage

        # apply damage
        for delta_info in delta:
            loc = delta_info.loc
            loc_end = delta_info.loc_end
            robot = self.robots[loc]

            # apply collision damage
            if actions[loc][0] != 'guard':
                damage = self._settings.collision_damage

                for loc2 in collisions[delta_info.loc]:
                    if robot.player_id != self.robots[loc2].player_id:
                        delta_info.hp_end -= damage

            # apply other damage
            damage_taken = damage_map[loc_end][1 - robot.player_id]
            if actions[loc][0] == 'guard':
                damage_taken /= 2

            delta_info.hp_end -= damage_taken

        if spawn:
            if self.turn % self._settings.spawn_every == 0:
                # clear bots on spawn
                for delta_info in delta:
                    loc_end = delta_info.loc_end

                    if loc_end in self._settings.spawn_coords:
                        delta_info.hp_end = 0

                # spawn bots
                locations = self._get_spawn_locations()
                for player_id, locs in enumerate(locations):
                    for loc in locs:
                        delta.append(AttrDict({
                            'loc': loc,
                            'hp': 0,
                            'player_id': player_id,
                            'loc_end': loc,
                            'hp_end': self._settings.robot_hp
                        }))

        return delta

    # delta = [AttrDict{
    #    'loc': loc,
    #    'hp': hp,
    #    'player_id': player_id,
    #    'loc_end': loc_end,
    #    'hp_end': hp_end
    # }]
    # returns new GameState
    def apply_delta(self, delta):
        new_state = GameState(self._settings,
                              next_robot_id=self._next_robot_id,
                              turn=self.turn + 1,
                              seed=self._spawn_random.randint(
                                  0, self._settings.max_seed),
                              symmetric=self.symmetric)

        for delta_info in delta:
            if delta_info.hp_end > 0:
                loc = delta_info.loc

                # is this a new robot?
                if delta_info.hp > 0:
                    robot_id = self.robots[loc].robot_id
                else:
                    robot_id = None

                new_state.add_robot(delta_info.loc_end, delta_info.player_id,
                                    delta_info.hp_end, robot_id)

        return new_state

    # actions = {loc: action}
    # all actions must be valid
    # returns new GameState
    def apply_actions(self, actions, spawn=True):
        delta = self.get_delta(actions, spawn)

        return self.apply_delta(delta)

    def get_scores(self):
        scores = [0, 0]

        for robot in self.robots.itervalues():
            scores[robot.player_id] += 1

        return scores

    # export GameState to be used by a robot
    def get_game_info(self, player_id):
        game_info = AttrDict()

        game_info.robots = dict((loc, AttrDict(robot))
                                for loc, robot in self.robots.iteritems())
        for robot in game_info.robots.itervalues():
            if robot.player_id != player_id:
                del robot.robot_id

        game_info.turn = self.turn

        return game_info

    # actor = location
    # action = well, action
    def is_valid_action(self, actor, action):
        try:
            if len(str(action)) > self._settings.str_limit:
                return False

            if len(repr(action)) > self._settings.str_limit:
                return False

            if action[0] in ['move', 'attack']:
                return action[1] in rg.locs_around(
                    actor, filter_out=['invalid', 'obstacle'])
            elif action[0] in ['guard', 'suicide']:
                return True
            else:
                return False

        except:
            return False
