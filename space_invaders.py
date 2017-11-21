from __future__ import print_function
import math
from enum import Enum
from CYLGame import GameLanguage
from CYLGame import Game
from CYLGame import MessagePanel
from CYLGame import MapPanel
from CYLGame import StatusPanel
from CYLGame import PanelBorder
from Invader import Invader

class Direction(Enum):
    RIGHT = 1
    LEFT = 2

class DropDodger(Game):
    MAP_WIDTH = 60
    MAP_HEIGHT = 25
    SCREEN_WIDTH = 60
    SCREEN_HEIGHT = MAP_HEIGHT + 6
    MSG_START = 20
    MAX_MSG_LEN = SCREEN_WIDTH - MSG_START - 1
    CHAR_WIDTH = 16
    CHAR_HEIGHT = 16
    GAME_TITLE = "Space Invaders"
    CHAR_SET = "terminal16x16_gs_ro.png"


    NUM_OF_INVADERS = 10
    TOTAL_INVADERS = 10
    NUM_OF_PITS_START = 0
    NUM_OF_PITS_PER_LEVEL = 8
    MAX_TURNS = 300

    PLAYER = '@'
    EMPTY = ' '
    PIT = '^'
    INVADER = 'X'
    MISSILE = '!'
    BULLET = '#'
    BARRIER_1 = '1'
    BARRIER_2 = '2'
    BARRIER_3 = '3'
    BARRIER_4 = '4'

    def __init__(self, random):
        self.random = random
        self.running = True
        self.in_pit = False
        self.centerx = self.MAP_WIDTH / 2
        self.centery = self.MAP_HEIGHT / 2
        self.player_pos = [self.centerx, (int) (self.MAP_HEIGHT * .99)]
        self.player_right = [self.centerx + 1, (int) (self.MAP_HEIGHT * .99)]
        self.player_left = [self.centerx - 1, (int) (self.MAP_HEIGHT * .99)]
        self.invaders = []
        self.drops_eaten = 0
        self.invaders_left = 0
        self.missiles_left = 0
        self.apple_pos = []
        self.objects = []
        self.turns = 0
        self.level = 0
        self.gravity_power = 1
        self.bullet_speed = 3
        self.invader_speed = 1
        self.placed_invaders = 0
        self.movement_direction = Direction.RIGHT
        self.msg_panel = MessagePanel(self.MSG_START, self.MAP_HEIGHT+1, self.SCREEN_WIDTH - self.MSG_START, 5)
        self.status_panel = StatusPanel(0, self.MAP_HEIGHT+1, self.MSG_START, 5)
        self.panels = [self.msg_panel, self.status_panel]
        self.msg_panel.add("Welcome to "+self.GAME_TITLE+"!!!")
        self.msg_panel.add("Move left and right to avoid being hit by the raindrops")
        self.lives = 3
        self.life_lost = False

        self.__create_map()

    def __create_map(self):
        self.map = MapPanel(0, 0, self.MAP_WIDTH, self.MAP_HEIGHT+1, self.EMPTY,
                            border=PanelBorder.create(bottom="-"))
        self.panels += [self.map]

        self.map[(self.player_pos[0], self.player_pos[1])] = self.PLAYER
        self.map[(self.player_right[0], self.player_right[1])] = self.PLAYER
        self.map[(self.player_left[0], self.player_left[1])] = self.PLAYER

        self.draw_level()

    def draw_level(self):
      start_barrier = 5 #we want to offset the first barrier
      barrier_height = 3
      barrier_width = 5
      set_sb = False
      for w in range(0, 60):
        for h in range(0, 25):
          #generating the invaders
          if h < 4 and w >=20 and w <= 40: #4 rows of 20 aliens (22 technically)
            self.invaders.append(Invader((w, h)))
            self.map[(w, h)] = self.INVADER
            #TODO: delete
            #self.map[(w, h)] = self.INVADER
            #self.placed_invaders += 1
          #generate the barriers
          if h >= self.MAP_HEIGHT - 1 - barrier_height and h < self.MAP_HEIGHT - 1:
            #it's a barrier row
            if w >= start_barrier and w <= start_barrier + barrier_width: #we draw the barrier
              self.map[(w, h)] = self.BARRIER_4
              #TODO: dont' overwrite start barrier while looping over the rightmost column of the barrier - this leads to only one being drawn
              if w == start_barrier + barrier_width:
                set_sb = True
        if set_sb:
          start_barrier += 12 #to achieve spacing between barriers...hopefully
          set_sb = False
      self.set_bottom_invaders()
      
      
    def set_bottom_invaders(self):
        # all_invaders = [ x for x in self.invaders ]
        cols = {}
        #sort all the invaders into columns
        for invader in self.invaders:
            pos = invader.get_pos()
            if pos[0] in cols:
                cols[pos[0]].append(invader)
            else:
                empty = []
                empty.append(invader)
                cols[pos[0]] = empty
        #sort each column on y value descending (high y values are "lower")
        for i in range(0, self.MAP_WIDTH):
          if i in cols:
            cols[i] = sorted(cols[i], key=lambda x: x.get_pos()[1], reverse=True)
            cols[i][0].set_bottom(True)
        




    #TODO: delete
    #def place_invaders(self, count):
    #    self.place_objects(self.INVADER, count)
    #    self.invaders_left += count
    #    self.placed_invaders += count

    def fire_missiles(self):
        for invader in self.invaders:
            if invader.get_bottom() and not invader.get_missile(): #it can fire
                invader_pos = invader.get_pos()
                #first we determine if the invader can fire...are there any invaders below it?
                #second we determine (randomly) if the invader will fire
                fire = self.random.randint(0, 20)
                if fire == 2: #hacky way to set it to fire at a low percentage only
                    missile_pos = (invader_pos[0], invader_pos[1] + self.gravity_power)
                    invader.set_missile(missile_pos)

    def fire_turret(self):
        #place the bullet one over the position
        #can only have on bullet on the screen at once
        if len(self.map.get_all_pos(self.BULLET)) == 0:
            bullet_pos = (self.player_pos[0], self.player_pos[1] - 1)
            if self.is_barrier(self.map[bullet_pos]):
              self.map[bullet_pos] = self.decrement_barrier(self.map[bullet_pos])
            elif self.map[bullet_pos] == self.MISSILE:
              self.map[bullet_pos] = self.EMPTY
            else:
              self.map[bullet_pos] = self.BULLET
    def is_barrier(self, c):
      if c == self.BARRIER_1 or c == self.BARRIER_2 or c == self.BARRIER_3 or c == self.BARRIER_4:
        return True
      return False

    def decrement_barrier(self, c):
      if c == self.BARRIER_1:
        return self.EMPTY
      elif c == self.BARRIER_2:
        return self.BARRIER_1
      elif c == self.BARRIER_3:
        return self.BARRIER_2
      elif c == self.BARRIER_4:
        return self.BARRIER_3
      else:
        return self.EMPTY

    def move_invaders(self):
        #determine if we can continue moving in the same direction (nothing will fall off the edge)
        move_down = False
        positions = None
        if self.movement_direction == Direction.RIGHT:
            #sort descending by x value
            positions = sorted([x.get_pos() for x in self.invaders], key=lambda x: x[0], reverse=True)
            print(positions[0])
            if positions[0][0] + 1 >= self.MAP_WIDTH:
                move_down = True
                self.movement_direction = Direction.LEFT

        elif self.movement_direction == Direction.LEFT:
            positions = sorted([x.get_pos() for x in self.invaders], key=lambda x: x[0], reverse=False)
            if positions[0][0] - 1 < 0:
                move_down = True
                self.movement_direction = Direction.RIGHT
            #sort ascending by x value
        if move_down:
            self.move_invaders_down()
            self.move_invaders() #to move one in the new direction after going down
        elif not move_down:
            movement = self.invader_speed
            if self.movement_direction == Direction.LEFT:
                movement *= -1 #go the other direction
            for invader in self.invaders:
                pos = invader.get_pos()
                new_pos = (pos[0] + movement, pos[1])
                # if not self.map[new_pos] == self.BULLET: 
                invader.set_pos(new_pos)
                #else:
                #    #if its a barrier, we need to decrement it
                #    #if its a bullet, we need to remove it
                #    if self.map[new_pos] == self.BULLET:
                #      self.map[new_pos] == self.EMPTY
                #      print("collision with a bullet!")
                #    elif is_barrier(self.map[new_pos]):
                #      self.map[new_pos] = decrement_barrier(self.map[new_pos])
                #    self.invaders.remove(invader)

    def move_invaders_down(self):
        for invader in self.invaders:
            pos = invader.get_pos()
            new_pos = (pos[0], pos[1] + 1)
            if new_pos[1] < self.MAP_HEIGHT:
                # if self.map[new_pos] != self.BULLET: #it wasn't a hit
                invader.set_pos(new_pos)
                #else: #it was hit
                #    self.map[new_pos] = self.EMPTY
                #    self.invaders.remove(invader)

    def move_bullets(self):
        #there should only be one tbh
        #we need to get the list of all invader positions
        invader_positions = [x.get_pos() for x in self.invaders]
        missile_positions = [x.get_missile() for x in self.invaders]
        for pos in sorted(self.map.get_all_pos(self.BULLET), key=lambda x: x[1], reverse=False):
            still_exists = True
            for i in range(0, self.bullet_speed): #0 - 1 so we clear the initial position
                clear = (pos[0], pos[1] - i)
                if clear[1] >= 0 and still_exists:
                    if clear in invader_positions:
                        #we need to find which invader it was and delete it
                        for invader in self.invaders:
                            if invader.get_pos() == clear:
                                self.invaders.remove(invader)
                        still_exists = False
                        self.map[clear] = self.EMPTY
                        self.map[pos] = self.EMPTY
                    elif self.map[clear] == self.MISSILE:
                        #we need to track downt he invader which owns this missile
                        for invader in self.invaders:
                            if invader.get_missile() == clear:
                                invader.set_missile(False)
                        self.map[pos] = self.EMPTY
                        self.map[clear] = self.EMPTY
                        still_exists = False
                    elif self.is_barrier(self.map[clear]):
                        self.map[clear] = self.decrement_barrier(self.map[clear])
                        self.map[pos] = self.EMPTY
                        still_exists = False
                    else:
                        self.map[clear] = self.EMPTY
                        self.map[pos] = self.EMPTY

            new_pos = (pos[0], pos[1] - self.bullet_speed)
            if new_pos[1] >= 0 and still_exists:
                if new_pos in invader_positions:
                    for invader in self.invaders:
                      if invader.get_pos() == new_pos:
                        self.invaders.remove(invader)
                    still_exists = False
                    self.map[clear] = self.EMPTY
                elif new_pos in missile_positions:
                    for invader in self.invaders:
                      if invader.get_missile() == new_pos:
                        invader.set_missile(False)
                    still_exists = False
                    self.map[new_pos] = self.EMPTY
                elif self.is_barrier(self.map[new_pos]):
                    self.map[new_pos] = self.decrement_barrier(self.map[new_pos])
                    still_exists = False
                if still_exists:
                    self.map[new_pos] = self.BULLET
                    self.map[clear] = self.EMPTY
            #if not still_exists:
            #    self.map[new_pos] = self.EMPTY

    def place_objects(self, char, count):
        placed_objects = 0
        while placed_objects < count:
            x = self.random.randint(0, self.MAP_WIDTH - 1)
            # y = self.random.randint(0, self.MAP_HEIGHT - 1)
            y = 0 #put it at the top of the screen

            if self.map[(x, y)] == self.EMPTY:
                self.map[(x, y)] = char
                placed_objects += 1

    def handle_key(self, key):
        self.turns += 1

        self.map[(self.player_pos[0], self.player_pos[1])] = self.EMPTY
        self.map[(self.player_right[0], self.player_right[1])] = self.EMPTY
        self.map[(self.player_left[0], self.player_left[1])] = self.EMPTY
        # if key == "w":
            # self.player_pos[1] -= 1
        # if key == "s":
            # self.player_pos[1] += 1
        if key == "a":
          if self.player_left[0] >= 0:
            self.player_pos[0] -= 1
            self.player_right[0] -= 1
            self.player_left[0] -= 1
        if key == "d":
          if self.player_right[0] < self.MAP_WIDTH:
            self.player_pos[0] += 1
            self.player_right[0] += 1
            self.player_left[0] += 1
        if key == " ":
            self.fire_turret()
        if key == "Q":
            self.running = False
            return

        #TODO: what does this do?
        # self.player_pos[0] %= self.MAP_WIDTH
        # self.player_pos[1] %= self.MAP_HEIGHT

        #move the invaders
        self.move_bullets() #we do hits detection first
        self.move_invaders()
        self.move_missiles(self.gravity_power) #move all drops down 1

        #collision detection #TODO: this detection code doesn't need to exist
        position = self.map[(self.player_pos[0], self.player_pos[1])]
        position_left = self.map[(self.player_left[0], self.player_left[1])]
        position_right = self.map[(self.player_right[0], self.player_right[1])]
        collision = False
        if position == self.MISSILE or position == self.INVADER:
          collision = True
        if position_left == self.MISSILE or position == self.INVADER:
          collision = True
        if position_right == self.MISSILE or position == self.INVADER:
          collision = True

        if collision:
            print("You lost a life!")
            position = self.EMPTY #clear the position
            self.lives -= 1
            #reset to center
            self.player_pos = [self.centerx, (int) (self.MAP_HEIGHT * .99)]
            self.player_right = [self.centerx + 1, (int) (self.MAP_HEIGHT * .99)]
            self.player_left = [self.centerx - 1, (int) (self.MAP_HEIGHT * .99)]
            #remove all missiles
            for invader in self.invaders:
              invader.set_missile(False)
            self.lost_life = True
        self.map[(self.player_pos[0], self.player_pos[1])] = self.PLAYER
        self.map[(self.player_left[0], self.player_left[1])] = self.PLAYER
        self.map[(self.player_right[0], self.player_right[1])] = self.PLAYER

        

        #TODO: lives lost

        #Fire the missiles
        #TODO: uncomment
        self.fire_missiles()

        if len(self.invaders) == 0:
            self.level += 1
            # self.place_drops(self.NUM_OF_DROPS)
            # self.place_pits(self.NUM_OF_PITS_PER_LEVEL)
        #first we clear all the prevoius invaders
        for old_invader in self.map.get_all_pos(self.INVADER):
            self.map[old_invader] = self.EMPTY
        for old_missile in self.map.get_all_pos(self.MISSILE):
            self.map[old_missile] = self.EMPTY

        for invader in self.invaders:
            self.map[invader.get_pos()] = self.INVADER
            if invader.get_missile():
                self.map[invader.get_missile()] = self.MISSILE

    def move_missiles(self, gravity_power): #gravity power is the number of positions a drop will fall per turn
        for invader in self.invaders:
            pos = invader.get_missile()
            if pos:
                #drop each by gravity_power
                new_pos = (pos[0], pos[1] + gravity_power)
                invader.set_missile(False)
                if new_pos[1] < self.MAP_HEIGHT:
                    if self.map[new_pos] == self.BULLET: 
                        self.map[new_pos] = self.EMPTY
                    elif self.map[new_pos] == self.PLAYER:
                        self.life_lost()
                    elif self.is_barrier(self.map[new_pos]):
                        self.map[new_pos] = self.decrement_barrier(self.map[new_pos])
                    else:
                        invader.set_missile(new_pos)
                        self.map[new_pos] = self.MISSILE

                    

                else: #it fell off the map
                    self.missiles_left -= 1


    def is_running(self):
        return self.running
    #TODO: finish this method
    def life_lost(self):
        return 0

    def get_vars_for_bot(self):
        bot_vars = {}

        x_dir, y_dir = self.find_closest_apple(*self.player_pos)

        x_dir_to_char = {-1: ord("a"), 1: ord("d"), 0: 0}
        y_dir_to_char = {-1: ord("w"), 1: ord("s"), 0: 0}

        bot_vars = {"x_dir": x_dir_to_char[x_dir], "y_dir": y_dir_to_char[y_dir],
                    "pit_to_east": 0, "pit_to_west": 0, "pit_to_north": 0, "pit_to_south": 0}

        if self.map[((self.player_pos[0]+1)%self.MAP_WIDTH, self.player_pos[1])] == self.PIT:
            bot_vars["pit_to_east"] = 1
        if self.map[((self.player_pos[0]-1)%self.MAP_WIDTH, self.player_pos[1])] == self.PIT:
            bot_vars["pit_to_west"] = 1
        if self.map[(self.player_pos[0], (self.player_pos[1]-1)%self.MAP_HEIGHT)] == self.PIT:
            bot_vars["pit_to_north"] = 1
        if self.map[(self.player_pos[0], (self.player_pos[1]+1)%self.MAP_HEIGHT)] == self.PIT:
            bot_vars["pit_to_south"] = 1

        return bot_vars

    @staticmethod
    def default_prog_for_bot(language):
        if language == GameLanguage.LITTLEPY:
            return open("apple_bot.lp", "r").read()

    @staticmethod
    def get_intro():
        return open("intro.md", "r").read()

    def get_score(self):
        return self.drops_eaten

    def draw_screen(self, frame_buffer):
        # End of the game
        if self.turns >= self.MAX_TURNS:
            self.running = False
            self.msg_panel.add("You are out of moves.")
        if self.lives == 0:
            self.running = False
            self.msg_panel += ["You lost all your lives"]
        if self.life_lost:
            self.life_lost = False
            self.msg_panel += ["You lost a life"]


        # if not self.running:
                # self.msg_panel += [""+str(self.drops_eaten)+" drops. Good job!"]

        # Update Status
        self.status_panel["Invaders"] = len(self.invaders)
        self.status_panel["Lives"] = str(self.lives) 
        self.status_panel["Move"] = str(self.turns) + " of " + str(self.MAX_TURNS)

        for panel in self.panels:
            panel.redraw(frame_buffer)


if __name__ == '__main__':
    from CYLGame import run
    run(DropDodger)
