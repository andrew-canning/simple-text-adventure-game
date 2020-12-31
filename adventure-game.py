import functools
from random import choice, randrange
from itertools import count
from copy import copy
from time import sleep

debug = True

class RoomSize:
    def __init__(self, height: int, width: int):
        self.height = height
        self.width = width

    def __str__(self):
        return str((self.width, self.height))


class RoomType:
    def __init__(self, type):
        if type == "normal" or type == "starting" or type == "final":
            self.type = type
        else:
            raise TypeError("RoomType: type: must be [ 'normal', 'starting', or 'final']")


class Room:
    next_room_id = count(0)

    def __init__(self, room_name: str, room_size: RoomSize, room_type: RoomType, position=(), chores=""):
        self.id = next(self.next_room_id)
        self.name = room_name               # a name of the room
        self.size = room_size               # a room type object
        self.type = room_type               # either normal, starting, or final
        self.position = position            # tuple room position
        self.connections = {}               # a dictionary of directions and room objects
        self.chores = []
        if chores:
            self.chores.append(chores)      # a list of chore objects

    def __str__(self):
        return'''
            Room id: {id}
            - name: {name}
            - chore: {chores}
            - size: h: {height}, w:{width}
            - type: {type}
            - position: {position}
            - connecting rooms: {connections}'''.format(
            id=self.id,
            name=self.name,
            chores=self.chores,
            height=self.size.height,
            width=self.size.width,
            type=self.type.type,
            position=self.position,
            connections=self.get_str_connections(self.connections)
        ).replace("            ", "")

    # to order rooms
    @functools.total_ordering
    def __lt__(self, other):
        if not isinstance(other, Room):
            return NotImplemented
        return self.id < other.id

    def do_chore(self, chore_name):
        return self.chores.pop(chore_name)

    def get_str_connections(self, conn_dict):
        string_conn = {}
        for k, v in conn_dict.items():
            string_conn[k.name] = v
        return string_conn


