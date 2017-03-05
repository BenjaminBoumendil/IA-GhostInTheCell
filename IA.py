import sys
import math
import time
from operator import itemgetter

ROUND_COUNT = 0
FREE_BOMB_LAUNCHING_ROUND_COUNT = 150
RANGE_FOR_BOOST_TURTLE = 3
RANGE_FOR_BOOST_PVP = 6

FACTORY_COUNT = int(input())  # the number of factories
link_count = int(input())  # the number of links between factories
link_array = []
for i in range(link_count):
    sub_array = [0, 0, 0]
    # factory1, factory2, range
    sub_array[0], sub_array[1], sub_array[2] = [int(j) for j in input().split()]
    link_array.append(sub_array)


class Entity:
    """
    Base class for game entity
    """
    owner = None

    def __str__(self):
        return ", ".join("%s: %s" % item for item in vars(self).items())

class BombEntity(Entity):
    """
    Represent each bomb
    """
    factory_id_src = None
    factory_id_dest = None
    round_before_arrival = None

    def __init__(self, owner, factory_id_src, factory_id_dest, round_before_arrival):
        self.owner = owner
        self.factory_id_src = factory_id_src
        self.factory_id_dest = factory_id_dest
        self.round_before_arrival = round_before_arrival

class TroopEntity(Entity):
    """
    Represent each Troop
    """
    factory_id_src = None
    factory_id_dest = None
    cyborgs_count = None
    round_before_arrival = None
    
    def __init__(self, owner, factory_id_src, factory_id_dest, cyborgs_count, round_before_arrival):
        self.owner = owner
        self.factory_id_src = factory_id_src
        self.factory_id_dest = factory_id_dest
        self.cyborgs_count = cyborgs_count
        self.round_before_arrival = round_before_arrival

class FactoryEntity(Entity):
    """
    Represent each Factory
    """
    factory_id = None
    cyborgs_count = None
    production = None
    factory_near = None
    next_move = None
    colony_in_progress = False
    
    def is_win(self, troop_list, owner):
        """
        Return True if friendly troop coming on self is greater than cyborgs_count
        """
        if self.get_cyborgs_inc(troop_list, owner) > self.cyborgs_count + self.get_cyborgs_inc(troop_list, self.owner):
            return True
        return False

    def is_bomb_inc(self, bomb_list):
        """
        Return True if a bomb is comming on self
        """
        for bomb in bomb_list:
            if bomb.factory_id_dest == self.factory_id:
                return True
        return False

    def get_range(self, dest):
        """
        return range between self and dest
        """
        for fact in self.factory_near:
            if fact[0] == dest:
                return fact[1]

    def get_cyborgs_inc_by_turn(self, troop_list, owner, turn_nb):
        """
        Return cyborgs cound comming on self next turn
        """
        count = 0
        for troop in troop_list:
            if troop.factory_id_dest == self.factory_id and \
               troop.owner == owner and troop.round_before_arrival <= turn_nb:
                count += troop.cyborgs_count
        return count

    def get_cyborgs_inc(self, troop_list, owner):
        """
        Return cyborgs cound comming on self
        """
        count = 0
        for troop in troop_list:
            if troop.factory_id_dest == self.factory_id and troop.owner == owner:
                count += troop.cyborgs_count
        return count

    def get_factory_near_sorted(self):
        """
        return list of all factory ordered by range
        """
        return sorted(self.factory_near, key=itemgetter(1))
    
    def get_owner_shortcut(self, dest, factory_dict, owner):
        """
        get a friendly factory with shortest path to dest from self
        """
        dist = self.get_range(dest.factory_id)
        target = dest.factory_id
        for f_src in self.factory_near:
            for f_dest in dest.factory_near:
                if factory_dict[f_src[0]].owner == owner and f_src[0] == f_dest[0] and (f_src[1] + f_dest[1]) < dist:
                    dist = f_src[1] + f_dest[1]
                    target = f_dest[0]
        if target == dest.factory_id:
            return target
        return self.get_owner_shortcut(factory_dict[target], factory_dict, owner)

    def get_shortcut(self, dest, factory_dict):
        """
        get a factory with shortest path to dest from self
        """
        dist = self.get_range(dest.factory_id)
        target = dest.factory_id
        for f_src in self.factory_near:
            for f_dest in dest.factory_near:
                if f_src[0] == f_dest[0] and (f_src[1] + f_dest[1]) < dist:
                    dist = f_src[1] + f_dest[1]
                    target = f_dest[0]
        if target == dest.factory_id:
            return target
        return self.get_shortcut(factory_dict[target], factory_dict)

    def consume_next_move(self):
        """
        Return next_move and set it back to None
        """
        tmp = self.next_move
        self.next_move = None
        return tmp

    def init_factory_near(self, factory_graph):
        """
        Init factory_near list
        """
        for link in factory_graph:
            if link[0] == self.factory_id:
                self.factory_near.append([link[1], link[2]])
            elif link[1] == self.factory_id:
                self.factory_near.append([link[0], link[2]])
    
    def __init__(self, factory_id, factory_graph):
        self.factory_near = []
        self.factory_id = factory_id
        self.init_factory_near(factory_graph)

    def update(self, owner, cyborgs_count, production):
        """
        Update class var every round
        """
        self.owner = owner
        self.cyborgs_count = cyborgs_count
        self.production = production

