#Patrick Douglas Strategy/AI
import rg

class Robot:
    def act(self, game):
        # Determine what to do:
        ret_value = []
        ret_value = self.spawn(game, ret_value)
        ret_value = self.attack(game, ret_value)
        ret_value = self.otherwise(game, ret_value)
        return ret_value
    
    #Checks to see if player is in spawn.
    def spawn(self, game, current_return):
        #CHECK IF RETURN IS SET
        if rg.loc_types(self.location) == 'spawn':
            possible_locations = rg.locs_around(self.location, filter_out = ('invalid', 'obstacle', 'spawn'))
            for locs in possible_locations:
                #if game.robots[locs].player_id != self.player_id:
                #If health low, attack it, if high, remove it.
                pass
            best_option = [100, (0,0)]
            for locs in possible_locations:
                current = [rg.wdist(locs, rg.CENTER_POINT), locs]
                if current[0] <= best_option[0]:
                    best_option = current
            return ['move', best_option[1]]

    #Will check for nearby enemies and respond appropriately.
    def attack(self, game, current_return):
        pass

    #Guaranteed to return something if nothing else is returned.
    def otherwise(self, game, current_return):
        return ['guard']

