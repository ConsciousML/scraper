import os
import json

from mtgscrapper.items import MtgArticle


def deep_equal(element_1, element_2) -> bool:
    if not isinstance(element_1, type(element_2)):
        return False

    mutable_types = (str, int, bool, float)
    if isinstance(element_1, mutable_types):
        return element_1 == element_2

    if isinstance(element_1, dict):
        for key, value_1 in element_1.items():
            value_2 = element_2.get(key)
            if not deep_equal(value_1, value_2):
                return False

    elif isinstance(element_1, list):
        for value_1, value_2 in zip(element_1, element_2):
            if not deep_equal(value_1, value_2):
                return False
    elif isinstance(element_1, type(None)):
        return True
    else:
        raise ValueError(f'type {type(element_1)} not supported.')
    return True


def test_article_load_equal():
    test_filepath = os.path.join('data', 'test_article.json')

    with open(test_filepath, 'r') as json_file:
        original_dict = json.load(json_file)

    mtg_article = MtgArticle.from_dict(original_dict)

    infered_dict = mtg_article.to_dict()

    assert deep_equal(original_dict, infered_dict), 'loaded article must be the same as the source.'

    infered_dict['content'][2]['format_'] = 'historic'

    assert not deep_equal(original_dict,
                          infered_dict), ('modified article must not be the same as the source.')
