settings = {
    # game settings
    'spawn_every': 10,
    'spawn_per_player': 5,
    'board_size': 19,
    'robot_hp': 50,
    'attack_range': (8, 10),
    'collision_damage': 5,
    'suicide_damage': 15,
    'max_turns': 100,
    'str_limit': 50,  # limit on length of representation of action
    'max_seed': 2147483647,

    # rendering
    # commented out lines are the settings used for the old animated mode
    'FPS': 60,  # frames per second
    'turn_interval': 300,  # milliseconds per turn

    # colors
    'colors': [(0.49, 0.14, 0.14), (0.14, 0.14, 0.49)],
    'color_guard': None,  # (0.0, 0.14, 0.0),
    'color_guard_border': (0.0, 0.49, 0.0),
    # 'colors': [(0.9, 0, 0.2), (0, 0.9, 0.2)],
    'obstacle_color': (.2, .2, .2),
    'text_color': (0.6, 0.6, 0.6),  # for labelling rows/columns
    'text_color_dark': (0.1, 0.1, 0.1),  # HP color when bots are bright
    'text_color_bright': (0.9, 0.9, 0.9),  # HP color when bots are dark
    'normal_color': (.9, .9, .9),
    'highlight_color': (0.6, 0.6, 0.6),
    'target_color': (0.6, 0.6, 1),

    # highlighting
    'clear_highlight_between_turns': False,
    # 'clear_highlight_between_turns': True,
    'clear_highlight_target_between_turns': True,
    'highlight_cursor_blink': True,
    'rate_cursor_blink': 1000,
    # 'highlight_cursor_blink': True,
    'highlight_cursor_blink_interval': 0.5,

    'bot_shape': 'square',
    # 'bot_shape': 'circle',
    'draw_movement_arrow': True,
    # 'draw_movement_arrow': False,

    # animations (only enabled if -A is used)
    'bot_die_animation': True,
    'bot_move_animation': False,
    'bot_suicide_animation': False,
    'bot_hp_animation': False,

    # rating systems
    'default_rating': 1200,

    # user-scripting
    'max_time_initialization': 2000,
    'max_time_first_act': 1500,
    'max_time_per_act': 300,
    'exposed_properties': ('location', 'hp', 'player_id'),
    'player_only_properties': ('robot_id',),
    'user_obj_types': ('Robot',),
    'valid_commands': ('move', 'attack', 'guard', 'suicide'),
}

# just change stuff above this line


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
settings = AttrDict(settings)
