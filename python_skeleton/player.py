'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction, AssignAction
from skeleton.states import GameState, TerminalState, RoundState, BoardState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND, NUM_BOARDS
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import eval7
import random
import math
'''
Things to do:

Implement win percent. DONE
Calculate strength of hands post-flop. DONE
Reform betting logic. ETHAN
Bluffing
'''


class Player(Bot):
    '''
    A pokerbot.
    '''
    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        self.board_allocations = [[],[],[]] #keep track of allocation of hole cards at round start
        self.hole_strengths = [0, 0, 0]
        self.MONTE_CARLO_ITERS = 400
        self.ordering_strength = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.ordering_number = [0, 0, 0, 0, 0, 0]
        self.epsilon = .7
        self.gamma = .98
        self.current_ordering = 0

        #1 normal, 2, strongest hole cards to third hole, 3 strongest hole cards to 1 and 2, 10 to check_fold
        self.NUM_STRATS = 3
        self.strat_number = 0
        self.strat_number_wins_plays = [(0, 0) for i in range(self.NUM_STRATS)]

        self.BIG_BLIND=True

        self.preflop_value_bet_lp=.6 
        self.preflop_bluff_lower_bound=.4  
        self.preflop_bluff_upper_bound=.6
        self.preflop_value_reraise_lp=.5
        
        self.postflop_value_bet_lp=.7 
        self.postflop_bluff_lower_bound=.4  
        self.postflop_bluff_upper_bound=.5
        self.postflop_value_reraise_lp=.6
        self.bound=40.0
        self.lp_options=[[.45,.5,.55,.6,.65,.7],[.35,.375,.4,.425,.45,.475],[.5,.525,.55,.575,.6,.625],[.4,.425,.45,.475,.5,.525,.55,.575,.6],[.55,.6,.65,.7,.75,.8],[.35,.375,.4,.425,.45,.475],[.4,.425,.45,.475,.5,.525],[.4,.425,.45,.475,.5,.525,.55,.575,.6]]
        self.lp_totals=self.lp_options[:]
        for i in range(len(self.lp_totals)):
            for j in range(len(self.lp_totals[i])):
                self.lp_totals[i][j]=[.1,0]
        self.indexes=[3,3,3,3,3,3,3,3]
        
        self.already_won=False
        self.aggressiveness_lp = random.random()
        self.initial_hole_lp = 0.1
        self.decay_factor_lp = 1
        self.intimidated_threshold_lp = 5
        self.intimidation_factor_lp = 0.15
        self.overstrength_threshold_lp = 0.05

        self.starting_strengths = {'AA': 85.255, 'KK': 82.39, 'QQ': 79.935, 'JJ': 77.485, 'TT': 75.02, '99': 72.09, '88': 69.175, '77': 66.24, 'KAs': 66.61, 'QAs': 65.8, 'JAs': 65.025, 'KA': 64.865, 'TAs': 64.25, '66': 63.17, 'QA': 64.005, 'JA': 63.16, 'QKs': 63.065, 'TA': 62.345, 'JKs': 62.26, '9As': 62.425, 'TKs': 61.49, '8As': 61.615, '55': 60.34, 'QK': 61.115, 'JK': 60.265,
         '7As': 60.665, '9A': 60.405, 'JQs': 60.085, '9Ks': 59.71, 'TK': 59.455, 'TQs': 59.315, '8A': 59.52, '5As': 59.615, '6As': 59.44, '4As': 58.725, '7A': 58.51, '44': 57.035, 'JQ': 57.965, '8Ks': 58.06, 'TJs': 57.49, '9K': 57.53, '9Qs': 57.515, '3As': 57.935, 'TQ': 57.135, '7Ks': 57.28, '5A': 57.36, '6A': 57.2, '2As': 57.155, '6Ks': 56.27, '4A': 56.41, '8Qs': 55.9,
          '8K': 55.75, '9Js': 55.645, 'TJ': 55.23, '9Q': 55.225, '5Ks': 55.56, '3A': 55.535, '33': 53.705, '7K': 54.925, '2A': 54.69, '4Ks': 54.645, '9Ts': 54.125, '7Qs': 54.185, '8Js': 54.01, '6K': 53.84, '3Ks': 53.83, '8Q': 53.48, '9J': 53.23, '6Qs': 53.4, '2Ks': 53.005, '5K': 53.07, '8Ts': 52.455, '5Qs': 52.68, '7Js': 52.315, '4K': 52.085, '9T': 51.63, '22': 50.365, '7Q': 51.65,
           '8J': 51.48, '4Qs': 51.765, '89s': 50.985, '3K': 51.175, '3Qs': 50.935, '7Ts': 50.76, '6Q': 50.78, '6Js': 50.5, '2K': 50.285, '2Qs': 50.07, '8T': 49.83, '5Js': 50.01, '5Q': 50.015, '7J': 49.69, '79s': 49.315, '4Js': 49.085, '6Ts': 48.95, '4Q': 49.025, '89': 48.305, '3Js': 48.245, '78s': 48.215, '7T': 48.025, '3Q': 48.12, '6J': 47.745, '69s': 47.53, '2Js': 47.405, '5Ts': 47.35, '2Q': 47.21, '5J': 47.2,
            '4Ts': 46.655, '79': 46.52, '68s': 46.4, '4J': 46.205, '6T': 46.105, '59s': 45.955, '3Ts': 45.81, '67s': 45.525, '78': 45.35, '3J': 45.3, '2Ts': 44.96, '58s': 44.82, '69': 44.59, '2J': 44.4, '5T': 44.375, '49s': 44.085, '57s': 44.005, '4T': 43.64, '39s': 43.475, '68': 43.395, '56s': 43.32, '48s': 42.98, '59': 42.895, '3T': 42.72, '29s': 42.63, '67': 42.455, '47s': 42.185, '2T': 41.81, '58': 41.725, '45s': 41.835,
             '46s': 41.53, '38s': 41.145, '49': 40.905, '57': 40.865, '28s': 40.565, '37s': 40.37, '39': 40.25, '56': 40.155, '35s': 40.065, '48': 39.75, '36s': 39.735, '29': 39.35, '34s': 39.03, '47': 38.905, '27s': 38.505, '45': 38.55, '25s': 38.235, '46': 38.225, '26s': 37.895, '38': 37.79, '28': 37.145, '24s': 37.235, '37': 36.96, '35': 36.65, '23s': 36.39, '36': 36.305, '34': 35.555, '27': 34.96, '25': 34.695, '26': 34.31, '24': 33.615, '23': 32.745}

        

    def rank_to_numeric(self, rank):
        if rank.isnumeric(): #2-9
            return int(rank)
        elif rank == 'T':
            return 10
        elif rank == 'J':
            return 11
        elif rank == 'Q':
            return 12
        elif rank == 'K':
            return 13
        elif rank == 'A':
            return 14
    
    def sort_cards_by_rank(self, cards):
        return sorted(cards, reverse=True, key=lambda x: self.rank_to_numeric(x[0])) #x[0] represents rank

    def hole_list_to_key(self, hole):
        '''
        Converts a hole card list into a key that we can use to query our 
        strength dictionary
        hole: list - A list of two card strings in the engine's format (Kd, As, Th, 7d, etc.)
        '''
        card_1 = hole[0] #get all of our relevant info
        card_2 = hole[1]

        rank_1, suit_1 = card_1[0], card_1[1] #card info
        rank_2, suit_2 = card_2[0], card_2[1]

        numeric_1, numeric_2 = self.rank_to_numeric(rank_1), self.rank_to_numeric(rank_2) #make numeric

        suited = suit_1 == suit_2 #off-suit or not
        suit_string = 's' if suited else ''

        if numeric_1 <= numeric_2: #keep our hole cards in rank order
            return rank_1 + rank_2 + suit_string
        else:
            return rank_2 + rank_1 + suit_string

    def allocate_cards(self, my_cards):
        
        # credits stackoverflow lol https://stackoverflow.com/a/5360442 
        def pairs_helper(cards):
            if len(cards) < 2: 
                yield []
                return 
            if len(cards) % 2 == 1:
                for i in range(len(cards)):
                    for result in pairs_helper(cards[:i] + cards[i+1:]):
                        yield result 
            else: 
                    a = cards[0]
                    for i in range(1,len(cards)):
                        pair = (a,cards[i])
                        for rest in pairs_helper(cards[1:i]+cards[i+1:]):
                            yield [pair] + rest                
                        
        def hand_lookup(card1, card2):
            if self.rank_to_numeric(card1[0]) <= self.rank_to_numeric(card2[0]):
                output = card1[0] + card2[0]
            else:
                output = card2[0] + card1[0]
            if card1[1] == card2[1]:
                output = output + 's'
            assert output in self.starting_strengths
            
            return self.starting_strengths[output]
        
        hands_max_score = 0 
        best_hands = [] #list of holes in game format
        best_hands_key = []
        for hand in pairs_helper(my_cards):
            hand_key = [hand_lookup(h[0], h[1]) for h in hand]
            #hand_key = [self.hole_list_to_key(h) for h in hand]
            hand_score = sum(map(lambda i : i*i*i, hand_key))
            if hand_score > hands_max_score: 
                print(best_hands)
                hands_max_score = hand_score
                best_hands = hand 
                best_hands_key = hand_key

        #merged_hands = tuple(zip(best_hands, best_hands_key))
        #merged_hands = sorted(merged_hands, key = lambda i: i[1])
        #best_hands_final = [tup[0] for tup in merged_hands]       
        best_hands_final=best_hands
        holes_allocated = best_hands_final

        assert len(holes_allocated) == 3, 'allocated more/less than 3 holes'
        return holes_allocated

        # if len(pairs) > 0:
        #     self.strong_hole = True

        # allocation = pairs + singles

        # for i in range(NUM_BOARDS):

        #     cards = [allocation[2*i], allocation[2*i + 1]]
            
        #     self.board_allocations[i] = cards
        

    def calculate_strength(self, hole, iters):
        return self.starting_strengths[self.hole_list_to_key(hole)]/100

    def calculate_strength_postflop(self, hole, iters, community, street):

        deck = eval7.Deck()
        hole_cards = [eval7.Card(card) for card in hole]
        community = community[:street]
        community_cards = [eval7.Card(card) for card in community]

        for card in hole_cards:
            deck.cards.remove(card)
        
        for card in community_cards:
            deck.cards.remove(card)
        
        score = 0

        for _ in range(iters):
            deck.shuffle()
            

            _COMM = 5 - street
            _OPP = 2

            draw = deck.peek(_COMM + _OPP)

            opp_hole = draw[: _OPP]
            sim_community = draw[_OPP:] + community_cards[:street]

            our_hand = hole_cards + sim_community
            opp_hand = opp_hole + sim_community

            our_hand_value = eval7.evaluate(our_hand)
            opp_hand_value = eval7.evaluate(opp_hand)

            if our_hand_value > opp_hand_value: #we win
                score += 2
            
            elif our_hand_value == opp_hand_value: #we tie
                score += 1
            
            else: #we lost
                score += 0
        
        hand_strength = score / (2 * iters)

        return hand_strength

    def assign_holes(self, hole_cards):
        holes_and_strengths = []

        for hole in hole_cards:
            key = self.hole_list_to_key(hole)
            strength = self.starting_strengths[key]/100
            # strength = self.calculate_strength(hole, self.MONTE_CARLO_ITERS)
            holes_and_strengths.append((hole, strength))

        hole_and_strengths = sorted(holes_and_strengths, key = lambda x: x[1])
        rand=1
        opt_index=-1
        if random.random()>self.epsilon: #sometimes use ordering strengths and find optimal index.
            rand=random.random()
            temp_strengths=self.ordering_strength/sum(self.ordering_strength)
            for i in range(len(temp_strengths-1)):
                temp_strengths[i+1]+=temp_strengths[i]
            for i in range(len(temp_strengths)):
                if temp_strengths[i]>rand:
                    opt_index=i
                    break
        else:
            rand=random.random()

        if rand<.16666 or opt_index==0:
            self.current_ordering=0
        elif rand<.33333 or opt_index==1:
            self.current_ordering=1
            temp = hole_and_strengths[2]
            hole_and_strengths[2] = hole_and_strengths[1]
            hole_and_strengths[1] = temp
        elif rand<.5 or opt_index==2:
            self.current_ordering=2
            temp = hole_and_strengths[1]
            hole_and_strengths[1] = hole_and_strengths[0]
            hole_and_strengths[0] = temp
        elif rand<.6666 or opt_index==3:
            self.current_ordering=3
            temp = hole_and_strengths[2]
            hole_and_strengths[2] = hole_and_strengths[1]
            hole_and_strengths[1] = temp
            temp = hole_and_strengths[2]
            hole_and_strengths[2] = hole_and_strengths[0]
            hole_and_strengths[0] = temp
        elif rand<.8333 or opt_index==4:
            self.current_ordering=3
            temp = hole_and_strengths[2]
            hole_and_strengths[2] = hole_and_strengths[1]
            hole_and_strengths[1] = temp
            temp = hole_and_strengths[1]
            hole_and_strengths[1] = hole_and_strengths[0]
            hole_and_strengths[0] = temp
        else:
            self.current_ordering=5
            temp = hole_and_strengths[2]
            hole_and_strengths[2] = hole_and_strengths[0]
            hole_and_strengths[0] = temp

        self.ordering_number[self.current_ordering] += 1
        self.epsilon*=self.gamma


        #if random.random() < 0.15: #swap strongest hole card with second
        #    temp = hole_and_strengths[2]
        #    hole_and_strengths[2] = hole_and_strengths[1]
        #    hole_and_strengths[1] = temp

        #if random.random() < 0.15: #swap second w last
        #    temp = hole_and_strengths[1]
        #    hole_and_strengths[1] = hole_and_strengths[0]
        #    hole_and_strengths[0] = temp
        
        for i in range(NUM_BOARDS):
            self.board_allocations[i] = hole_and_strengths[i][0]
            self.hole_strengths[i] = hole_and_strengths[i][1]
        
    def strategic_assign_holes(self, strat_number, hole_cards):

        #0 is default, 1 is focus on hole 3, 2 is focus on 1 and 2
        if strat_number == 0:
            return self.assign_holes(hole_cards)
        
        holes_and_strengths = []

        for hole in hole_cards:
            key = self.hole_list_to_key(hole)
            strength = self.starting_strengths[key]/100
            # strength = self.calculate_strength(hole, self.MONTE_CARLO_ITERS)
            holes_and_strengths.append((hole, strength))

        hole_and_strengths = sorted(holes_and_strengths, key = lambda x: x[1])

        if strat_number == 1: #maps strongest card to hole 3
            
            for i in range(NUM_BOARDS):
                j = NUM_BOARDS - i - 1
                self.board_allocations[i] = hole_and_strengths[j][0]
                self.hole_strengths[i] = hole_and_strengths[j][1]
        
        if strat_number == 2: #maps strongest cards to hole 1 and 2

            self.board_allocations[1] = hole_and_strengths[0][0]
            self.hole_strengths[1] = hole_and_strengths[0][1]

            self.board_allocations[0] = hole_and_strengths[1][0]
            self.hole_strengths[0] = hole_and_strengths[1][1]

            self.board_allocations[2] = hole_and_strengths[2][0]
            self.hole_strengths[2] = hole_and_strengths[2][1]

    def update_strats(self, my_delta):

        return

        if self.strat_number == 10 or self.already_won:
            self.strat_number = 10
            return
        
        
        if my_delta > 0: #updates strat_number_wins_plays
            self.strat_number_wins_plays[self.strat_number] = (self.strat_number_wins_plays[self.strat_number][0] + 1, self.strat_number_wins_plays[self.strat_number][1] + 1)
        else:
            self.strat_number_wins_plays[self.strat_number] = (self.strat_number_wins_plays[self.strat_number][0], self.strat_number_wins_plays[self.strat_number][1] + 1)

         #chooses best strat number based on win percentage with a randomness factor.
        max = -1
        best_strat_number = 0
        for i in range(self.NUM_STRATS): #choose best strat off of greatest win percentage
            if self.strat_number_wins_plays[i][1] != 0:
                if self.strat_number_wins_plays[i][0]/self.strat_number_wins_plays[i][1] > max:
                    max = self.strat_number_wins_plays[i][0]/self.strat_number_wins_plays[i][1]
                    best_strat_number = i

        rand = random.random()
        strat_list = []
        for i in range(self.NUM_STRATS):
            strat_list.append(i)

        if rand < 0.333:
            best_strat_number = strat_list[best_strat_number - 1]
        
        self.strat_number = best_strat_number
    

    def choose_lps(self, possibilities):
        return
        if random.random()<self.epsilon:
            return floor(random.random()*len(possibilities))

        probabilities=[]
        total=sum(possibilities)
        for i in range(len(possibilities)):
            if total == 0:
                probabilities.append(0)
            else:
                probabilities.append(possibilities[i]/total)
        for i in range(len(probabilities)-1):
            probabilities[i+1]+=probabilities[i]
        rand=random.random()
        for i in range(len(probabilities)):
            if probabilities[i]>rand:
                return i
        return len(probabilities)-1
        
    def change_probabilities_lp(self,change,lp_index,chosen_index):
        return
        self.lp_totals[lp_index][chosen_index][0]*=self.lp_totals[lp_index][chosen_index][1]
        self.lp_totals[lp_index][chosen_index][1]+=1
        self.lp_totals[lp_index][chosen_index][0]+=change
        self.lp_totals[lp_index][chosen_index][0]/=self.lp_totals[lp_index][chosen_index][1]
        self.lp_totals[lp_index][chosen_index][0]=max(self.lp_totals[lp_index][chosen_index],0)

        
    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        opp_bankroll = game_state.opp_bankroll # ^but for your opponent
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your six cards at teh start of the round
        big_blind = bool(active)  # True if you are the big blind
        
        allocated_holes = self.allocate_cards(my_cards)
        self.strategic_assign_holes(self.strat_number, allocated_holes)
        '''       
        for i in range(8):
            self.indexes[i]=self.choose_lps(self.lp_totals[i][:][0])
        self.preflop_value_bet_lp=self.lp_options[0][self.indexes[0]] 
        self.preflop_bluff_lower_bound=self.lp_options[1][self.indexes[1]]  
        self.preflop_bluff_upper_bound=self.lp_options[2][self.indexes[2]]
        self.preflop_value_reraise_lp=self.lp_options[3][self.indexes[3]]
        
        self.postflop_value_bet_lp=self.lp_options[4][self.indexes[4]] 
        self.postflop_bluff_lower_bound=self.lp_options[5][self.indexes[5]]  
        self.postflop_bluff_upper_bound=self.lp_options[6][self.indexes[6]]
        self.postflop_value_reraise_lp=self.lp_options[7][self.indexes[7]]
        '''

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        opp_delta = terminal_state.deltas[1-active] # your opponent's bankroll change from this round 
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        for terminal_board_state in previous_state.board_states:
            previous_board_state = terminal_board_state.previous_state
            my_cards = previous_board_state.hands[active]  # your cards
            opp_cards = previous_board_state.hands[1-active]  # opponent's cards or [] if not revealed

        bound=1.0
        round_result=min(max(my_delta,-bound),bound)
        round_result2=min(max(my_delta,0),self.bound)
        
        self.ordering_strength[self.current_ordering]=(self.ordering_strength[self.current_ordering]*(self.ordering_number[self.current_ordering]-1)+round_result2)/self.ordering_number[self.current_ordering]
        
        #self.update_lps(round_result2, my_delta)

        self.board_allocations = [[],[],[]]
        self.hole_strengths = [0, 0, 0]
        for i in range(8):
            self.change_probabilities_lp(min(max(my_delta,0),self.bound),i,self.indexes[i])

        self.update_strats(round_result2) #updates win percentages and strat number to run.

        print(self.strat_number_wins_plays)

        game_clock = game_state.game_clock
        round_num = game_state.round_num

        if round_num == NUM_ROUNDS:
            print(game_clock)


    def get_actions(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs a triplet of actions from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your actions.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards across all boards
        board_cards = [board_state.deck if isinstance(board_state, BoardState) else board_state.previous_state.deck for board_state in round_state.board_states] #the board cards
        my_pips = [board_state.pips[active] if isinstance(board_state, BoardState) else 0 for board_state in round_state.board_states] # the number of chips you have contributed to the pot on each board this round of betting
        opp_pips = [board_state.pips[1-active] if isinstance(board_state, BoardState) else 0 for board_state in round_state.board_states] # the number of chips your opponent has contributed to the pot on each board this round of betting
        continue_cost = [opp_pips[i] - my_pips[i] for i in range(NUM_BOARDS)] #the number of chips needed to stay in each board's pot
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        stacks = [my_stack, opp_stack]
        net_upper_raise_bound = round_state.raise_bounds()[1] # max raise across 3 boards
        net_cost = 0 # keep track of the net additional amount you are spending across boards this round
        my_actions = [None] * NUM_BOARDS
        
        if my_stack-opp_stack>21*(NUM_ROUNDS-game_state.round_num+1)+3:
            self.already_won=True

        def raise_amount_bounder(raise_amount):
            raise_amount = max([min_raise, raise_amount])
            raise_amount = min([max_raise, raise_amount])

            raise_cost = raise_amount - my_pips[i]

            if (raise_cost <= my_stack - net_cost):
                commit_cost = raise_cost
            else:
                commit_cost = my_stack - net_cost

            return raise_amount, commit_cost
        
        def action_tree(raise_amount):
            if RaiseAction in legal_actions[i] and raise_amount > 0:
                raise_amount, commit_cost = raise_amount_bounder(raise_amount)
                commit_action = RaiseAction(raise_amount)
            elif CallAction in legal_actions[i] and raise_amount == 0:
                commit_action = CallAction()
                commit_cost = board_cont_cost
            elif CheckAction in legal_actions[i] and raise_amount >= -1:
                commit_action = CheckAction()
                commit_cost = 0
            else:
                commit_action = FoldAction()
                commit_cost = -1
            
            return commit_action, commit_cost


        for i in range(NUM_BOARDS):
            i = NUM_BOARDS - i - 1 # can change the order we bet in. want to bet on strongest hand first.

            if AssignAction in legal_actions[i]: #allocate cards
                cards = self.board_allocations[i]
                my_actions[i] = AssignAction(cards)

            elif isinstance(round_state.board_states[i], TerminalState): #round over so check?
                my_actions[i] = CheckAction()

            else: #do we add more resources
                board_cont_cost = continue_cost[i] #continue cost is a list
                board_total = round_state.board_states[i].pot #pot before round starts
                pot_total = my_pips[i] + opp_pips[i] + board_total
                
                min_raise, max_raise = round_state.board_states[i].raise_bounds(active, round_state.stacks) #active variable is which player we are
                pot_odds = board_cont_cost / (pot_total + board_cont_cost)


                if self.strat_number == 10:
                    commit_action, commit_cost = action_tree(-1)
                    
                    my_actions[i] = commit_action
                    if commit_cost >= 0:
                        net_cost += commit_cost
                        
                else:
                    if street < 3: #means pre-flop
                        if my_pips[i] == 1:
                            self.BIG_BLIND = False
                        elif my_pips[i] == 2 and opp_pips[i] == 1:
                            self.BIG_BLIND = True
                        
                        strength = self.hole_strengths[i]
                        if not self.BIG_BLIND and my_pips[i]==1:  
                            #based on the strength and lps, we bet 5/3rds of the pot total preflop on small blind.
                            if strength>self.preflop_value_bet_lp or (strength>self.preflop_bluff_lower_bound and strength<self.preflop_bluff_upper_bound and pot_total<200): #small-blind raise for value or bluff
                                raise_amount = int(round(strength * 4 + ((0.5 - random.random()) * 2))) #int(round(1.6666*(pot_total)+my_pips[i])) 
                                #fixed raise amount
                                commit_action, commit_cost = action_tree(raise_amount)

                            else: 
                                commit_action, commit_cost = action_tree(0) #call

                        elif board_cont_cost==0: #we're big blind and small blind called.
                            if strength>self.preflop_value_bet_lp or (strength>self.preflop_bluff_lower_bound and strength<self.preflop_bluff_upper_bound and pot_total<200):
                                raise_amount= int(round(strength * 4 + ((0.5 - random.random()) * 2)))#int(round(1.5*(pot_total)+my_pips[i]))
                                commit_action, commit_cost = action_tree(raise_amount)
                            else:
                                commit_action, commit_cost = action_tree(-1)
                        else:
                            if strength> 0.79: #because if they raise us, they have good cards.
                                raise_amount= int(round(opp_pips[i]+pot_total*.666666))
                                commit_action, commit_cost = action_tree(raise_amount)
                            elif strength > (pot_odds + (random.random() * 0.5)):
                                if pot_total > 100:
                                    if strength > 0.79:
                                        commit_action, commit_cost = action_tree(0)
                                    else:
                                        commit_action, commit_cost = action_tree(-2)
                                elif pot_total > 50:
                                    if strength > 0.65:
                                        commit_action, commit_cost = action_tree(0)
                                    else:
                                        commit_action, commit_cost = action_tree(-2)
                                else:
                                    commit_action, commit_cost = action_tree(0) #call/check
                            else:
                                commit_action, commit_cost = action_tree(-2)

                    else: #not pre-flop

                        strength = self.calculate_strength_postflop(self.board_allocations[i], self.MONTE_CARLO_ITERS, board_cards[i], street)
                        if continue_cost==0 and not self.BIG_BLIND:
                            if strength > self.postflop_value_bet_lp:
                                raise_amount = int(round(pot_total*1.2))
                                commit_action, commit_cost = action_tree(raise_amount)
                            elif (strength>self.postflop_bluff_lower_bound and strength<self.postflop_bluff_upper_bound and pot_total<100):
                                raise_amount = int(round(pot_total * strength / 2 + my_pips[i]))
                                commit_action, commit_cost = action_tree(raise_amount)
                            else:
                                commit_action, commit_cost = action_tree(-1) #checking
                        elif not self.BIG_BLIND:
                            if strength > 0.6 + 0.1*i and pot_total < 200:
                                raise_amount= int(round(opp_pips[i]+pot_total*.666666))
                                commit_action, commit_cost = action_tree(raise_amount)

                            elif strength>pot_odds + 0.3:
                                commit_action, commit_cost = action_tree(0) #calling
                            else:
                                commit_action, commit_cost = action_tree(-2) #folding
                        elif continue_cost==0: #big blind, we go first and nothing's happened

                            if strength>self.postflop_value_bet_lp:
                                raise_amount=int(round(pot_total*1.2))
                                commit_action, commit_cost = action_tree(raise_amount)
                            elif (strength>self.postflop_bluff_lower_bound and strength<self.postflop_bluff_upper_bound and pot_total<200):
                                raise_amount = int(round(pot_total * strength / 2 + my_pips[i]))
                                commit_action, commit_cost = action_tree(raise_amount)
                            else:
                                commit_action, commit_cost = action_tree(-1) #checking
                        else:
                            if strength> 0.6 + pot_odds:
                                raise_amount= int(round(min(0.15 * (my_stack - net_cost), pot_total * 1.1)))
                                commit_action, commit_cost = action_tree(raise_amount)
                            elif strength>pot_odds + 0.3:
                                commit_action, commit_cost = action_tree(0) #calling
                            else:
                                commit_action, commit_cost = action_tree(-2) #folding


                    #random_factor = random.random()

                    #raise_amount = int(round(my_pips[i] + board_cont_cost + (strength + self.initial_hole_lp) * (pot_total + board_cont_cost) + min(12, round((random_factor * (i + 1))/self.decay_factor_lp)))) #randomness factor depending on randomness, size of board, and decay
                
                    my_actions[i] = commit_action
                    if commit_cost >= 0:
                        net_cost += commit_cost
                #else dont update commit_cost
                

        return my_actions
    


if __name__ == '__main__':
    run_bot(Player(), parse_args())
