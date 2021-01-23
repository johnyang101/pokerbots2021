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
        self.MONTE_CARLO_ITERS = 500
        self.ordering_strength = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.ordering_number = [0, 0, 0, 0, 0, 0]
        self.epsilon = .7
        self.gamma = .98
        self.current_ordering = 0

        self.BIG_BLIND=True

        self.preflop_value_bet_lp=.6 
        self.preflop_bluff_lower_bound=.4  
        self.preflop_bluff_upper_bound=.6
        self.preflop_value_reraise_lp=.5
        
        self.postflop_value_bet_lp=.7 
        self.postflop_bluff_lower_bound=.4  
        self.postflop_bluff_upper_bound=.5
        self.postflop_value_reraise_lp=.5
        
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
        '''
        ranks = {}

        for card in my_cards:
            card_rank = card[0] # string of numbers 2-9, T for 10, J, Q, K, A
            card_suit = card[1] # d, h, s, c

            if card_rank in ranks: #appends card to ranks dictionary
                ranks[card_rank].append(card)
            else:
                ranks[card_rank] = [card]
        '''
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
                hands_max_score = hand_score
                best_hands = hand 
                best_hands_key = hand_key

        #merged_hands = tuple(zip(best_hands, best_hands_key))
        #merged_hands = sorted(merged_hands, key = lambda i: i[1])
        #best_hands_final = [tup[0] for tup in merged_hands]       
        best_hands_final=best_hands
        holes_allocated = best_hands_final
        '''    
        pairs = []
        singles = []

        for rank in ranks:
            cards = ranks[rank]

            if len(cards) == 1: #only single
                singles.append(cards[0])
            
            elif len(cards) == 2 or len(cards) == 4: # pairs or 4 of a kind
                pairs += cards
            
            else: #len(cards) == 3
                pairs.append(cards[0])
                pairs.append(cards[1])
                singles.append(cards[2])

        
        cards_remaining = set(my_cards)
        allocated_cards = set() #cards committed
        holes_allocated = [] #holes made already

        _MIN_PAIR_VALUE = 5 #we only want pairs stronger than this value

        for i in range(len(pairs)//2):
            pair = [pairs[2*i], pairs[2*i+1]] #get pair
            pair_rank = pair[0][0]

            if self.rank_to_numeric(pair_rank) >= _MIN_PAIR_VALUE:
                holes_allocated.append(pair)
                allocated_cards.update(pair)
            
        cards_remaining = cards_remaining - allocated_cards #update what cards we have remaining

        sorted_remaining = self.sort_cards_by_rank(list(cards_remaining))

        for i in range(len(sorted_remaining) - 1):
            card_1 = sorted_remaining[i]
            card_2 = sorted_remaining[i + 1]

            rank_diff = self.rank_to_numeric(card_1[0]) - self.rank_to_numeric(card_2[0])

            if (rank_diff <= 1) and (card_1 not in allocated_cards) and (card_2 not in allocated_cards):
                hole = [card_1, card_2]
                holes_allocated.append(hole)
                allocated_cards.update(hole)
            
        cards_remaining = cards_remaining - allocated_cards

        suits = {} #dictionary that maps suits to cards remaining
        for card in cards_remaining:
            card_suit = card[1]

            if card_suit in suits:
                suits[card_suit].append(card)
            else:
                suits[card_suit] = [card]
                
        for suit in suits:
            cards = suits[suit]

            if len(cards) == 2 or len(cards) == 3:
                hole = [cards[0], cards[1]]
                holes_allocated.append(hole)
                allocated_cards.update(hole)
            
            elif len(cards) == 4: 
                hole_1 = [cards[0], cards[1]]
                hole_2 = [cards[2], cards[3]]

                holes_allocated.append(hole_1)
                allocated_cards.update(hole_1)

                holes_allocated.append(hole_2)
                allocated_cards.update(hole_2)
    
        cards_remaining = cards_remaining - allocated_cards
        extra_cards = list(cards_remaining)

        for i in range(len(extra_cards) // 2):
            hole = [extra_cards[2*i], extra_cards[2*i +1]]
            holes_allocated.append(hole)
            allocated_cards.update(hole)

        cards_remaining = cards_remaining - allocated_cards


        assert len(holes_allocated) == 3, 'allocated more/less than 3 holes'
        assert len(cards_remaining) == 0, 'we didnt allocate enough'
        '''
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

        '''
        deck = eval7.Deck()
        hole_cards = [eval7.Card(card) for card in hole]

        for card in hole_cards:
            deck.cards.remove(card)
        
        score = 0

        for _ in range(iters):
            deck.shuffle()

            _COMM = 5
            _OPP = 2

            draw = deck.peek(_COMM + _OPP)

            opp_hole = draw[: _OPP]
            community = draw[_OPP: ]

            our_hand = hole_cards + community
            opp_hand = opp_hole + community

            our_hand_value = eval7.evaluate(our_hand) #eval7 values doesnt have any meaning, only relative rankings.
            opp_hand_value = eval7.evaluate(opp_hand)

            if our_hand_value > opp_hand_value: #we win
                score += 2
            
            elif our_hand_value == opp_hand_value: #we tie
                score += 1
            
            else: #we lost
                score += 0
        
        hand_strength = score / (2 * iters)

        return hand_strength
        '''

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
        if random.random()>self.epsilon:
            max_strength=-1
            for k in range (6):
                if self.ordering_strength[k]>max_strength:
                    max_strength=self.ordering_strength[k]
                    opt_index=k
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
        elif rand<.6666 or opt_index==4:
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
        self.assign_holes(allocated_holes)
        

        # lec 2 strat
        # self.allocate_cards(my_cards)

        # for i in range(NUM_BOARDS):
        #     hole = self.board_allocations[i]
        #     strength = self.calculate_strength(hole, self._MONTE_CARLO_ITERS)
        #     self.hole_strengths[i] = strength
    
    #def choose_lps(self, possibilities, total):
        
    def update_lps(self, result, my_delta):
        if result == 1.0: #win
            self.initial_hole_lp *= 1.01 + (my_delta * 0.001)
            self.decay_factor_lp += 0.05
            #logic underneath is that if we won a lot more, we can afford to play more ballsy.
            self.intimidated_threshold_lp *= 0.99 - (my_delta * 0.001)
            self.intimidation_factor_lp *= 0.99 - (my_delta * 0.001)
            self.overstrength_threshold_lp *= 0.99 - (my_delta * 0.001)
            self.aggressiveness_lp *= 0.95 - (my_delta * 0.001)
        elif result == -1.0: #loss
            assert result == -1.0, 'Result not -1 for loss'
            my_delta = abs(my_delta)

            self.initial_hole_lp *= 0.99 - (my_delta * 0.001)
            self.decay_factor_lp += 0.05 

            #if we lost a lot more, we should play more conservatively.
            self.intimidated_threshold_lp * 1.01 + (my_delta * 0.001)
            self.intimidation_factor_lp *= 1.01 + (my_delta * 0.001)
            self.overstrength_threshold_lp *= 1.01 + (my_delta * 0.001)
            self.aggressiveness_lp *= 1.05 + (my_delta * 0.001)

        return
        

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
        
        self.ordering_strength[self.current_ordering]=(self.ordering_strength[self.current_ordering]*(self.ordering_number[self.current_ordering]-1)+round_result)/self.ordering_number[self.current_ordering]
        
        self.update_lps(round_result, my_delta)

        self.board_allocations = [[],[],[]]
        self.hole_strengths = [0, 0, 0]

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
        
        

        def raise_amount_bounder(raise_amount, min_raise, max_raise):
            raise_amount = max([min_raise, raise_amount])
            raise_amount = min([max_raise, raise_amount])

            raise_cost = raise_amount - my_pips[i]

            if (raise_cost <= my_stack - net_cost):
                commit_cost = raise_cost
            else:
                commit_cost = my_stack - net_cost

            return raise_amount, commit_cost
        
        def action_tree(raise_amount, min_raise, max_raise):
            if RaiseAction in legal_actions[i] and raise_amount > 0:
                raise_amount, commit_cost = raise_amount_bounder(raise_amount, min_raise, max_raise)
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
            if AssignAction in legal_actions[i]: #allocate cards
                cards = self.board_allocations[i]
                my_actions[i] = AssignAction(cards)

            elif isinstance(round_state.board_states[i], TerminalState): #round over so check?
                my_actions[i] = CheckAction()

            else: #do we add more resources
                board_cont_cost = continue_cost[i] #continue cost is a list
                board_total = round_state.board_states[i].pot #pot before round starts
                pot_total = my_pips[i] + opp_pips[i] + board_total
                
                min_raise, max_raise_dummy = round_state.board_states[i].raise_bounds(active, round_state.stacks) #active variable is which player we are
                max_raise = my_stack - my_pips[i] - net_cost
                print([my_stack, my_pips[i], max_raise, net_upper_raise_bound], net_cost)
                pot_odds = board_cont_cost / (pot_total + board_cont_cost)

                if street < 3: #means pre-flop
                    if my_pips[i] == 1:
                        self.BIG_BLIND = False
                    elif my_pips[i] == 2 and opp_pips[i] == 1:
                        self.BIG_BLIND = True
                    
                    strength = self.hole_strengths[i]
                    if not self.BIG_BLIND and my_pips[i]==1:  
                        if strength>self.preflop_value_bet_lp or (strength>self.preflop_bluff_lower_bound and strength<self.preflop_bluff_upper_bound and pot_total<200): #small-blind raise for value or bluff
                            raise_amount = int(round(1.6666*(pot_total)+my_pips[i]))
                            commit_action, commit_cost = action_tree(raise_amount, min_raise, max_raise)
                        else: 
                            commit_action, commit_cost = action_tree(-2, min_raise, max_raise) #folding

                    elif board_cont_cost==0:
                        raise_amount= int(round(1.5*(pot_total)+my_pips[i]))
                        commit_action, commit_cost = action_tree(raise_amount, min_raise, max_raise)
                    else:
                        if strength>pot_odds+self.preflop_value_reraise_lp:
                            raise_amount= int(round(opp_pips[i]+pot_total*.666666))
                            commit_action, commit_cost = action_tree(raise_amount, min_raise, max_raise)
                        elif strength>pot_odds:
                            commit_action, commit_cost = action_tree(0, min_raise, max_raise) #call/check
                        else:
                            commit_action, commit_cost = action_tree(-2, min_raise, max_raise)
                                                
                    
                    '''
                    Initial raise amount should depend on strength of hole, an arbitrary learning parameter, and a randomness factor that decays over time.

                    My implementation does this; however, may not be ideal.
                    '''
                    
                    # initial_hole_lp = 1 #initial learning parameter
                    # decay_factor_lp = 1 #arbitarily increases by 0.1 lets say for each round. in the denominator of random_factor
                    #random_factor = random.random()

                    #raise_amount = int(round(my_pips[i] + board_cont_cost + (strength + self.initial_hole_lp) * (pot_total + board_cont_cost) + min(12, round((random_factor * (i + 1))/self.decay_factor_lp)))) #randomness factor depending on randomness, size of board, and decay

                else: #not pre-flop
                    '''
                    Post Flop Betting Logic
                    When PLaying Small Blind
                    If Big Blind checks then Small Blind will raise to put pressure (either as a bluff or for value) or check back with very weak cards
                    If Big Blind raises then reraise with really good cards, call with decent cards, fold with garbage cards

                    When Playing Big Blind
                    Raise with good cards or with bluffs, check with decent or garbage cards
                    If rereaised then call with good hands and reraise with super super good hands (should not happen often)
                    '''

                    strength = self.calculate_strength_postflop(self.board_allocations[i], self.MONTE_CARLO_ITERS, board_cards[i], street)
                    if continue_cost==0 and not self.BIG_BLIND:
                        if strength>self.postflop_value_bet_lp or (strength>self.postflop_bluff_lower_bound and strength<self.postflop_bluff_upper_bound and pot_total<200):
                            raise_amount=int(round(pot_total*1.5))
                            raise_amount = raise_amount_bounder(raise_amount, min_raise, max_raise)
                            commit_action, commit_cost = action_tree(raise_amount, min_raise, max_raise)
                        else:
                            commit_action, commit_cost = action_tree(-1, min_raise, max_raise) #checking

                    elif not self.BIG_BLIND:
                        if strength>pot_odds+self.postflop_value_reraise_lp:
                            raise_amount= int(round(opp_pips[i]+pot_total*.666666))
                            commit_action, commit_cost = action_tree(raise_amount, min_raise, max_raise)
                        elif strength>pot_odds:
                            commit_action, commit_cost = action_tree(0, min_raise, max_raise) #calling
                        else:
                            commit_action, commit_cost = action_tree(-2, min_raise, max_raise) #folding
                    elif continue_cost==0: 
                        if strength>self.postflop_value_bet_lp or (strength>self.postflop_bluff_lower_bound and strength<self.postflop_bluff_upper_bound and pot_total<200):
                            raise_amount=int(round(pot_total*1.5))
                            commit_action, commit_cost = action_tree(raise_amount, min_raise, max_raise)
                        else:
                            commit_action, commit_cost = action_tree(-1, min_raise, max_raise) #checking
                    else:
                        if strength>pot_odds+self.preflop_value_reraise_lp:
                            raise_amount= int(round(pot_total*1.5))
                            commit_action, commit_cost = action_tree(raise_amount, min_raise, max_raise)
                        elif strength>pot_odds:
                            commit_action, commit_cost = action_tree(0, min_raise, max_raise) #calling
                        else:
                            commit_action, commit_cost = action_tree(-2, min_raise, max_raise) #folding
                

                try:
                    assert commit_cost + net_cost <= my_stack, 'Raise is too much'
                    my_actions[i] = commit_action
                except:
                    print('Raise too much')
                    my_actions[i] = RaiseAction(max_raise)
                    commit_cost = max_raise
                
                if commit_cost >= 0:
                    net_cost += commit_cost
                #else dont update commit_cost
                
                
                '''
                if board_cont_cost > 0: #opponent raised

                    #intimidated_threshold_lp = 5
                    if board_cont_cost > self.intimidated_threshold_lp: #raised by more than 5, parameter to tweak
                        #intimidation_factor_lp = 0.15
                        
                        strength = max([0, strength - self.intimidation_factor_lp])

                    if strength >= pot_odds: #positive expected value
                                                #should at least call

                        overstrength = strength - pot_odds #should change our behavior depending on overstrength
                        
                        #overstrength_threshold_lp = 0.05

                        if overstrength > self.overstrength_threshold_lp and random.random() > 1 - strength:
                            my_actions[i] = commit_action #raise basically
                            net_cost += commit_cost
                        
                        else:
                            my_actions[i] = CallAction()
                            net_cost += board_cont_cost
                    
                    else: #negative EV
                        my_actions[i] = FoldAction()
                        net_cost += 0
                
                else: #board_cont_cost == 0
                    
                    if self.aggressiveness_lp + strength > 1: #aggressiveness_lp defined earlier.
                        my_actions[i] = commit_action
                        net_cost += commit_cost
                    
                    else:
                        my_actions[i] = CheckAction()
                        net_cost += 0
'''

        return my_actions
    


if __name__ == '__main__':
    run_bot(Player(), parse_args())