class Move:
    @staticmethod
    def bomb(src, dest):
        return ";BOMB {} {}".format(src, dest)

    @staticmethod
    def boost(src):
        return ";INC {}".format(src)

    @staticmethod
    def move(src, dest, cyborgs_count):
        return ";MOVE {} {} {}".format(src, dest, cyborgs_count)    

class IA(Move):
    """
    Base class for IA
    """
    command = ""
    factory_dict = None
    state_list = []

    def boost(self, src):
        self.command += super(IA, self).boost(src)

    def move(self, fact_src, dest, cyborgs_count, troop_list):
        if cyborgs_count < 0:
            return ;
        troop_list.append(TroopEntity(1, fact_src.factory_id, dest, cyborgs_count, fact_src.get_range(dest)))
        self.command += super(IA, self).move(fact_src.factory_id, dest, cyborgs_count)

    def is_ready(self, *args):
        return True

    def find_nearest(self, fact, owner, target_list=None, avoid_nb=0):
        """
        Find nearest factory around "fact"
        check owner, slice list with avoid number
        can take a custom "target_list" to search in
        return None for end of list
        """
        if target_list is None:
            target_list = fact.get_factory_near_sorted()

        for key, value in target_list:
            if self.factory_dict[key].owner == owner:
                if avoid_nb > 0:
                    avoid_nb -= 1
                    continue ;
                return key
        return None

    def find_nearest_by_condition(self, fact, owner, condition_func, troop_list, target_list=None, avoid_nb=0):
        """
        Find nearest factory around "fact" respecting "condition_func"
        raise exception for end of list
        """
        nearest = self.find_nearest(fact, owner, target_list, avoid_nb)

        while nearest is not None and condition_func(nearest, troop_list) is True:
            avoid_nb += 1
            nearest = self.find_nearest(fact, owner, target_list, avoid_nb)
                    
        if nearest is None:
            raise Exception("End of List")
        return nearest

    def __init__(self, factory_dict):
        self.factory_dict = factory_dict

