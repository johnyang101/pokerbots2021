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
        
        if len(pairs) > 0:
            self.strong_hole = True

        allocation = pairs + singles

        for i in range(NUM_BOARDS):

            cards = [allocation[2*i], allocation[2*i + 1]]
            
            self.board_allocations[i] = cards
        

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
        
        _MONTE_CARLO_ITERS = 100
        
        self.allocate_cards(my_cards)

        for i in range(NUM_BOARDS):
            hole = self.board_allocations[i]
            strength = self.calculate_strength(hole, _MONTE_CARLO_ITERS)
            self.hole_strengths[i] = strength

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
            if AssignAction in legal_actions[i]:
                cards = [my_cards[2*i], my_cards[2*i+1]]
                my_actions[i] = AssignAction(cards)

            elif isinstance(round_state.board_states[i], TerminalState):
                my_actions[i] = CheckAction()

            else: #do we add more resources
                board_cont_cost = continue_cost[i] #continue cost is a list
                board_total = round_state.board_states[i].pot #pot before round starts
                pot_total = my_pips[i] + opp_pips[i] + board_total
                
                min_raise, max_raise = round_state.board_states[i].raise_bounds(active, round_state.stacks) #active variable is which player we are
                strength = self.hole_strengths[i]

                if street < 3: #means pre-flop
                    raise_amount = int(my_pips[i] + board_cont_cost + 0.4 * (pot_total + board_cont_cost)) #0.4 is a parameter to tweak
                else:
                    raise_amount = int(my_pips[i] + board_cont_cost + 0.75 * (pot_total + board_cont_cost))
                
                #makes sure raise amount in bounds
                raise_amount = max([min_raise, raise_amount])
                raise_amount = min([max_raise, raise_amount])

                raise_cost = raise_amount - my_pips[i]

                #need to be allowed to raise and afford it
                if RaiseAction in legal_actions[i] and (raise_cost <= my_stack - net_cost):
                    commit_action = RaiseAction(raise_amount)
                    commit_cost = raise_cost
                
                elif CallAction in legal_actions[i]:
                    commit_action = CallAction()
                    commit_cost = board_cont_cost
                
                else: #can only check
                    commit_action = CheckAction()
                    commit_cost = 0
                
                if board_cont_cost > 0: #opponent raised

                    if board_cont_cost > 5: #raised by more than 5, parameter to tweak
                        _INTIMIDATION = 0.15
                        strength = max([0, strength - _INTIMIDATION])
                    
                    pot_odds = board_cont_cost / (pot_total + board_cont_cost)

                    if strength >= pot_odds: #positive expected value
                                                #should at least call

                        if strength > 0.5 and random.random() < strength:
                            my_actions[i] = commit_action
                            net_cost += commit_cost
                        
                        else:
                            my_actions[i] = CallAction()
                            net_cost += board_cont_cost
                    
                    else: #negative EV
                        my_actions[i] = FoldAction()
                        net_cost += 0
                
                else: #board_cont_cost == 0
                    if random.random() < strength:
                        my_actions[i] = commit_action
                        net_cost += commit_cost
                    
                    else:
                        my_actions[i] = CheckAction()
                        net_cost += 0





            # elif RaiseAction in legal_actions[i] and self.strong_hole:
            #     min_raise, max_raise = round_state.board_states[i].raise_bounds(active, stacks)
            #     max_cost = max_raise - my_pips[i]

            #     if max_cost <= my_stack - net_cost:
            #         my_actions[i] = RaiseAction(max_raise)
            #         net_cost += max_cost
                
            #     elif CallAction in legal_actions[i]:
            #         my_actions[i] = CallAction()
            #         net_cost += continue_cost
            #     else:
            #         my_actions[i] = CheckAction()
                
            # elif CheckAction in legal_actions[i]:  # check-call
            #     my_actions[i] = CheckAction()
            # else:
            #     my_actions[i] = CallAction()
        return my_actions
    


if __name__ == '__main__':
    run_bot(Player(), parse_args())
