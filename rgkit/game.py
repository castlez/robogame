import imp
import random
import sys
import traceback
try:
    import threading
except ImportError:
    import dummy_threading as threading


from rgkit import rg
from rgkit.gamestate import GameState
from rgkit.settings import settings

sys.modules['rg'] = rg  # preserve backwards compatible robot imports


class NullDevice(object):
    def write(self, msg):
        pass


def init_settings(map_data):
    # I'll get rid of the globals. I promise.
    global settings
    settings.spawn_coords = map_data['spawn']
    settings.obstacles = map_data['obstacle']
    settings.start1 = map_data['start1']
    settings.start2 = map_data['start2']
    rg.set_settings(settings)
    return settings


class Player(object):
    def __init__(self, code=None, robot=None):
        self._player_id = None  # must be set using set_player_id

        if code is not None:
            self._code = code
            self.reload()
        elif robot is not None:
            self._module = None
            self._robot = robot
        else:
            raise Exception('you need to provide code or a robot')

    def reload(self):
        self._module = imp.new_module('usercode%d' % id(self))
        exec self._code in self._module.__dict__
        self._robot = self._module.__dict__['Robot']()

    def set_player_id(self, player_id):
        self._player_id = player_id

    def _get_action(self, game_state, game_info, robot, seed):
        try:
            random.seed(seed)
            # Server requires knowledge of seed
            game_info.seed = seed

            self._robot.location = robot.location
            self._robot.hp = robot.hp
            self._robot.player_id = robot.player_id
            self._robot.robot_id = robot.robot_id
            action = self._robot.act(game_info)

            if not game_state.is_valid_action(robot.location, action):
                raise Exception(
                    'Bot {0}: {1} is not a valid action from {2}'.format(
                        robot.robot_id + 1, action, robot.location)
                )

        except:
            traceback.print_exc(file=sys.stdout)
            action = ['guard']

        return action

    # returns map (loc) -> (action) for all bots of this player
    # 'fixes' invalid actions
    def get_actions(self, game_state, seed):
        game_info = game_state.get_game_info(self._player_id)
        actions = {}

        for loc, robot in game_state.robots.iteritems():
            if robot.player_id == self._player_id:
                # Every act call should get a different random seed
                actions[loc] = self._get_action(
                    game_state, game_info, robot,
                    seed=str(seed) + '-' + str(robot.robot_id))

        return actions