class IABomber(IA):
    """
    Manage bomb entity
    """
    bomb_count = 0
    state_list = ["COLONY", "PVP", "TURTLE"]

    def launch_bomb(self, fact, state):
        """
        Launch bomb on fact and set a next move to attack behind if PVP state
        """
        self.bomb_count += 1
        
        self.command += super(IA, self).bomb(self.find_nearest(fact, 1), fact.factory_id)
        
        # if state != "COLONY":
        launch_base = self.factory_dict[self.find_nearest(fact, 1)]
        if launch_base is not None:
            launch_base.next_move = (launch_base.factory_id, fact.factory_id, 1)
    
    def play(self, fact, bomb_list, state, troop_list, *args, **kwargs):
        """
        Build command for bomb
        """
        self.command = ""
        if (fact.owner == -1 or (fact.is_win(troop_list, -1) and fact.owner != 1)) and fact.is_bomb_inc(bomb_list) is False:
            if ((fact.production >= 2) or (ROUND_COUNT > FREE_BOMB_LAUNCHING_ROUND_COUNT and fact.production >= 1)) and self.bomb_count == 0:
                self.launch_bomb(fact, state)
            elif ((fact.production >= 2) or (ROUND_COUNT > FREE_BOMB_LAUNCHING_ROUND_COUNT and fact.production >= 1)) and self.bomb_count == 1:
                self.launch_bomb(fact, state)
        return self.command

class IAAttack(IA):
    state_list = ["PVP",]

    def neutral_condition(self, target, troop_list):
        """
        check if target respect neutral condition for PVP state
        """
        if self.factory_dict[target].production == 0:
            return True
        if self.factory_dict[target].is_win(troop_list, 1) is True:
            return True
        if self.factory_dict[target].colony_in_progress is True:
            return True
        return False

    def enemy_condition(self, target, troop_list):
        """
        check if target respect enemy condition for PVP state
        """
        if self.factory_dict[target].production == 0 and self.factory_dict[target].is_win(troop_list, 1) is True:
            return True
        return False

    def find_enemy(self, fact, troop_list, colonise_list, avoid_nb):
        """
        Find nearest enemy around "fact" (PVP and TURTLE STATE)
        """
        try:
            nearest_neutral = self.find_nearest_by_condition(fact, 0, self.neutral_condition, troop_list, colonise_list, avoid_nb)
            if nearest_neutral is not None and self.factory_dict[nearest_neutral].production > 0:
                return nearest_neutral
        except Exception as e:
            print(e, file=sys.stderr)

        return self.find_nearest_by_condition(fact, -1, self.enemy_condition, troop_list, avoid_nb=avoid_nb)
    
    def get_troop_size(self, fact, troop_list, target):
        """
        Return troop size to win a factory, or fact.cyborgs_count
        """
        target_fact = self.factory_dict[target]
        round_to_target = fact.get_range(target)
        cyborgs_count_to_win = target_fact.cyborgs_count + (target_fact.production * round_to_target) + \
                               target_fact.get_cyborgs_inc_by_turn(troop_list, -1, round_to_target) - \
                               target_fact.get_cyborgs_inc_by_turn(troop_list, 1, round_to_target)
        # print("cyborgs_count_to_win: {}, target_fact.get_cyborgs_inc_by_turn: {}, round_to_target: {}".format(cyborgs_count_to_win, target_fact.get_cyborgs_inc_by_turn(troop_list, 1, round_to_target), round_to_target), file=sys.stderr)
        if cyborgs_count_to_win > 0 and cyborgs_count_to_win < fact.cyborgs_count:
            return cyborgs_count_to_win + 1
        return None

    def is_ready(self, fact, troop_list):
        """
        Check if "fact" respect general condition for PVP state
        """
        if fact.owner != 1:
            return False
        if fact.production == 3 and fact.cyborgs_count > fact.get_cyborgs_inc(troop_list, -1):
            fact.cyborgs_count -= fact.get_cyborgs_inc_by_turn(troop_list, -1, 1)
            return True
        elif fact.production == 2 and fact.cyborgs_count > fact.get_cyborgs_inc(troop_list, -1):
            fact.cyborgs_count -= fact.get_cyborgs_inc_by_turn(troop_list, -1, 1)
            return True
        elif fact.production == 1 and fact.cyborgs_count > fact.get_cyborgs_inc(troop_list, -1):
            fact.cyborgs_count -= fact.get_cyborgs_inc_by_turn(troop_list, -1, 1)
            return True
        elif fact.production == 0 and fact.cyborgs_count >= fact.get_cyborgs_inc(troop_list, -1):
            fact.cyborgs_count -= fact.get_cyborgs_inc_by_turn(troop_list, -1, 1)
            return True
        return False

    def rally_friend(self, fact, target, troop_list):
        nearest_friend = self.find_nearest(self.factory_dict[target], 1)
        if nearest_friend != fact.factory_id:
            self.move(fact, nearest_friend, fact.cyborgs_count, troop_list)
            fact.cyborgs_count -= fact.cyborgs_count

    def play(self, fact, troop_list, colonise_list, *args, **kwargs):
        """
        Build "fact" command for PVP state
        """
        self.command = ""
        avoid_nb = 0
        troop_size = 0
        while fact.cyborgs_count > 0:
            try:
                nearest_enemy = self.find_enemy(fact, troop_list, colonise_list, avoid_nb)
                # upgrade if base is safe and have prod
                if (fact.production == 1 or fact.production == 2) and \
                    fact.get_range(nearest_enemy) >= RANGE_FOR_BOOST_PVP:
                    self.boost(fact.factory_id)
                    break ;
                # else attack
                else:
                    shortcut = fact.get_shortcut(self.factory_dict[nearest_enemy], self.factory_dict)
                    # if i get shortcut
                    if shortcut != nearest_enemy:
                        troop_size = fact.cyborgs_count
                    else:
                        troop_size = self.get_troop_size(fact, troop_list, nearest_enemy)
                        # if enemy to big, rally on closest friend
                        if troop_size is None:
                            self.rally_friend(fact, nearest_enemy, troop_list)
                            avoid_nb += 1
                            continue ;
                    self.move(fact, shortcut, troop_size, troop_list)
                    fact.cyborgs_count -= troop_size
            except Exception as e:
                print(e, file=sys.stderr)
                break ;
        return self.command

