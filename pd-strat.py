#Patrick Douglas 
#Robot Strategy/AI
import rg

"""
-check if in spawn zone. 
   if yes, find open space and go there.
   if no, continue

-check surrounding area.
    if 1 enemy:
      if myhealth > enemyhealth:
        attack
      if myhealth < enemyhealth:
         if they have less than 15, suicide
         else back away
    if 2 or more enemy:
      if both less than 15 and mine less than 20, suicide
      else back away
    else go to move

-move to center:
  if cant go further, guard
"""

class Robot:
    def act(self, game):
        # Determine what to do:
        ret_value = ['empty']
        ret_value = self.spawn(game, ret_value)
        ret_value = self.attack(game, ret_value)
        ret_value = self.otherwise(game, ret_value)
        return ret_value
    
    #Checks to see if player is in spawn.
    def spawn(self, game, current_return):
        if current_return != ['empty']:
            return current_return
        #If bot is in spawn, determine how to move out.
        if rg.loc_types(self.location) == 'spawn':
            possible_locations = rg.locs_around(self.location, filter_out = ('invalid', 'obstacle', 'spawn'))
            enemy_locs = []
            for locs in possible_locations:
                if locs in game.robots and game.robots[locs].player_id != self.player_id:
                    enemy_locs.append(locs)
            for enemy in enemy_locs:
                if enemy.hp < 9:
                    return ['attack', enemy]
                elif enemy in possible_locations:
                    possible_locations.remove(enemy)
            best_option = [100, (0,0)]
            for locs in possible_locations:
                current = [rg.wdist(locs, rg.CENTER_POINT), locs]
                if current[0] <= best_option[0]:
                    best_option = current
            return ['move', best_option[1]]
        return current_return

    #Will check for nearby enemies and respond appropriately.
    def attack(self, game, current_return):
        if current_return != ['empty']:
            return current_return
        possible_locations = rg.locs_around(self.location, filter_out = ('invalid', 'obstacle', 'spawn'))
        enemy_locs = []
        enemy_num = 0
        for locs in possible_locations:
            if locs in game.robots and game.robots[locs].player_id != self.player_id:
                enemy_num += 1
                enemy_locs.append(locs)
        #Once we have a list of enemies, we can follow a process to determine how to deal with them.
        """ if 1 enemy:
            if myhealth > enemyhealth:
            attack
            if myhealth < enemyhealth:
            if they have less than 15, suicide
            else back away
            if 2 or more enemy:
            if both less than 15 and mine less than 20, suicide
            else back away
            else go to move """

        for enemy in enemy_locs:
            return ['attack', enemy]

        #Need to flesh out attack strategy
            if enemy_num == 1:
                return ['attack', enemy]
        return current_return

    #Guaranteed to return something if nothing else is returned.
    def otherwise(self, game, current_return):
        if current_return != ['empty']:
            return current_return
        if self.location != rg.CENTER_POINT:
            towards_center = rg.toward(self.location, rg.CENTER_POINT)
            return ['move', towards_center]
        else:
            return ['guard']