class RoomGrid:
    # upper left is [0][0] of grid
    # spaces are either a room or a list
    # list would be four booleans
    # [(left), (right), (top), (bottom)]
    # this will show where the neighbors are
    left, right, top, bottom = 0, 1, 2, 3

    def __init__(self, debug=False):
        if debug:
            self.debug = True
            print("\nInitializing RoomGrid class...\n"
                  "\n   With debug on, you can watch the game place all the rooms(semi-randomly),\n"
                  "one at a time. First it checks to see if the plot is free, then places the \n"
                  "room on the grid and then marks its neighbor(s).\n\n"
                  "   It's placement technique could be improved as it only knows how to \n"
                  "start with the upper left corner of the room; it cannot, for example,\n"
                  "find a corner where the bottom and right spots are taken and build to the\n"
                  "upper left.\n\n")
            input("\nPress 'Enter'/'Return' to continue")
        else:
            self.debug = False
        # a space that is not a room is represented with [False, False, False, False]
        # each boolean is a direction, specified in the class variable section
        self.room_grid = [[self.new_space()]]

        # we would like rooms so that that are more likely to be closely clustered
        # do this will track where current rooms are placed
        # will be a list of coordinates
        self.heat_map = []

    def __str__(self):
        """
        prints a grid of where the rooms (first letter of room)
        integers represent how many rooms are adjacent to this spot
        example:
        0 1 1 1 1 1 1 1 0
        1 m k k g d d M 1
        1 b k k G d d M 1
        1 b 3 2 G 2 1 1 0
        1 s s 1 1 0 0 0 0
        0 1 1 0 0 0 0 0 0
        """
        print_str = ""
        for row in range(len(self.room_grid[0])):
            for column in self.room_grid:
                space = column[row]
                if type(space) == Room:
                    print_str += space.name[0] + " "
                else:
                    print_str += str(sum(column[row])) + " "
            print_str += "\n"
        return print_str

    def new_space(self):
        return [False, False, False, False]

    # grow grid functions will increase grid side in a direction when the game needs
    #   more space to place rooms or mark neighbors
    def grow_grid_up(self):
        for column in self.room_grid:
            column.insert(0, self.new_space())

    def grow_grid_down(self):
        for column in self.room_grid:
            column.append(self.new_space())

    def grow_grid_right(self):
        self.room_grid.append([self.new_space() for space in range(len(self.room_grid[0]))])

    def grow_grid_left(self):
        self.room_grid.insert(0, [self.new_space() for space in range(len(self.room_grid[0]))])

    # here we are marking a space in a direction, to let them know a adjacent room exists
    # so we mark a space on top of the room with a "bottom neighbor"
    def mark_top_neighbor(self, space: list):
        # else mark the "bottom" boolean as True (because room is to bottom of this space)
        self.room_grid[space[0]][space[1] - 1][self.bottom] = True

    def mark_bottom_neighbor(self, space: list):
        # else mark the "top" boolean as True (because room is to top of this space)
        self.room_grid[space[0]][space[1] + 1][self.top] = True

    def mark_left_neighbor(self, space: list):
        # else make the "right" boolean as True (because room is to right of this space)
        self.room_grid[space[0] - 1][space[1]][self.right] = True

    def mark_right_neighbor(self, space: list):
        # else mark the "left" boolean as True (because room is to left of this space)
        self.room_grid[space[0] + 1][space[1]][self.left] = True

    # Currently there is only one deployment direction;
    # starting with upper left corner of room and looking to
    # see if it can place it in a down right direction.
    # Direction #4
    def find_placement_direction(self, open_space):
        # find possible placement directions using graph quadrant numbers
        if type(open_space) == Room:
            raise TypeError("SpaceType: type: must be a space not taken by a room")
        if type(open_space) != list:
            raise TypeError("SpaceType: type: must be a list")

        directions = []

        if not open_space[self.top] and not open_space[self.right]:
            directions.append(1)

        if not open_space[self.top] and not open_space[self.left]:
            directions.append(2)

        if not open_space[self.bottom] and not open_space[self.left]:
            directions.append(3)

        if not open_space[self.bottom] and not open_space[self.right]:
            directions.append(4)

        return directions

    # Before with modify the grid we need to make sure the space is free for the room
    def confirm_placement_zone(self, space: list, direction: int, size: RoomSize):
        free = True
        if direction == 4:
            for w_unit in range(size.width):
                for h_unit in range(size.height):
                    # if space is outside of grid it is free
                    if w_unit + space[0] > len(self.room_grid) - 1:
                        continue
                    if h_unit + space[1] > len(self.room_grid[0]) - 1:
                        continue
                    # if space is not a room it is free
                    if type(self.room_grid[w_unit + space[0]][h_unit + space[1]]) == Room:
                        free = False
                        break
        else:
            free = False

        return free

    # Update the list that tracks where we can and want to place
    # our next room
    def update_grid_heat_map(self):
        # The heat map will be used to randomly select our next room.
        # We want to have the rooms be clustered together so we will
        #    increase the chances of places a room next to multiple rooms.
        # We will use a system similar to mine sweeper; so empty spaces next
        #    to 2 rooms would get a "2". Or in this case two entries in our list.
        cluster_weight = 2
        # list of tuples (coordinates on grid)
        self.heat_map = []
        for c_index, column in enumerate(self.room_grid):
            for s_index, space in enumerate(column):
                if type(space) is not Room:
                    for x in range(sum(space) ** cluster_weight):
                        self.heat_map.append((c_index,s_index))

    # this is the function responsible for finding a spot for a room to be placed on the grid
    def place_room(self, room: Room, space=[]):
        # TODO split this into shorter functions
        # a list of rooms adjacent to this room after placement
        total_neighbors = {}
        # a direction to deploy room square by square
        chosen_direction = 0
        if self.debug: print("\n---------------------------")
        if self.debug: print("\nPlacing room:", room.name)
        if self.debug: print("With size:", room.size)
        # if room(s) have already been placed
        if self.heat_map and not space:
            if self.debug: print("Trying random placement")
            tmp_heat_map = copy(self.heat_map)
            # while there are space left to try
            spot_found = False
            while len(tmp_heat_map) > 0 and not spot_found:
                # pick a random space, weighted for multiple neighbors
                chosen_space = tmp_heat_map.pop(randrange(len(tmp_heat_map)))
                if self.debug: print("Candidate Space:", chosen_space, end=" -- ")

                # if the room larger than size (1,1) we need to make sure the whole room fits
                if room.size.width > 1 or room.size.height > 1:
                    directions = self.find_placement_direction(self.room_grid[chosen_space[0]][chosen_space[1]])
                    # lets just keep it simple and deploy in down right direction
                    if 4 not in directions or not directions:
                        if self.debug: print("No free direction")
                        continue
                    else:
                        for direction in directions:
                            # check to see if we can place the room for the given direction
                            if self.confirm_placement_zone(chosen_space, direction, room.size):
                                if self.debug: print("Free ")
                                chosen_direction = direction
                                space = chosen_space
                                spot_found = True
                                break
                # if the room is size (1,1) it will fit and any spot
                else:
                    if self.debug: print("Free ")
                    space = chosen_space
                    chosen_direction = 4
                    spot_found = True
                    break
            # it's impossible that we don't find any open spaces, so something is wrong
            if not chosen_direction and space:
                raise RuntimeError("Could not find a place to put room")
        # if we hard coded a space
        elif space:
            pass

        # if no space was provided and we don't have a heat map
        # most likely when this is the first room
        else:
            space = [0, 0]

        for w_unit in range(room.size.width):
            # If we need to add another column to fit room.
            # Since currently we only place rooms from top left to bottom right
            #  we only need to grow the grid right and down during placement
            if len(self.room_grid) - 1 < w_unit + space[0]:
                self.grow_grid_right()
            for h_unit in range(room.size.height):
                if self.debug: print("\nPlacing room cell x{}, y{}".format(w_unit + 1 , h_unit + 1))
                this_space_x = w_unit + space[0]
                this_space_y = h_unit + space[1]
                if len(self.room_grid[0]) - 1 < h_unit + space[1]:
                    self.grow_grid_down()
                self.room_grid[this_space_x][this_space_y] = room
                space_adjustment, neighbors = self.place_neighbors(space=[this_space_x, this_space_y], this_room=room)
                space = [space[0] + space_adjustment[0], space[1] + space_adjustment[1]]
                total_neighbors.update(neighbors)
        # Once the room is placed and the neighbors are marked we need to update the placement list
        self.update_grid_heat_map()

        # lets connect  some of the neighbors to this room to travel
        room.connections.update(total_neighbors)
        opposite_direction = {"north": "south", "south": "north", "east": "west", "west": "east"}
        if self.debug: print("Adding neighbors to existing rooms:")
        for k, v in total_neighbors.items():
            k.connections.update({room: opposite_direction[v]})
            if self.debug: print("Giving", k.name, "'", room.name, opposite_direction[v],"'")

    def place_neighbors(self, space: list, this_room: Room):
        # TODO split this into shorter functions
        # [(left), (right), (top), (bottom)]
        left, right, top, bottom = 0, 1, 2, 3
        # when you prepend grid you need to move target space
        space_adjustment = [0, 0]
        neighboring_rooms = {}
        if self.debug: print("Start adding neighbors")
        if self.debug: print("Coords:", space[0], space[1])
        if self.debug: print(self.__str__())

        # mark left neighbor
        # if this is the left most space grow grid left
        if self.debug: print("Mark left neighbor")
        target_space = self.room_grid[space[0] - 1][space[1]]
        if space[0] == 0:
            self.grow_grid_left()
            # move coord over after growing grid with prepend
            space[0] += 1
            space_adjustment[0] += 1
            self.mark_left_neighbor(space)
        # if this neighbor is a room, add to room neighbors
        elif type(target_space) == Room:
            if target_space is not this_room:
                neighboring_rooms[target_space] = "west"
        # else make the "right" boolean as True (because room is to right of this space)
        else:
            self.mark_left_neighbor(space)
        if self.debug: print(self.__str__())


        if self.debug: print("Mark right neighbor")
        # mark right neighbor
        # if this is the right most space, grow grid right
        target_space = self.room_grid[space[0] + 1][space[1]] if len(self.room_grid) > space[0] + 1 else False
        if space[0] == len(self.room_grid) - 1:
            self.grow_grid_right()
            self.mark_right_neighbor(space)
        # if this neighbor is a room, skip
        elif type(target_space) == Room:
            if target_space is not this_room:
                neighboring_rooms[target_space] = "east"
        # else mark the "left" boolean as True (because room is to left of this space)
        else:
            self.mark_right_neighbor(space)
        if self.debug: print(self.__str__())


        if self.debug: print("Mark bottom neighbor")
        # mark bottom neighbor
        # if this is the bottom most spot grow grid down
        target_space = self.room_grid[space[0]][space[1] + 1] if len(self.room_grid[0]) > space[1] + 1 else False
        if space[1] == len(self.room_grid[0]) - 1:
            self.grow_grid_down()
            self.mark_bottom_neighbor(space)
        # if this neighbor is a room, skip
        elif type(target_space) == Room:
            if target_space is not this_room:
                neighboring_rooms[target_space] = "south"
        # else mark the "top" boolean as True (because room is to top of this space)
        else:
            self.mark_bottom_neighbor(space)
        if self.debug: print(self.__str__())


        if self.debug: print("Mark top neighbor")
        # mark top neighbor
        # if this is the top most spot grow grid up
        target_space = self.room_grid[space[0]][space[1] - 1]
        if space[1] == 0:
            self.grow_grid_up()
            # move coord over after growing grid with prepend
            space[1] += 1
            space_adjustment[1] += 1
            self.mark_top_neighbor(space)
        # if this neighbor is a room, skip
        elif type(target_space) == Room:

            if target_space is not this_room:
                neighboring_rooms[target_space] = "north"
        # else mark the "bottom" boolean as True (because room is to bottom of this space)
        else:
            self.mark_top_neighbor(space)
        if self.debug: print(self.__str__())

        if self.debug: print("Neighbor object for this cell:")
        if self.debug: print(this_room.get_str_connections(neighboring_rooms))
        return space_adjustment, neighboring_rooms