class IAColonise(IA):
    state_list = ["COLONY",]

    def is_ready(self, fact, troop_list):
        """
        Check if "fact" respect general condition for colonisation state
        """
        if fact.owner != 1:
            return False
        if fact.production > 0 and fact.cyborgs_count > fact.get_cyborgs_inc(troop_list, -1):
            return True
        elif fact.production == 0:
            return True
        return False

    def colonise_condition(self, target, troop_list):
        """
        check if target respect colonisation condition for COLONY state
        """
        if self.factory_dict[target].colony_in_progress is True:
            return True
        return False

    def play(self, fact, troop_list, colonise_list, *args, **kwargs):
        """
        Build "fact" command for COLONY state
        """
        self.command = ""
        avoid_nb = 0
        while fact.cyborgs_count > 0:
            try:
                nearest_neutral = self.find_nearest_by_condition(fact, 0, self.colonise_condition, troop_list, colonise_list, avoid_nb)
                # shortcut = fact.get_shortcut(self.factory_dict[nearest_neutral], self.factory_dict)
                # if i get shortcut send all troop
                # if shortcut != nearest_neutral and (self.factory_dict[shortcut].owner == 1 or self.factory_dict[shortcut].owner == 0):
                #     troop_size = self.factory_dict[nearest_neutral].cyborgs_count + 1
                #     fact.cyborgs_count -= self.factory_dict[nearest_neutral].cyborgs_count + 1
                #     # avoid attack if my troops < enemy troop
                #     if fact.cyborgs_count < 0:
                #         fact.cyborgs_count += troop_size
                #         avoid_nb += 1
                #         continue ;
                #     nearest_neutral = shortcut
                # # else send troop needed to win
                # else:
                troop_size = self.factory_dict[nearest_neutral].cyborgs_count + 1
                fact.cyborgs_count -= troop_size
                # avoid attack if my troops < enemy troop
                if fact.cyborgs_count < 0:
                    fact.cyborgs_count += troop_size
                    avoid_nb += 1
                    continue ;
                self.factory_dict[nearest_neutral].colony_in_progress = True
                self.move(fact, nearest_neutral, troop_size, troop_list)
            except Exception as e:
                print(e, file=sys.stderr)
                break ;
        return self.command

