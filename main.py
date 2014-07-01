class Game():

    def __init__(self):
        ####
        # properties that stay the same throughout the game
        ####
        self.fruits = {}   # num of each type of fruit possible
        self.targets = {}   # max to win each type
        self.num_types_to_win = 0   # num of types of fruit need to win
        self.width = WIDTH
        self.height = HEIGHT
        
        self.settings = {
            'closeness_margin': 1   # distance +/- 1 irrelevant for choosing dinner
        } 
        
        ####
        # properties that change
        ####
        # state of the game - fixed from game
        self.board = []
        self.current_position = (0,0)
        
        # state of the game - calculated
        self.needed_fruits = {}   # how much of each type of fruit need to get
        self.available_fruits = {}   # how much of each type still on the board
        self.num_types_needed = 0   # how many types of fruit left to win
        self.num_types_won = 0   # how many types of fruit already won
        
        # preferences for next move
        self.pref_fruit_types = []   # list of types of fruit going to try and get
        self.pref_fruit_locations = {}
        
        # next move
        self.dinner_location = (0,0)
        self.next_move = False    

    ####
    # methods required by game
    ####        
    def new_game(self):
        # calculate how many fruits for each type of fruit
        self.init_fruits()
        self.available_fruits = self.fruits.copy()
        self.needed_fruits = self.fruits.copy()
        # calculate target fruits for each type of fruit
        self.init_targets()
        # calculate number of types needed to win
        self.init_num_types_to_win()
        
    def make_move(self):
        # reset move and get fixed game properties
        self.next_move = False
        self.set_current_position()
        self.board = get_board()
        # if on the same place as current closest fruit, pick up
        if self.can_take_fruit():
            return self.move()
        # cannot take, calculate current game state
        self.calculate_game_state()
        # calculate preferences for this move
        self.calculate_move_preferences()
        # calculate which fruit to go for
        self.calculate_dinner_location()
        # move!
        return self.move()

    ####
    # main methods
    ####
    def set_current_position(self):
        self.current_position = (get_my_x(), get_my_y())
    
    def move(self):
        if self.dinner_location:
            self._calculate_direction()
        return self.next_move
    
    def can_take_fruit(self):
        if self.dinner_location and self.current_position == self.dinner_location:
            x,y = self.current_position
            if self.board[x][y] > 0:
                self.next_move = TAKE
                self.dinner_location = False
                return True
        return False

    def calculate_dinner_location(self):
        possible_fruits = self._get_list_of_possible_fruits()
        dinner = {'name': '', 'coords': (0,0), 'distance': 0}
        for fruit in possible_fruits:
            if not dinner['name']:
                dinner = fruit
                continue
            if self.needed_fruits[fruit['name']] < self.needed_fruits[dinner['name']]:
                dinner = fruit
                continue
            if self.needed_fruits[fruit['name']] == self.needed_fruits[dinner['name']]:
                if fruit['distance'] < dinner['distance']:
                    dinner = fruit
        self.dinner_location = dinner['coords']

    def calculate_game_state(self):
        self.num_types_won = 0
        for fruit_name,fruit_total in self.fruits.iteritems():
            mine = get_my_item_count(fruit_name)
            opponent = get_opponent_item_count(fruit_name)
            available = fruit_total - mine - opponent
            # set available fruit
            self.available_fruits[fruit_name] = available
            # count if I've won this type
            if mine >= self.targets[fruit_name]:
                self.num_types_won += 1
            # set needed fruit
            if (mine >= self.targets[fruit_name] or opponent >= self.targets[fruit_name] or 
                    not available):
                self.needed_fruits[fruit_name] = 0
                continue
            self.needed_fruits[fruit_name] = self.targets[fruit_name] - mine
        self.num_types_needed = self.num_types_to_win - self.num_types_won

    def calculate_move_preferences(self):
        # reset preferences
        self.pref_fruit_types = []
        self.pref_fruit_locations = {}
        # set pref fruit types
        self.calculate_pref_fruit_types()
        # set pref fruit locations
        self.calculate_pref_fruit_locations()
    
    def calculate_pref_fruit_types(self):
        needed_fruits = self.needed_fruits.copy()
        for i in range(self.num_types_needed):
            try:
                fruit = min(needed_fruits, key=available_fruits.get)
                if needed_fruits[fruit] == 0:
                    needed_fruits.pop(fruit, None)
                    continue
            except:
                # going to be a tie, no more prefs so pick any available fruit
                fruit = fruit = self._find_any_leftover_fruit()
            self.pref_fruit_types.append(fruit)
    
    
    def calculate_pref_fruit_locations(self):
        for x in range(self.width):
            for y in range(self.height):
                name = self.board[x][y]
                if name in self.pref_fruit_types:
                    position = (x,y)
                    distance = self._distance(self.current_position, position)
                    if distance not in self.pref_fruit_locations:
                        self.pref_fruit_locations[distance] = []
                    self.pref_fruit_locations[distance].append({
                        'name': name, 
                        'coords': position,
                        'distance': distance})
            
    ####
    # helper methods
    ####
    def _calculate_min_stuff_wanted(self, stuff_total):
        if stuff_total % 2 == 0:
            return (stuff_total + 2) / 2
        else:
            return (stuff_total + 1) / 2
            
    def _find_any_leftover_fruit(self):
        for fruit_name,fruit_total in self.available_fruits.iteritems():
            if fruit_total != 0 and fruit_name not in self.pref_fruit_types:
                return fruit_name
                
                
    def _distance(self, p0, p1):
        """ difference in x + difference in y to calculate distance """
        return abs(p0[0] - p1[0]) + abs(p0[1] - p1[1])

    def _get_list_of_possible_fruits(self):
        smallest_distance = min(self.pref_fruit_locations)
        possible_fruits = self.pref_fruit_locations[smallest_distance]
        # add others based on closeness margin
        for i in range(self.settings['closeness_margin']):
            new_distance = smallest_distance + i + 1
            if new_distance in self.pref_fruit_locations:
                possible_fruits += self.pref_fruit_locations[new_distance]
        return possible_fruits
        
    def _calculate_direction(self):
        mx,my = self.current_position
        tx,ty = self.dinner_location
        trace('current position: ' + str(self.current_position))
        trace('dinner location: ' + str(self.dinner_location))
        if mx > tx:
            self.next_move = WEST
            return
        if mx < tx:
            self.next_move = EAST
            return
        if my > ty:
            self.next_move = NORTH
            return
        if my < ty:
            self.next_move = SOUTH
            
    ####
    # init methods
    ####
    def init_fruits(self):
        for fruit_type in range(get_number_of_item_types()):
            fruit_count = get_total_item_count(fruit_type+1)
            self.fruits[fruit_type+1] = fruit_count
            
    def init_num_types_to_win(self):
        self.num_types_to_win = self._calculate_min_stuff_wanted(len(self.fruits))

    def init_targets(self):
        for fruit_name,fruit_count in self.fruits.iteritems():
            fruit_target = self._calculate_min_stuff_wanted(fruit_count)        
            self.targets[fruit_name] = fruit_target
    
    ####
    # broken random direction
    ####    
    def pick_random_direction(self):
        possible_directions = [NORTH, SOUTH, EAST, WEST]
        if self.current_position[0] == 0:
            possible_directions.remove(WEST)
        if self.current_position[0] == self.width:
            possible_directions.remove(EAST)
        if self.current_position[1] == 0:
            possible_directions.remove(NORTH)
        if self.current_position[1] == self.height:
            possible_directions.remove(SOUTH)
        # cannot import to pick random, so just pick first
        return possible_directions[0]
       

GAME = Game()
                
def make_move():
    return GAME.make_move()
    
def new_game():
    GAME.new_game()