class Game:

    def __init__(self, room_size_pool: dict, room_chore_pool: dict, num_rooms=None, debug=False):
        print("\nWelcome to a text based adventure game!\n"
              "Starting game Setup:\n")
        if debug:
            self.debug = True
            print("###############################\n"
                  "#                             #\n"
                  "#     Debug Mode Enabled      #\n"
                  "#                             #\n"
                  "###############################\n"
                  )
        else:
            self.debug = False
        self.starting_room: Room
        self.final_room: Room
        self.current_room: Room
        self.room_pool = []
        self.room_grid: RoomGrid
        self.num_rooms = num_rooms
        self.room_size_pool = room_size_pool
        self.room_chore_pool = room_chore_pool
        self.initialized_chores = []
        self.collected_chores = []
        self.all_objectives_completed = False
        self.game_over = False
        self.new_map()
        while True:
            self.main_loop()
            self.play_again()

    def new_map(self):
        while not self.num_rooms:
            try:
                num_rooms = input("How many rooms would you like to play with? (default: 8):")
                num_rooms = int(num_rooms) if num_rooms else 8
            except:
                print("Enter an integer!")
                continue
            if not num_rooms:
                num_rooms = 8
            if num_rooms < 3:
                print("Need atleast 3 rooms to play!")
                continue
            elif num_rooms > len(self.room_chore_pool) + 2:
                print("You can't have more rooms that your room pool + 2")
                continue
            else:
                self.num_rooms = num_rooms
        self.room_pool = []
        # form new rooms from our list of possible room sizes and chores
        self.make_rooms(self.room_size_pool, self.room_chore_pool)
        # place each of our new rooms on the grid to form our play area
        for this_room in self.room_pool:
            self.room_grid.place_room(this_room)
        if self.debug: [print("---------------------------", x) for x in self.room_pool]
        if self.debug: print("---------------------------")

    def make_rooms(self, room_sizes: dict, chore_pool: dict):
        # # form new rooms from our list of possible room sizes and chores
        self.room_grid = RoomGrid(debug=self.debug)
        self.initialized_chores = []
        for room in range(self.num_rooms):
            room_size = choice(list(room_sizes.values()))
            # first room is our starting area
            if room == 0:
                room_type = RoomType("starting")
                chore = None
                name = "man cave"
            # last room is our final room
            elif room == (self.num_rooms - 1):
                room_type = RoomType("final")
                chore = None
                name = "Master bedroom"
            # Every other room is a normal room with a chore
            else:
                room_type = RoomType("normal")
                name = choice(list(chore_pool.keys()))
                chore = chore_pool[name]
                del chore_pool[name]
                self.initialized_chores.append(chore)
            new_room = Room(room_name=name, room_size=room_size, position=(0, 0), chores=chore, room_type=room_type)
            # mark our starting and final rooms so the game knows where to start and end
            if room == 0:
                self.starting_room = new_room
            if room == (self.num_rooms - 1):
                self.final_room = new_room

            self.room_pool.append(new_room)
        if self.debug: print("Initialized chore list:\n", self.initialized_chores)

    def print_room_prompt(self, room: Room, doors: dict):
        # main output on every game loop
        print("--------------------------------")
        print("You are currently in the {}.".format(room.name))
        print("What would you like to do?\n")
        visible_chores = []
        for chore in room.chores:
            if chore not in self.collected_chores:
                visible_chores.append(chore)
        if len(visible_chores) > 1:
            print("Chores to be done:")
        elif len(visible_chores) == 1:
            print("Chore to be done:")
        else:
            print("No chores to do here! Where to next?")
        for chore in visible_chores:
            print("-", chore)
        door_list = {}

        print("\nDoors I can see:")
        for direction, doors in doors.items():
            if len(doors) > 1:
                for i, door in enumerate(doors):
                    if self.debug:
                        room_name_hint = "(debug mode hint: {})".format(door.name)
                    else:
                        room_name_hint = ""
                    print("- {}: Door {} {}".format(direction, i + 1, room_name_hint))
            else:
                if self.debug:
                    room_name_hint = "(debug mode hint: {})".format(doors[0].name)
                else:
                    room_name_hint = ""
                print("- {} {}".format(direction, room_name_hint))

    def get_doors(self, room: Room):
        # return a dictionary of directions to walk in
        door_list = {}
        for k, v in sorted(room.connections.items()):
            if not door_list.get(v):
                door_list[v] = [k]
            else:
                door_list[v].append(k)
        return door_list

    def walk(self, doors, selection: list):
        doors_in_direction = sorted(doors.get(selection[1])) if doors.get(selection[1]) else False
        # "walk ikujagsdikuhg"
        if not doors_in_direction:
            print("\nPick a correct direction!\n")
        # "walk north"
        elif len(doors_in_direction) == 1 and len(selection) == 2:
            print("\nWalking {}!\n".format(selection[1]))
            self.current_room = doors[selection[1]][0]
        # "walk north" but more than one door north
        elif len(doors_in_direction) > 1 and len(selection) == 2:
            print("\nPick a door number. More than 1 option walking {0}!\n"
                  "Example: 'walk {0} to door 1'\n".format(selection[1]))

        # "walk into space!"
        elif len(doors_in_direction) == 0:
            print("\nPlease pick a correct destination!\n")
        # "walk north to Door 1"
        elif len(selection) >= 5:
            # User puts a door number that's negative
            if int(selection[4]) < 1:
                print("\nNo negative or zero door numbers!\n")
            # correct input
            elif int(selection[4]) <= len(doors_in_direction):
                print("\nWalking {}!\n".format(selection[1]))
                self.current_room = doors_in_direction[int(selection[4]) - 1]
            # if you pick a door number thats out of range
            elif int(selection[4]) > len(doors_in_direction) or int(selection[4]) < 1:
                if len(doors_in_direction) == 1:
                    article = "is"
                    noun = "door"
                else:
                    article = "are"
                    noun = "doors"
                print("\nDoor {} doesn't exist, "
                      "there {} only {} {} in that direction!\n"
                      .format(selection[4], article, len(doors_in_direction), noun))
            # Bad input
            else:
                print("\nPlease pick a correct room name!\n")

        # some random input condition the code couldn't deal with
        else:
            print("Errr try again")

    def do_chore(self, room: Room, selection: str):
        str_selection = " ".join(selection)
        if str_selection in room.chores:
            # take a chore from the room and put it in your collected chores
            self.collected_chores.append(str_selection)
            print("'{}' -- done!".format(" ".join(selection[1:])))
        else:
            print("Select a chore in this room! (or fix your spelling!)")

    def end_game_conditions(self):
        if self.all_objectives_completed:
            self.game_over = True
            print("******************************************\n"
                  "*                                        *\n"
                  "*                YOU WIN                 *\n"
                  "*                                        *\n"
                  "******************************************\n")
            print("After a good day's work you sleep in your bed.")
        else:
            self.game_over = True
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
                  "X                                        X\n"
                  "X                YOU LOSE                X\n"
                  "X                                        X\n"
                  "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n")
            print("You are sleeping on the couch!")

    def main_loop(self):
        # main game logic once the game is initialized
        self.current_room = self.starting_room
        print("\n##################################################")
        print("#                   Welcome!                     #")
        print("#  Do all the chores so that you don't have to   #")
        print("#              sleep on the couch!               #")
        print("##################################################\n")
        print("***** If you show up in the Master bedroom *****\n"
              "   ***** with incomplete tasks you lose!*****\n")
        print("You can either walk somewhere or do a chore. Example syntax:")
        print("Chores (please use verb 'go'):\n 'go clean the table'")
        print("Walking (please use verb 'walk'):")
        print(" 'walk north' (when there is only on door in a direction)")
        print(" 'walk north to door 1' (when there are multiple doors in the same direction)\n")
        print("You can also reset the game or get a new layout with: 'reset'\n")
        if self.debug: print("Note: Room names on doors are revealed because debug is on.")
        input("\nPress 'Enter'/'Return' to continue")
        print("Start!\n")
        while not self.game_over:
            sleep(1)
            # If you did all the chores, print it out!
            if not self.all_objectives_completed and \
                    sorted(self.collected_chores) == sorted(self.initialized_chores):
                print("\n********************************\n"
                      "** You've done all the chores **\n"
                      "********************************\n")
                self.all_objectives_completed = True
                sleep(1)
            if self.current_room.type.type == "final":
                self.end_game_conditions()
                break
            doors = self.get_doors(self.current_room)
            self.print_room_prompt(self.current_room, doors)
            selection = input("\nInput:").lower().split()
            # if input is empty
            if len(selection) == 0:
                print("\nEnter anything!\n")
                continue
            # "go make the bed"
            if "go" in selection[0]:
                self.do_chore(self.current_room, selection)

            elif "walk" in selection[0]:
                self.walk(doors, selection)
            # "Jump the shark!"
            elif selection[0] == "reset" and len(selection) == 1:
                while True:
                    prompt = input("Are you sure you want to reset the game?(y/n)")
                    if prompt == 'y':
                        self.game_over = True
                        break
                    elif prompt == 'n':
                        break
                    else:
                        print("bad input, enter 'y' or 'n'")
            else:
                print("\nI couldn't understand you. Try again!\n")

    def play_again(self):
        while True:
            play_again = input("Play again? (y/n):")
            if play_again == 'n':
                print("--------------------------------")
                print("Thanks for playing!")
                print("See you soon!")
                print("--------------------------------")
                exit(0)
            elif play_again == 'y':
                same_level = input("Would you like to play on the same layout? (y/n):")
                if same_level == 'y':
                    self.collected_chores = []
                    self.current_room = self.starting_room
                    self.all_objectives_completed = False
                    self.game_over = False
                    break
                elif same_level == 'n':
                    self.all_objectives_completed = False
                    self.num_rooms = None
                    self.new_map()
                    self.collected_chores = []
                    self.game_over = False
                    break
                else:
                    print("bad input, enter 'y' or 'n'")

            else:
                print("bad input, enter 'y' or 'n'")


room_size_pool = {
    "small_room": RoomSize(1, 1),
    "tall_room": RoomSize(2, 1),
    "wide_room": RoomSize(1, 2),
    "big_room": RoomSize(2, 2)
}
room_chore_pool = {
    "kitchen": "go empty the dishwasher",
    "dinning room": "go clean the table",
    "living room": "go vacuum the carpet",
    "bathroom": "go wash the bathtub",
    "guestroom": "go make the bed",
    "Garage": "go organize the tools",
    "study": "go arrange the books",
    "office": "go sharpen the pencils"
}

Game(room_size_pool=room_size_pool, room_chore_pool=room_chore_pool, debug=debug)