class IATurtle(IAAttack):
    state_list = ["TURTLE",]

    def feeder_condition(self, target, troop_list):
        if self.factory_dict[target].production < 3:
            return True
        return False

    def feed(self, fact, troop_list):
        try:
            nearest_friend = self.find_nearest_by_condition(fact, 1, self.feeder_condition, troop_list)
            feeder = self.factory_dict[nearest_friend]
            if self.factory_dict[nearest_friend].get_range(fact.factory_id) <= 5 and feeder.cyborgs_count >= 0:
                if feeder.cyborgs_count == 0:
                    troop_size = feeder.production
                else:
                    troop_size = feeder.cyborgs_counts
                feeder.next_move = (feeder.factory_id, fact.factory_id, troop_size)
        except Exception as e:
            print(e, file=sys.stderr)

    def play(self, fact, troop_list, colonise_list, *args, **kwargs):
        """
        Build "fact" command for TURTLE state
        """
        self.command = ""

        if fact.production == 0:
            self.feed(fact, troop_list)

        avoid_nb = 0
        troop_size = 0
        while fact.cyborgs_count > 0:
            try:
                nearest_enemy = self.find_enemy(fact, troop_list, colonise_list, avoid_nb)
                # Upgrade if base is safe
                if fact.production < 3 and fact.get_range(nearest_enemy) >= RANGE_FOR_BOOST_TURTLE:
                    self.boost(fact.factory_id)
                    break ;
                # else attack
                else:
                    shortcut = fact.get_shortcut(self.factory_dict[nearest_enemy], self.factory_dict)
                    # if i get shortcut
                    if shortcut != nearest_enemy:
                        troop_size = fact.cyborgs_count
                    else:
                        troop_size = self.get_troop_size(fact, troop_list, nearest_enemy)
                        # if enemy to big, rally on closest friend
                        if troop_size is None:
                            self.rally_friend(fact, nearest_enemy, troop_list)
                            avoid_nb += 1
                            continue ;
                    self.move(fact, shortcut, troop_size, troop_list)
                    fact.cyborgs_count -= troop_size
            except Exception as e:
                print(e, file=sys.stderr)
                break ;
        return self.command

class IADodge(IA):
    state_list = ["COLONY", "PVP", "TURTLE"]

    def play(self, fact, troop_list, *args, **kwargs):
        """
        send all units on "fact" to nearest friend if "fact" is lost next turn
        """
        self.command = ""
        nearest = self.find_nearest(fact, 1)
        my_cyborgs_count = fact.cyborgs_count + fact.production + fact.get_cyborgs_inc_by_turn(troop_list, 1, 1)
        if nearest is not None and fact.owner == 1 and \
           fact.get_cyborgs_inc_by_turn(troop_list, -1, 1) > my_cyborgs_count:
            self.move(fact, nearest, fact.cyborgs_count, troop_list)
        return self.command

