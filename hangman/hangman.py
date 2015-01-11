
# coding: utf-8

# In[4]:

import re
import random
import string
import collections


# In[5]:

WORDS = [w.strip() for w in open('/usr/share/dict/british-english').readlines() 
         if re.match(r'^[a-z]*$', w.strip())]


# In[6]:

LETTER_COUNTS = collections.Counter(l.lower() for l in open('../sherlock-holmes.txt').read() if l in string.ascii_letters)
LETTERS_IN_ORDER = [p[0] for p in LETTER_COUNTS.most_common()]


# In[7]:

STARTING_LIVES = 10


# In[8]:

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


# In[9]:

DICT_COUNTS = collections.Counter(l.lower() for l in open('/usr/share/dict/british-english').read() if l in string.ascii_letters)
DICT_LETTERS_IN_ORDER = [p[0] for p in DICT_COUNTS.most_common()]


# In[10]:

class PlayerAdaptiveNoRegex:
    def __init__(self, words):
        self.candidate_words = words
        
    def guess(self, discovered, missed, lives):
        self.filter_candidate_words(discovered, missed)
        self.set_ordered_letters()
        guessed_letters = [l.lower() for l in discovered + missed if l in string.ascii_letters]
        return [l for l in self.ordered_letters if l not in guessed_letters][0]
    
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


# In[11]:

class PlayerAdaptiveLengthNoRegex(PlayerAdaptiveNoRegex):
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


# In[12]:

class PlayerAdaptiveIncludedLettersNoRegex(PlayerAdaptiveNoRegex):
    def filter_candidate_words(self, discovered, missed):
        self.candidate_words = [w for w in self.candidate_words if self.match(discovered, w)]


# In[13]:

class PlayerAdaptiveExcludedLettersNoRegex(PlayerAdaptiveNoRegex):
    def filter_candidate_words(self, discovered, missed):
        if missed:
            empty_target = '_' * len(discovered)
            self.candidate_words = [w for w in self.candidate_words if self.match(empty_target, w, missed)]        


# In[14]:

class PlayerAdaptivePatternNoRegex(PlayerAdaptiveNoRegex):
    def filter_candidate_words(self, discovered, missed):
        attempted_letters = [l for l in discovered if l != '_'] + missed
        self.candidate_words = [w for w in self.candidate_words if self.match(discovered, w, attempted_letters)]


# In[15]:

get_ipython().run_cell_magic('timeit', '', '\nwins = 0\nfor _ in range(1000):\n    g = Game(random.choice(WORDS), player=PlayerAdaptivePatternNoRegex(WORDS))\n    g.play_game()\n    if g.game_won:\n        wins += 1\nprint(wins)')


# In[21]:

len([w for w in WORDS if 'r' in w])


# In[22]:

len([w for w in WORDS if 'r' not in w])


# In[19]:

letter_diffs = []
for l in string.ascii_lowercase:
    n = 0
    for w in WORDS:
        if l in w:
            n += 1
        else:
            n -=1
    letter_diffs += [(l, abs(n))]
sorted(letter_diffs, key=lambda p: p[1])


# In[23]:

def letter_diff(l):
    return abs(sum(1 if l in w else -1 for w in WORDS))

letter_diffs = [(l, letter_diff(l)) 
                for l in string.ascii_lowercase]
sorted(letter_diffs, key=lambda p: p[1])


# In[71]:

class PlayerAdaptiveSplit(PlayerAdaptivePatternNoRegex):
    def set_ordered_letters(self):
        def letter_diff(l):
            return abs(sum(1 if l in w else -1 for w in self.candidate_words))
        possible_letters = set(''.join(self.candidate_words))
        # if len(self.candidate_words) > 1:
        letter_diffs = [(l, letter_diff(l)) for l in possible_letters]
        self.ordered_letters = [p[0] for p in sorted(letter_diffs, key=lambda p: p[1])]
        # else:
        #    self.ordered_letters = list(self.candidate_words[0])


# In[72]:

g = Game(random.choice(WORDS), player=PlayerAdaptiveSplit(WORDS))
g.play_game()


# In[73]:

g.target


# In[74]:

g.discovered


# In[75]:

