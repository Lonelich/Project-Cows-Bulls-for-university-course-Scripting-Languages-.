from typing import Dict, Tuple, List
from random import choice
from datetime import datetime
from os.path import exists as is_exists
from sys import argv
import json

WORD_INDEX = int
WORD = str
DETAIL = str
COUNT = int
VALIDATE = Tuple[bool, DETAIL]
STATS = Dict


class Dictionary:
    default_dictionary_path = './dictionary.txt'

    def __init__(self, file: str = None):
        self.file = file or Dictionary.default_dictionary_path
        self.words = self.load_words()

    def load_words(self):
        with open(self.file, 'r', encoding='utf-8') as f:
            words = f.read().split('\n')
        return words

    def filter_words(self, max_word_length: int = None):
        if not max_word_length:
            return self.words
        return [word for word in self.words if len(word) <= max_word_length]


class Stats:
    date_format: str = '%Y-%m-%d'
    default_highscore_path = 'highscore.txt'

    def __init__(self, stats_file: str = './stats.json', hightscore_file: str = None, date_format: str = None):
        self.stats_file = stats_file
        self.date_format = date_format or Stats.date_format
        self.highscore_file = hightscore_file or Stats.default_highscore_path

        if not is_exists(stats_file):
            with open(stats_file, 'w') as f:
                f.write('{}')
        self.stats: STATS = json.load(open(self.stats_file, 'r', encoding='utf-8'))

    @property
    def today(self):
        today_str = datetime.now().strftime(self.date_format)
        self._create_today_if_not_exists(today_str)
        return today_str

    def _create_today_if_not_exists(self, today_str: str):
        if today_str not in self.stats:
            self.stats.update({today_str: []})

    def push(self, bulls: str, cows: str, difficulty: str, attempts: int, target_word: str,
             user_words: List[str]):
        record = {
            'bulls': bulls,
            'cows': cows,
            'difficulty': difficulty,
            'attempts': attempts,
            'target_word': target_word,
            'user_words': user_words,
            'date': self.today
        }
        self.stats[self.today].append(record)
        self.save()
        return record

    def get_best_result_for_mode(self, mode: str):
        best_record = None
        for day in self.stats.keys():
            for record in self.stats[day]:
                if record['difficulty'] != mode:
                    continue

                if not best_record or record['attempts'] < best_record['attempts']:
                    best_record = record.copy()

        return best_record

    def get_best_result(self):
        best_record = None
        for day in self.stats.keys():
            for record in self.stats[day]:
                if not best_record or record['attempts'] < best_record['attempts']:
                    best_record = record.copy()

        return best_record

    def get_best_result_for_mode_pretty(self, mode: str):
        result = self.get_best_result_for_mode(mode)
        if not result:
            return 'No one game is played in that mode...'
        return ''.join([f'{k}: {v}\n' for k, v in result.items()])

    def get_best_result_pretty(self):
        result = self.get_best_result()
        if not result:
            return 'No one game is played all time...'
        return ''.join([f'{k}: {v}\n' for k, v in result.items()])

    def save(self):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.stats, indent=3, ensure_ascii=False))

    def export_to_txt(self, msg='Success'):
        with open(self.highscore_file, 'w') as f:
            f.write(self.get_best_result_pretty())
        return msg


class Validator:
    def __init__(self):
        pass

    def validate_user_word(self, user_word: str, current_word: str):
        is_correct, msg = self.validate_length(user_word, current_word)
        if not is_correct:
            return is_correct, msg

        is_correct, msg = self.validate_doubles(user_word)
        if not is_correct:
            return is_correct, msg
        return True, 'OK'

    @staticmethod
    def validate_length(word1: str, word2: str) -> VALIDATE:
        if len(word1) != len(word2):
            return False, 'Length is incorrect'
        return True, 'OK'

    @staticmethod
    def validate_doubles(word: str) -> VALIDATE:
        last_check = None
        for symbol in word:
            if symbol == last_check:
                return False, 'it\'s not an izogram'
            last_check = symbol

        return True, 'OK'