class Game(object):
    def __init__(self, player1, player2, record_actions=False,
                 record_history=False, print_info=False,
                 seed=None, quiet=0, symmetric=False):
        self._settings = settings
        self._player1 = player1
        self._player1.set_player_id(0)
        self._player2 = player2
        self._player2.set_player_id(1)
        self._record_actions = record_actions
        self._record_history = record_history
        self._print_info = print_info
        if seed is None:
            seed = random.randint(0, self._settings.max_seed)
        self.seed = str(seed)
        self._random = random.Random(self.seed)
        self._quiet = quiet
        self._state = GameState(self._settings, use_start=True, seed=self.seed,
                                symmetric=symmetric)

        self._actions_on_turn = {}
        self._states = {}
        self.history = []  # TODO: make private

    # actions_on_turn = {loc: log_item}
    # log_item = {
    #     'name': action_name,
    #     'target': action_target or None,
    #     'loc': loc,
    #     'hp': hp,
    #     'player': player_id,
    #     'loc_end': loc_end,
    #     'hp_end': hp_end
    # }
    #
    # or dummy if turn == settings.max_turn
    def get_actions_on_turn(self, turn):
        assert self._record_actions
        return self._actions_on_turn[turn]

    def get_state(self, turn):
        return self._states[turn]

    def _save_actions_on_turn(self, actions_on_turn, turn):
        self._actions_on_turn[turn] = actions_on_turn

    def _save_state(self, state, turn):
        self._states[turn] = state

    def _get_robots_actions(self):
        if self._quiet < 3:
            if self._quiet >= 1:
                sys.stdout = NullDevice()
            if self._quiet >= 2:
                sys.stderr = NullDevice()
        seed1 = self._random.randint(0, self._settings.max_seed)
        seed2 = self._random.randint(0, self._settings.max_seed)
        actions = self._player1.get_actions(self._state, seed1)
        actions2 = self._player2.get_actions(self._state, seed2)
        actions.update(actions2)
        if self._quiet < 3:
            if self._quiet >= 1:
                sys.stdout = sys.__stdout__
            if self._quiet >= 2:
                sys.stderr = sys.__stderr__

        return actions

    def _make_history(self, actions):
        '''
        An aggregate of all bots and their actions this turn.

        Stores a list of each player's bots at the start of this turn and
        the actions they each performed this turn. Newly spawned bots have no
        actions.
        '''
        robots = []
        for loc, robot in self._state.robots.iteritems():
            robot_info = {
                'location': loc,
                'hp': robot.hp,
                'player_id': robot.player_id,
                'robot_id': robot.robot_id,
            }
            if loc in actions:
                robot_info['action'] = actions[loc]
            robots.append(robot_info)
        return robots

    def _calculate_actions_on_turn(self, delta, actions):
        actions_on_turn = {}

        for delta_info in delta:
            loc = delta_info.loc

            if loc in actions:
                name = actions[loc][0]
                if name in ['move', 'attack']:
                    target = actions[loc][1]
                else:
                    target = None
            else:
                name = 'spawn'
                target = None

            # note that a spawned bot may overwrite an existing bot
            actions_on_turn[loc] = {
                'name': name,
                'target': target,
                'loc': loc,
                'hp': delta_info.hp,
                'player': delta_info.player_id,
                'loc_end': delta_info.loc_end,
                'hp_end': delta_info.hp_end
            }

        return actions_on_turn

    def run_turn(self):
        if self._print_info:
            print (' running turn %d ' % (self._state.turn)).center(70, '-')

        actions = self._get_robots_actions()

        delta = self._state.get_delta(actions)

        if self._record_actions:
            actions_on_turn = self._calculate_actions_on_turn(delta, actions)
            self._save_actions_on_turn(actions_on_turn, self._state.turn)

        new_state = self._state.apply_delta(delta)
        self._save_state(new_state, new_state.turn)

        if self._record_history:
            self.history.append(self._make_history(actions))

        self._state = new_state

    def run_all_turns(self):
        assert self._state.turn == 0

        if self._print_info:
            print ('Match seed: {0}'.format(self.seed))

        self._save_state(self._state, 0)

        while self._state.turn < self._settings.max_turns:
            self.run_turn()

        # create last turn's state for server history
        if self._record_history:
            self.history.append(self._make_history({}))

        # create dummy data for last turn
        # TODO: render should be cleverer
        actions_on_turn = {}

        for loc, robot in self._state.robots.iteritems():
            log_item = {
                'name': '',
                'target': None,
                'loc': loc,
                'hp': robot.hp,
                'player': robot.player_id,
                'loc_end': loc,
                'hp_end': robot.hp
            }

            actions_on_turn[loc] = log_item

        self._save_actions_on_turn(actions_on_turn, self._settings.max_turns)

    def get_scores(self):
        return self.get_state(self._settings.max_turns).get_scores()


class ThreadedGame(Game):
    def __init__(self, *args, **kwargs):
        super(ThreadedGame, self).__init__(*args, **kwargs)

        max_turn = self._settings.max_turns

        # events set when actions_on_turn are calculated
        self._has_actions_on_turn = [threading.Event()
                                     for _ in xrange(max_turn + 1)]

        # events set when state are calculated
        self._has_state = [threading.Event()
                           for _ in xrange(max_turn + 1)]

    def get_actions_on_turn(self, turn):
        self._has_actions_on_turn[turn].wait()
        return super(ThreadedGame, self).get_actions_on_turn(turn)

    def get_state(self, turn):
        self._has_state[turn].wait()
        return super(ThreadedGame, self).get_state(turn)

    def _save_actions_on_turn(self, actions_on_turn, turn):
        super(ThreadedGame, self)._save_actions_on_turn(actions_on_turn, turn)
        self._has_actions_on_turn[turn].set()

    def _save_state(self, state, turn):
        super(ThreadedGame, self)._save_state(state, turn)
        self._has_state[turn].set()

    def run_all_turns(self):
        lock = threading.Lock()

        def task():
            with lock:
                super(ThreadedGame, self).run_all_turns()

        turn_runner = threading.Thread(target=task)
        turn_runner.daemon = True
        turn_runner.start()
