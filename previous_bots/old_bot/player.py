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
        self.MONTE_CARLO_ITERS = 100
        self.ordering_strength = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.ordering_number = [0, 0, 0, 0, 0, 0]
        self.epsilon = .7
        self.gamma = .99
        self.current_ordering = 0

        self.aggressiveness_lp = random.random()
        self.initial_hole_lp = 0.0
        self.decay_factor_lp = 1.0
        self.intimidated_threshold_lp = .75
        self.intimidation_factor_lp = 0.075
        self.overstrength_threshold_lp = 0.05
        self.optimal_lps=[0.5,0.0,1.0,0.75,0.075,0.05]
        self.my_delta_sum=[0.0,0.0,0.0,0.0,0.0,0.0]
        self.weighted_lps_sum=[0.0,0.0,0.0,0.0,0.0,0.0]
        self.lp_ranges=[1.0,.6,1.0,.5,.15,.1]
        self.epsilon_lp=[.9,.9,.9,.9,.9,.9]
        self.gamma_lp=.985
        self.flag_aggressive=False
        self.flag_overstrength=False
        self.flag_intimidation=False
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

    def allocate_cards(self, my_cards):
        ranks = {}

        for card in my_cards:
            card_rank = card[0] # string of numbers 2-9, T for 10, J, Q, K, A
            card_suit = card[1] # d, h, s, c

            if card_rank in ranks: #appends card to ranks dictionary
                ranks[card_rank].append(card)
            else:
                ranks[card_rank] = [card]

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

        return holes_allocated

        # if len(pairs) > 0:
        #     self.strong_hole = True

        # allocation = pairs + singles

        # for i in range(NUM_BOARDS):

        #     cards = [allocation[2*i], allocation[2*i + 1]]

        #     self.board_allocations[i] = cards


    def calculate_strength(self, hole, iters):

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

    def assign_holes(self, hole_cards):
        holes_and_strengths = []

        for hole in hole_cards:
            strength = self.calculate_strength(hole, self.MONTE_CARLO_ITERS)
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

    def choosing_lps(self):
        self.aggressiveness_lp=self.optimal_lps[0]
        self.initial_hole_lp=self.optimal_lps[1]
        self.decay_factor_lp+=.1
        self.intimidated_threshold_lp=self.optimal_lps[3]
        self.intimidation_factor_lp=self.optimal_lps[4]
        self.overstrength_threshold_lp=self.optimal_lps[5]

        if random.random()<self.epsilon_lp[0]:
            self.aggressiveness_lp=random.random()*self.lp_ranges[0]
        if random.random()<self.epsilon_lp[1]:
            self.initial_hole_lp=random.random()*self.lp_ranges[1]-.3
        if random.random() < self.epsilon_lp[3]:
            self.intimidated_threshold_lp = random.random() * self.lp_ranges[3]+.5
        if random.random() < self.epsilon_lp[4]:
            self.intimidation_factor_lp = random.random() * self.lp_ranges[4]
        if random.random() < self.epsilon_lp[5]:
            self.overstrength_threshold_lp = random.random() * self.lp_ranges[5]

    def update_optimal_lps(self, my_delta):
        bound_lp=40.0
        if my_delta>0:
            my_delta=min(my_delta,bound_lp)

            if self.flag_aggressive:
                self.weighted_lps_sum[0]+=self.aggressiveness_lp*my_delta
                self.my_delta_sum[0] += my_delta
                self.epsilon_lp[0] *= self.gamma_lp

            self.weighted_lps_sum[1] += self.initial_hole_lp*my_delta
            self.my_delta_sum[1] += my_delta
            self.epsilon_lp[1] *= self.gamma_lp

            if self.flag_intimidation:
                self.weighted_lps_sum[3] += self.intimidated_threshold_lp*my_delta
                self.weighted_lps_sum[4] += self.intimidation_factor_lp*my_delta
                self.my_delta_sum[3] += my_delta
                self.my_delta_sum[4] += my_delta
                self.epsilon_lp[3] *= self.gamma_lp
                self.epsilon_lp[4] *= self.gamma_lp

            if self.flag_overstrength:
               self.weighted_lps_sum[5] += self.overstrength_threshold_lp*my_delta
               self.my_delta_sum[5] += my_delta
               self.epsilon_lp[5] *= self.gamma_lp

            self.flag_intimidation=False
            self.flag_overstrength=False
            self.flag_aggressive=False

            for j in range(6):
                if self.my_delta_sum[j] == 0:
                    pass
                else:
                    self.optimal_lps[j]=self.weighted_lps_sum[j]/self.my_delta_sum[j]



      #  if result == 1.0: #win
       #     self.initial_hole_lp * 1.01 + (my_delta * 0.001)
        #    self.decay_factor_lp += 0.05
         #   #logic underneath is that if we won a lot more, we can afford to play more ballsy.
       #     self.intimidated_threshold_lp *= 0.99 - (my_delta * 0.001)
        #    self.intimidation_factor_lp *= 0.99 - (my_delta * 0.001)
         #   self.overstrength_threshold_lp *= 0.99 - (my_delta * 0.001)
         #   self.aggressiveness_lp *= 0.95 - (my_delta * 0.001)
       # elif result == -1.0: #loss
        #    assert result == -1.0, 'Result not -1 for loss'
        #    my_delta = abs(my_delta)
        #   self.initial_hole_lp *= 0.99 - (my_delta * 0.001)
        #    self.decay_factor_lp += 0.05

            #if we lost a lot more, we should play more conservatively.
        #   self.intimidated_threshold_lp * 1.01 + (my_delta * 0.001)
        #   self.intimidation_factor_lp *= 1.01 + (my_delta * 0.001)
        #    self.overstrength_threshold_lp *= 1.01 + (my_delta * 0.001)
        #    self.aggressiveness_lp *= 1.05 + (my_delta * 0.001)

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

        self.update_optimal_lps(my_delta)

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
        for i in range(NUM_BOARDS):
            if AssignAction in legal_actions[i]: #allocate cards
                cards = [my_cards[2*i], my_cards[2*i+1]]
                my_actions[i] = AssignAction(cards)

            elif isinstance(round_state.board_states[i], TerminalState): #round over so check?
                my_actions[i] = CheckAction()

            else: #do we add more resources
                board_cont_cost = continue_cost[i] #continue cost is a list
                board_total = round_state.board_states[i].pot #pot before round starts
                pot_total = my_pips[i] + opp_pips[i] + board_total

                min_raise, max_raise = round_state.board_states[i].raise_bounds(active, round_state.stacks) #active variable is which player we are
                strength = self.hole_strengths[i]

                if street < 3: #means pre-flop
                    if my_pips[i] == 1:
                        BIG_BLIND = False
                    elif my_pips[i] == 2 and opp_pips[i] == 1:
                        BIG_BLIND = True

                    '''
                    Initial raise amount should depend on strength of hole, an arbitrary learning parameter, and a randomness factor that decays over time.

                    My implementation does this; however, may not be ideal.
                    '''

                    # initial_hole_lp = 1 #initial learning parameter
                    # decay_factor_lp = 1 #arbitarily increases by 0.1 lets say for each round. in the denominator of random_factor
                    random_factor = random.random()
                    doggo = round(my_pips[i] + board_cont_cost + (strength + self.initial_hole_lp) * (pot_total + board_cont_cost) + min(12, round((random_factor * (i + 1))/self.decay_factor_lp)))
                    print(doggo)
                    print('initial hole lp ' + str(self.initial_hole_lp))
                    raise_amount = int(round(my_pips[i] + board_cont_cost + (strength + self.initial_hole_lp) * (pot_total + board_cont_cost) + min(12, round((random_factor * (i + 1))/self.decay_factor_lp)))) #randomness factor depending on randomness, size of board, and decay

                else: #not pre-flop
                    # need to code smth to figure out strength given hole AND community cards.
                    # rn just using hole strength


                    # initial_hole_lp = 1 #initial learning parameter
                    # decay_factor_lp = 1 #arbitarily increases by 0.1 lets say for each round. in the denominator of random_factor
                    random_factor = random.random()
                    doggo = round(my_pips[i] + board_cont_cost + (strength + self.initial_hole_lp) * (pot_total + board_cont_cost) + min(12, round((random_factor * (i + 1))/self.decay_factor_lp)))
                    print(doggo)
                    print('initial hole lp ' + str(self.initial_hole_lp))
                    raise_amount = int(round(my_pips[i] + board_cont_cost + (strength + self.initial_hole_lp) * (pot_total + board_cont_cost) + min(12, round((random_factor * (i + 1))/self.decay_factor_lp)))) #randomness factor depending on randomness, size of board, and decay


                #makes sure raise amount in bounds
                raise_amount = max([min_raise, raise_amount])
                raise_amount = min([max_raise, raise_amount])

                raise_cost = raise_amount - my_pips[i]

                #need to be allowed to raise and afford it
                if RaiseAction in legal_actions[i]:
                    commit_action = RaiseAction(raise_amount)
                    if (raise_cost <= my_stack - net_cost):
                        commit_cost = raise_cost
                    else:
                        commit_cost = my_stack - net_cost

                elif CallAction in legal_actions[i]:
                    commit_action = CallAction()
                    commit_cost = board_cont_cost

                else: #can only check
                    commit_action = CheckAction()
                    commit_cost = 0



                if board_cont_cost > 0: #opponent raised

                    #intimidated_threshold_lp = 5
                    if board_cont_cost > self.intimidated_threshold_lp*pot_total: #raised by more than 5, parameter to tweak
                        #intimidation_factor_lp = 0.15

                        strength = max([0, strength - self.intimidation_factor_lp])
                        self.flag_intimidation=True

                    pot_odds = board_cont_cost / (pot_total + board_cont_cost)

                    if strength >= pot_odds: #positive expected value
                                                #should at least call

                        overstrength = strength - pot_odds #should change our behavior depending on overstrength

                        #overstrength_threshold_lp = 0.05

                        if overstrength > self.overstrength_threshold_lp and random.random() > 1 - strength:
                            my_actions[i] = commit_action #raise basically
                            net_cost += commit_cost
                            self.flag_overstrength=True

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
                        self.flag_aggressive=True

                    else:
                        my_actions[i] = CheckAction()
                        net_cost += 0


        return my_actions
    


if __name__ == '__main__':
    run_bot(Player(), parse_args())
