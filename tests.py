from main import Dictionary, Validator, Stats, Engine
import unittest


class TestDictionary(unittest.TestCase):
    def test_filter_words(self):
        file = './dictionary-test.txt'
        with open(file, 'w') as f:
            f.write('fire\njust\nmoonwalk')

        dictionary = Dictionary(file)

        self.assertEqual(['fire', 'just'], dictionary.filter_words(max_word_length=4))


class TestValidator(unittest.TestCase):
    def test_validations(self):
        validator = Validator()
        self.assertTrue(validator.validate_user_word('fire', 'just')[0])
        self.assertFalse(validator.validate_user_word('fire123', 'just')[0])
        self.assertFalse(validator.validate_user_word('aasd', 'just')[0])


class TestStats(unittest.TestCase):
    def test_stats(self):
        file = './stats-test.json'
        with open(file, 'w') as f:
            f.write('{}')
        record = {
            'bulls': 4, 'cows': 0, 'difficulty': 'easy', 'attempts': 3, 'target_word': 'fire',
            'user_words': ['asdf', 'moon', 'neva']
        }
        stats = Stats(file)
        stats.push(**record)
        self.assertEqual(record['target_word'], stats.get_best_result_for_mode('easy')['target_word'])


class TestEngine(unittest.TestCase):
    def test_stats(self):
        engine = Engine()
        user_word_bulls = 'fire'
        user_word_cows = 'aweq'
        current_word = 'fire'

        engine.current_word = current_word

        self.assertEqual(engine.get_bulls(user_word_bulls), 4)
        self.assertEqual(engine.get_cows(user_word_cows), 1)



if __name__ == '__main__':
    unittest.main()