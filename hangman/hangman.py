import re
import random
import string
import collections

WORDS = [w.strip() for w in open('/usr/share/dict/british-english').readlines() 
         if re.match(r'^[a-z]*$', w.strip())]

LETTER_COUNTS = collections.Counter(l.lower() for l in open('../sherlock-holmes.txt').read() if l in string.ascii_letters)
LETTERS_IN_ORDER = [p[0] for p in LETTER_COUNTS.most_common()]

DICT_COUNTS = collections.Counter(''.join(WORDS))
DICT_LETTERS_IN_ORDER = [p[0] for p in DICT_COUNTS.most_common()]

STARTING_LIVES = 10

class Game:
    def __init__(self, target, player=None, lives=STARTING_LIVES):
        self.lives = lives
        self.player = player
        self.target = target
        self.discovered = list('_' * len(target))
        self.wrong_letters = []
        self.game_finished = False
        self.game_won = False
        self.game_lost = False
    
    def find_all(self, letter):
        return [p for p, l in enumerate(self.target) if l == letter]
    
    def update_discovered_word(self, guessed_letter):
        locations = self.find_all(guessed_letter)
        for location in locations:
            self.discovered[location] = guessed_letter
        return self.discovered
    
    def do_turn(self):
        if self.player:
            guess = self.player.guess(self.discovered, self.wrong_letters, self.lives)
        else:
            guess = self.ask_for_guess()
        if guess in self.target:
            self.update_discovered_word(guess)
        else:
            self.lives -= 1
            if guess not in self.wrong_letters:
                self.wrong_letters += [guess]
        if self.lives == 0:
            self.game_finished = True
            self.game_lost = True
        if '_' not in self.discovered:
            self.game_finished = True
            self.game_won = True
            
    def ask_for_guess(self):
        print('Word:', ' '.join(self.discovered), 
              ' : Lives =', self.lives, 
              ', wrong guesses:', ' '.join(sorted(self.wrong_letters)))
        guess = input('Enter letter: ').strip().lower()[0]
        return guess
    
    def play_game(self):
        while not self.game_finished:
            self.do_turn()
        if not self.player:
            self.report_on_game()
        return self.game_won
    
    def report_on_game(self):
        if self.game_won:
            print('You won! The word was', self.target)
        else:
            print('You lost. The word was', self.target)
        return self.game_won


class PlayerFixedOrder:
    def __init__(self, ordered_letters):
        self.ordered_letters = ordered_letters
        
    def guess(self, discovered, missed, lives):
        return [l for l in self.ordered_letters if l not in discovered + missed][0]

class PlayerAlphabetical(PlayerFixedOrder):
    def __init__(self):
        super().__init__(string.ascii_lowercase)

class PlayerAlphabeticalReversed(PlayerFixedOrder):
    def __init__(self):
        super().__init__(list(reversed(string.ascii_lowercase)))

class PlayerFreqOrdered(PlayerFixedOrder):
    def __init__(self):
        super().__init__(LETTERS_IN_ORDER)

class PlayerDictFreqOrdered(PlayerFixedOrder):
    def __init__(self):
        super().__init__(DICT_LETTERS_IN_ORDER)


class PlayerAdaptive:
    def __init__(self, words):
        self.candidate_words = words
        
    def guess(self, discovered, missed, lives):
        self.filter_candidate_words(discovered, missed)
        self.set_ordered_letters()
        return [l for l in self.ordered_letters if l not in discovered + missed][0]
    
    def filter_candidate_words(self, discovered, missed):
        pass
        
    def set_ordered_letters(self):
        counts = collections.Counter(l.lower() 
                                     for l in ''.join(self.candidate_words) + string.ascii_lowercase 
                                     if l in string.ascii_letters)
        self.ordered_letters = [p[0] for p in counts.most_common()]

    def match(self, pattern, target, excluded=None):
        if not excluded:
            excluded = ''
        if len(pattern) != len(target):
            return False
        for m, c in zip(pattern, target):
            if m == '_' and c not in excluded:
                # true
                pass
            elif m != '_' and m == c:
                # true
                pass
            else:
                return False
        return True        

class PlayerAdaptiveLength(PlayerAdaptive):
    def __init__(self, words):
        super().__init__(words)
        self.word_len = None
        self.ordered_letters = None
        
    def filter_candidate_words(self, discovered, missed):
        if not self.word_len:
            self.word_len = len(discovered)
            self.candidate_words = [w for w in self.candidate_words if len(w) == self.word_len]
    
    def set_ordered_letters(self):
        if not self.ordered_letters:
            super().set_ordered_letters()


class PlayerAdaptiveIncludedLetters(PlayerAdaptive):
    def filter_candidate_words(self, discovered, missed):
        self.candidate_words = [w for w in self.candidate_words if self.match(discovered, w)]


class PlayerAdaptiveExcludedLetters(PlayerAdaptive):
    def filter_candidate_words(self, discovered, missed):
        if missed:
            empty_target = '_' * len(discovered)
            self.candidate_words = [w for w in self.candidate_words if self.match(empty_target, w, missed)]        


class PlayerAdaptivePattern(PlayerAdaptive):
    def filter_candidate_words(self, discovered, missed):
        attempted_letters = [l for l in discovered if l != '_'] + missed
        self.candidate_words = [w for w in self.candidate_words if self.match(discovered, w, attempted_letters)]


class PlayerAdaptiveSplit(PlayerAdaptivePattern):
    def set_ordered_letters(self):
        def letter_diff(l):
            return abs(sum(1 if l in w else -1 for w in self.candidate_words))
        possible_letters = set(''.join(self.candidate_words))
        letter_diffs = [(l, letter_diff(l)) for l in possible_letters]
        self.ordered_letters = [p[0] for p in sorted(letter_diffs, key=lambda p: p[1])]

