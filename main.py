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
        
        # settings
        self.pick_priority = ['yummy', 'needed', 'distance', 'name']   # fruit choosing decision
        
        ####
        # properties that change
        ####
        # state of the game - fixed from game
        self.board = []
        self.current_position = (0,0)
        self.opponent_position = (0,0)
        
        # state of the game - calculated
        self.needed_fruits = {}   # how much of each type of fruit need to get
        self.available_fruits = {}   # how much of each type still on the board
        self.num_types_needed = 0   # how many types of fruit left to win
        self.num_types_won = 0   # how many types of fruit already won
        
        # preferences for next move
        self.pref_fruit_types = []   # list of types of fruit going to try and get
        self.pref_fruit_with_attributes = []   # all fruit looking at with  additional data
        
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
        self.opponent_position = (get_opponent_x(), get_opponent_y())
    
    def move(self):
        if self.dinner_location:
            self._calculate_direction()
        trace('num types: ' +str(self.num_types_needed))
        trace('pref types: '+str(self.pref_fruit_types))
        trace('needed: '+str(self.needed_fruits))
        return self.next_move
    
    def can_take_fruit(self):
        if self.dinner_location and self.current_position == self.dinner_location:
            x,y = self.current_position
            if self.board[x][y] > 0:
                trace('DELICIOUS FRUIT OM NOM NOM NOM')
                self.next_move = TAKE
                self.dinner_location = False
                return True
        return False
    
    def calculate_dinner_location(self):
        dinner = {
            'name': '', 
            'position': (0,0), 
            'distance': 0, 
            'opp_distance': 0, 
            'needed': 0,
            'available': 0}
        for fruit in self.pref_fruit_with_attributes:
            if not dinner['name']:
                dinner = fruit
                continue
            dinner = self._decide_most_delicious(dinner, fruit)
        trace('DINNER LOCATED: ' + str(dinner))
        self.dinner_location = dinner['position']

    def calculate_game_state(self):
        """ calculates fruits available, fruits needed, and number of fruit types needed """
        self.num_types_won = 0
        additional_types_needed = 0
        for fruit_name,fruit_total in self.fruits.iteritems():
            mine = get_my_item_count(fruit_name)
            opponent = get_opponent_item_count(fruit_name)
            available = fruit_total - mine - opponent
            # set available fruit
            self.available_fruits[fruit_name] = available
            # count if I've won this type
            if mine >= self.targets[fruit_name]:
                self.num_types_won += 1
            # count if opponent has almost won a type
            if self._one_fruit_left_to_win(fruit_name, opponent):
                additional_types_needed = 1
            # set needed fruit
            if (mine >= self.targets[fruit_name] or opponent >= self.targets[fruit_name] or 
                    not available or self._opponent_about_to_win_type(fruit_name, opponent)):
                self.needed_fruits[fruit_name] = 0
                continue
            self.needed_fruits[fruit_name] = self.targets[fruit_name] - mine
        self.num_types_needed = ((self.num_types_to_win - self.num_types_won) +
            additional_types_needed)

    def calculate_move_preferences(self):
        # reset preferences
        self.pref_fruit_types = []
        self.pref_fruit_with_attributes = []
        # set pref fruit types
        self.calculate_pref_fruit_types()
        # set pref fruit locations
        self.calculate_pref_fruit_with_attributes()
    
    def calculate_pref_fruit_types(self):
        """ calculate the types of fruit we want """
        needed_fruits = self.needed_fruits.copy()
        for i in range(self.num_types_needed):
            try:
                fruit = min(needed_fruits, key=available_fruits.get)
                if needed_fruits[fruit] == 0:
                    needed_fruits.pop(fruit, None)
                    continue
            except:
                # going to be a tie, no more prefs so pick any available fruit type
                fruit = self._find_any_leftover_fruit()
            self.pref_fruit_types.append(fruit)
    
    def calculate_pref_fruit_with_attributes(self):
        """ create list of fruit we possibly want with useful attributes """
        for x in range(self.width):
            for y in range(self.height):
                name = self.board[x][y]
                if name in self.pref_fruit_types:
                    position = (x,y)
                    distance = self._distance(self.current_position, position)
                    opp_distance = self._distance(self.opponent_position, position)
                    self.pref_fruit_with_attributes.append({
                        'name': name, 
                        'position': position,
                        'distance': distance,
                        'opp_distance': opp_distance,
                        'needed': self.needed_fruits[name],
                        'available': self.available_fruits[name]})
            
    ####
    # fruit-picking methods
    ####
    def _pick_lowest(self, f0, f1, iteration):
        """ go through pick_priority until we have a winner! """
        try:
            key = self.pick_priority[iteration]
        except:
            # nothing between them, more AI in future, for now pick f0
            return f0
        if f0[key] == f1[key]:
            return self._pick_lowest(f0, f1, iteration + 1)
        return min((f0,f1), key=lambda x:x[key])
    
    def _calculate_nearby_fruit_factor(self, fruit):
        """ look at nearby fruit and assign weight to each """
        search_area = 10
        empty_position_weight = 30
        fruits_nearby = 0
        weight_offset = 0
        for x,y in self._nearby_positions(fruit['position'], search_area):
            if self.board[x][y] in self.pref_fruit_types:
                fruits_nearby += 1
                name = self.board[x][y]
                weight_offset += (self._distance(fruit['position'], (x,y)) + 
                    self.needed_fruits[name] + self.available_fruits[name])
        weight = ((self._max_num_nearby_positions(search_area) - fruits_nearby) * 
            empty_position_weight) + weight_offset
        return weight/100
    
    def _calculate_fruit_deliciousness(self, fruit):
        """ calculate the 'yummy' of the fruit """
        # common adjustments
        needed = fruit['needed']
        available = fruit['available']
        nearby_factor = self._calculate_nearby_fruit_factor(fruit)
        distance = fruit['distance'] + 1
        
        # special cases
        if not fruit['needed']:
            needed = 30   # random high number to push up yumminess
        if not fruit['opp_distance']:
            needed = 15   # opp currently on this fruit, probably get so ignore
        if available == 1:
            available = 0.01

        # add final numbers to object for debugging
        fruit['yummy_calc'] = (needed, available, nearby_factor, distance)
        fruit['nearby_factor'] = self._calculate_nearby_fruit_factor(fruit)
        # calculation
        return (distance * 2.5) + (needed * 1) + (available * 1.2) + (nearby_factor * 1.2)
    
    def _decide_most_delicious(self, f0, f1):
        f0['yummy'] = self._calculate_fruit_deliciousness(f0)
        f1['yummy'] = self._calculate_fruit_deliciousness(f1)
        trace('comparing: ' + str(f0) +  ' || vs || ' + str(f1))
        return self._pick_lowest(f0, f1, 0)

    ####
    # helper methods
    ####
    def _max_num_nearby_positions(self, area):
        """ assuming no board edges, maximum number of nearby positions """
        total = 0
        for i in range(area):
            total += (i+1) * 4
        return total
    
    def _nearby_positions(self, position, area):
        """ generator to calculate nearby valid positions """
        for x in range(position[0] - area, position[0] + area + 1):
            for y in range(position[1] - area, position[1] + area + 1):
                if (x < 0 or y < 0) or (x,y) == position or (x >= self.width or y >= self.height):
                    continue
                if abs(position[0] - x) + abs(position[1] - y) > area:
                    continue
                yield (x,y) 
    
    def _opponent_about_to_win_type(self, fruit_name, count):
        """ returns true if opponent can take the fruit on their next go and win this type """
        fruit_at_opp = self.board[self.opponent_position[0]][self.opponent_position[1]]
        if fruit_at_opp == fruit_name and self._one_fruit_left_to_win(fruit_name, count):
            trace('opp about to win')
            return True
        return False
    
    def _one_fruit_left_to_win(self, fruit_name, count):
        """ returns true if only 1 (or 0.5) more fruit is required to win the type """
        to_go = self.targets[fruit_name] - count
        if (to_go > 0) and (to_go <= 1) and (to_go <= self.available_fruits[fruit_name]):
            trace('1 to go')
            return True
        return False    
    
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
        
    def _calculate_direction(self):
        mx,my = self.current_position
        tx,ty = self.dinner_location
        trace('current position: ' + str(self.current_position))
        trace('dinner position: ' + str(self.dinner_location))
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
            return
        # actually, dinner is here! convenient! :D
        self.next_move = TAKE
            
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
    # broken random direction - need to fix without import
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