class Engine:
    difficulty_params = {
        'easy': {
            'max_word_length': 4,
            'mode': 'easy'
        },
        'normal': {
            'max_word_length': 7,
            'mode': 'normal'
        },
        'hard': {
            'max_word_length': 10,
            'mode': 'hard'
        }
    }
    default_config_path = './config.json'

    def __init__(self, config: str = None):
        self.stats = NotImplementedError
        self.validator = NotImplementedError
        self.dictionary = NotImplementedError

        self.config = self._load_config(config or Engine.default_config_path)
        self.current_word = None
        self.difficulty = None
        self.attempts = None

    def init(self):
        if not self.config.get('mode'):
            self.request_difficulty()
        if not self.config.get('attempts'):
            self.request_attempts()

        self.difficulty = self.difficulty_params[self.config['mode']]
        self.attempts = self.config['attempts']

        self.stats = Stats()
        self.validator = Validator()
        self.dictionary = Dictionary()

        self.choice_current()

    def _load_config(self, config: str):
        self._config_file = config
        if not is_exists(self._config_file):
            with open(self._config_file, 'w') as f:
                f.write('{}')

        with open(self._config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config

    def write_to_config(self, **kwargs):
        if not hasattr(self, '_config_file'):
            raise Exception('Config is not loaded.')
        self.config.update(kwargs)
        with open(self._config_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.config, indent=3, ensure_ascii=False))

    def init_menu(self):
        self.stats = Stats()

    def _get_right_words_position(self, user_word: str) -> Dict[WORD_INDEX, WORD]:
        guessed_words = {}
        for index, user_symbol in enumerate(user_word):
            if user_symbol == self.current_word[index]:
                guessed_words[index] = user_symbol
        return guessed_words

    def get_bulls(self, user_word: str) -> COUNT:
        return len(self._get_right_words_position(user_word))

    def get_cows(self, user_word: str):
        cows = 0
        right_positions = self._get_right_words_position(user_word)
        current_without_bulls = ''.join(
            [symbol for index, symbol in enumerate(self.current_word) if index not in right_positions])
        for user_symbol in user_word:
            cows += current_without_bulls.count(user_symbol)

        return cows

    def choice_current(self):
        self.current_word = choice(self.dictionary.filter_words(max_word_length=self.difficulty['max_word_length']))

    def change_mode(self, new_mode: str):
        if new_mode not in self.difficulty_params.keys():
            return 'Incorrect mode.'
        self.write_to_config(mode=new_mode)
        self.dictionary = self.difficulty_params[new_mode]
        return 'difficulty mode is changed to: %s' % new_mode

    def change_attempts(self, attempts: str or int):
        if isinstance(attempts, str):
            attempts = int(attempts)

        self.attempts = attempts
        self.write_to_config(attempts=attempts)
        return 'attempts has changed to %s' % self.attempts

    def request_difficulty(self):
        difficulty_modes = list(self.difficulty_params.keys())
        selected = None
        while not selected:
            user_input = input(f'Select difficulty one of {difficulty_modes}: ')
            if user_input not in difficulty_modes:
                print(f'please select difficulty one of {difficulty_modes}')
                continue
            selected = user_input
        self.write_to_config(mode=selected)

    def request_attempts(self):
        print('No attempts contains in the config')
        attempts = None
        while not attempts:
            try:
                user_input = int(input(f'Input count of attempts: '))
            except Exception:
                print(f'Incorrect. Please input int attempts.')
                continue
            attempts = user_input

        self.write_to_config(attempts=attempts)

    def is_totally_right(self, user_word: str):
        bulls = self.get_bulls(user_word)
        return bulls == len(user_word)

    @property
    def rules(self):
        return f"""
        --Cows&Bulls--!
      You need to guess the word
    If you want to leave write "q" 
               """

    @property
    def config_string(self):
        return f"You can change your config in the menu of game.\n" \
               f"mode: {self.config.get('mode')}"

    def run(self):
        self.init()
        print('-------')
        print(self.config_string)
        user_words = []
        bulls = 0
        cows = 0
        save = lambda: self.stats.push(bulls, cows, self.difficulty['mode'], attempt, self.current_word,
                                       user_words)

        print(self.rules)

        print('Current word length: %s' % len(self.current_word))

        attempt = 0
        while attempt < self.attempts:
            print(f'Attempt {attempt}/{self.attempts}')
            user_word = input('Your guess: ')
            is_correct, msg = self.validator.validate_user_word(user_word, self.current_word)

            if user_word == 'q':
                break
            if not is_correct:
                print(msg)
                continue

            user_words.append(user_word)
            if self.is_totally_right(user_word):
                print('YOU WON! THAT\'S RIGHT!')
                print('The word has been: %s' % self.current_word)
                save()
                break
            bulls, cows = self.get_bulls(user_word), self.get_cows(user_word)

            print(f'Bulls: {bulls}, Cows: {cows}')

            attempt += 1
            save()

    def menu(self):
        self.init_menu()
        commands = {
            'best': {
                'func': self.stats.get_best_result_for_mode_pretty,
                'example': 'best easy',
                'description': 'see your best result'
            },
            'mode': {
                'func': self.change_mode,
                'example': 'mode easy',
                'description': 'Change difficulty to "easy", "normal" or "hard"'
            },
            'export': {
                'func': self.stats.export_to_txt,
                'example': 'export',
                'description': 'Export your result to hightscore.txt'
            },
            'attempts': {
                'func': self.change_attempts,
                'example': 'attempts 20',
                'description': 'Change count of attempts'
            },
            'q': {
                'func': None,
                'example': 'q',
                'description': 'Quit from menu'
            }
        }
        print("""
        < -- Menu commands -->
        """)
        for cmd in commands.keys():
            print(f'{cmd}: {commands[cmd]["description"]}. Example use: {commands[cmd]["example"]}')
        while True:
            command = input('Command: ')
            args = command.split(' ')
            cmd = args[0]
            if cmd == 'q':
                break

            if cmd not in commands:
                print('Incorrect command.')
                continue

            print(commands[cmd]['func'](*args[-1:] if args else None))


if __name__ == '__main__':
    game = Engine()
    while True:
        go_to = input('menu, new, rules, quit: ')
        if go_to == 'menu':
            game.menu()
        elif go_to == 'new':
            game.run()
        elif go_to == 'rules':
            print(game.rules)
        elif go_to == 'quit':
            print("Have a nice day)")
            break