class IAManager:
    state = "COLONY"
    command = ""
    colonise_list = None
    ia_list = None

    def is_colony_end(self, factory_dict):
        """
        Condition for colony end state
        """
        for fact in self.colonise_list:
            if factory_dict[fact[0]].colony_in_progress is False and factory_dict[fact[0]].owner == 0:
                return False
        self.state = "PVP"
        self.update_state(factory_dict)
        return True

    def best_move(self, fact, factory_dict, troop_list, bomb_list):
        """
        Get the best moove for "fact" depending on game state
        """
        if fact.next_move is not None:
            move = fact.consume_next_move()
            if factory_dict[move[0]].owner == 1:
                self.command += Move.move(*move)
                fact.cyborgs_count -= move[2]
        
        for ia in self.ia_list:
            self.is_colony_end(factory_dict)
            if self.state in ia.state_list and ia.is_ready(fact, troop_list) is True:
                self.command += ia.play(fact=fact, troop_list=troop_list, bomb_list=bomb_list,
                                        colonise_list=self.colonise_list, state=self.state)

    def update_state(self, factory_dict):
        """
        Update game state
        """
        if self.state == "PVP" or self.state == "TURTLE":
            my_fac = 0
            my_prod = 0
            enemy_fac = 0
            enemy_prod = 0
            for key, fact in factory_dict.items():
                if fact.owner == 1:
                    my_fac += 1
                    my_prod += fact.production
                elif fact.owner == -1:
                    enemy_fac += 1
                    enemy_prod += fact.production
            # print("{} vs {}".format(my_prod, enemy_prod), file=sys.stderr)
            if my_fac >= FACTORY_COUNT // 2 + 1 or my_prod >= enemy_prod or my_fac >= enemy_fac:
                self.state = "TURTLE"
            else:
                self.state = "PVP"

    def manage(self, factory_dict, troop_list, bomb_list):
        """
        Init command line, update game state and run on all factory to get their moove
        """
        self.command = "WAIT"

        self.update_state(factory_dict)
        for key, fact in factory_dict.items():
            self.best_move(fact, factory_dict, troop_list, bomb_list)

        return self.command

    def init_first_round(self, factory_dict):
        """
        Init some vars on first round
        colonise_list
        """
        self.colonise_list = []
        for key, fact in factory_dict.items():
            if fact.owner == 1:
                my_fact = fact.factory_id
            elif fact.owner == -1:
                enemy_fact = fact.factory_id

        my_fac_near = factory_dict[my_fact].factory_near
        enemy_fac_near = factory_dict[enemy_fact].factory_near

        for my_fac in my_fac_near:
            for enemy_fac in enemy_fac_near:
                if my_fac[0] == enemy_fac[0] and my_fac[1] <= enemy_fac[1]:
                    self.colonise_list.append(my_fac)

        self.colonise_list = sorted(self.colonise_list, key=itemgetter(1))

    def __init__(self, *args):
        self.ia_list = args

factory_dict = {}
for i in range(FACTORY_COUNT):
    factory_dict[i] = FactoryEntity(i, link_array)

ia_colonise = IAColonise(factory_dict)
ia_attack = IAAttack(factory_dict)
ia_turtle = IATurtle(factory_dict)
ia_bomber = IABomber(factory_dict)
ia_dodge = IADodge(factory_dict)

ia = IAManager(ia_colonise, ia_attack, ia_turtle, ia_bomber, ia_dodge)

# game loop
while True:
    start = time.time()
    troop_list = []
    bomb_list = []
    entity_count = int(input())  # the number of entities (e.g. factories and troops)
    for i in range(entity_count):
        entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = input().split()
        entity_id = int(entity_id)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        arg_5 = int(arg_5)
        if entity_type == "FACTORY":
            factory_dict[entity_id].update(arg_1, arg_2, arg_3)
        elif entity_type == "TROOP":
            troop_list.append(TroopEntity(arg_1, arg_2, arg_3, arg_4, arg_5))
        elif entity_type == "BOMB":
            bomb_list.append(BombEntity(arg_1, arg_2, arg_3, arg_4))

    if ROUND_COUNT == 0:
        ia.init_first_round(factory_dict)

    command = ia.manage(factory_dict, troop_list, bomb_list)
    ROUND_COUNT += 1
    print("{}ms".format(int((time.time() - start) * 1000)), file=sys.stderr)
    print(command)