g.wrong_letters


# In[78]:

get_ipython().run_cell_magic('timeit', '', '\nwins = 0\nfor _ in range(1000):\n    g = Game(random.choice(WORDS), player=PlayerAdaptiveSplit(WORDS))\n    g.play_game()\n    if g.game_won:\n        wins += 1\nprint(wins)')


# In[54]:

p=PlayerAdaptiveSplit(WORDS)


# In[55]:

dsc = ['_'] * len('recognition')
dsc


# In[56]:

p.guess(dsc, [], 10)


# In[57]:

len(p.candidate_words)


# In[58]:

p.guess(['_', '_', '_', 'o', '_', '_', '_', '_', '_', 'o', '_'], [], 10)


# In[59]:

p.candidate_words


# In[60]:

p.guess(['_', '_', 'c', 'o', '_', '_', '_', '_', '_', 'o', '_'], [], 10)


# In[61]:

p.candidate_words


# In[62]:

p.guess(['_', '_', 'c', 'o', '_', '_', '_', '_', '_', 'o', '_'], ['a'], 9)


# In[63]:

p.candidate_words


# In[64]:

p.guess(['_', '_', 'c', 'o', '_', '_', '_', '_', '_', 'o', '_'], ['a', 'd'], 8)


# In[65]:

p.candidate_words


# In[67]:

g = Game('recognition', player=PlayerAdaptiveSplit(WORDS))
g.play_game()


# In[68]:

g.discovered


# In[69]:

g.lives


# In[79]:

get_ipython().run_cell_magic('timeit', '', '\nwins = 0\nfor _ in range(10000):\n    g = Game(random.choice(WORDS), player=PlayerAdaptiveSplit(WORDS))\n    g.play_game()\n    if g.game_won:\n        wins += 1\nprint(wins)')


# In[81]:

get_ipython().run_cell_magic('timeit', '', '\nwins = 0\nfor _ in range(10000):\n    g = Game(random.choice(WORDS), player=PlayerAdaptivePatternNoRegex(WORDS))\n    g.play_game()\n    if g.game_won:\n        wins += 1\nprint(wins)')


# In[90]:

for w in random.sample(WORDS, 5000):
    gp = Game(w, player=PlayerAdaptivePatternNoRegex(WORDS))
    gp.play_game()
    gs = Game(w, player=PlayerAdaptiveSplit(WORDS))
    gs.play_game()
    if not gp.game_won and not gs.game_won:
        print('Both:::::', gp.target, 'Pattern:', '[' + ' '.join(gp.discovered) + ']', ''.join(gp.wrong_letters), 
              ':: Split:', '[' + ' '.join(gs.discovered) + ']', ''.join(gs.wrong_letters))
    if not gp.game_won and gs.game_won:
        print('Pattern::', gp.target, '[' + ' '.join(gp.discovered) + ']', ''.join(gp.wrong_letters))
    if gp.game_won and not gs.game_won:
        print('Split::::', gs.target, '[' + ' '.join(gs.discovered) + ']', ''.join(gs.wrong_letters))


# In[91]:

gs = Game('businesses', player=PlayerAdaptiveSplit(WORDS))


# In[170]:

g = Game('feminism', player=PlayerAdaptiveSplit(WORDS))
while not g.game_finished:
    guess = g.player.guess(g.discovered, g.wrong_letters, g.lives)
    print(g.target, '(' + str(g.lives) + ')', 
          '[' + ' '.join(g.discovered) + ']', ''.join(g.wrong_letters), 
          ';', len(g.player.candidate_words), 'candidate words')
    print('Guess = ', guess)
    g.do_turn()


# In[172]:

g = Game('feminism', player=PlayerAdaptivePatternNoRegex(WORDS))
while not g.game_finished:
    guess = g.player.guess(g.discovered, g.wrong_letters, g.lives)
    print(g.target, '(' + str(g.lives) + ')', 
          '[' + ' '.join(g.discovered) + ']', ''.join(g.wrong_letters), 
          ';', len(g.player.candidate_words), 'candidate words')
    print('Guess = ', guess)
    g.do_turn()


# In[171]:

g.player.candidate_words


# In[ ]:



