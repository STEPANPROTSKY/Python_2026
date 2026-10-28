"""Задание 3. Поисковый индекс на основе инвертированного индекса"""

import re


def tokenize(text):
    return re.findall(r'\w+', text.lower())


class SearchIndex:
    """Простой поиск по текстам.

    Что храним:
      _index  : dict[слово, set[doc_id]] - для каждого слова множество документов,
                где оно есть (это и есть инвертированный индекс). Через dict слово
                находится сразу, без перебора. set нужен, чтобы быстро находить общие
                документы (&) или все вместе (|) и быстро убирать документ.
      _docs   : dict[doc_id, dict[слово, сколько раз]] - какие слова есть в каждом
                документе. Благодаря ему remove и повторный add меняют только слова
                этого документа, а не проходят по всему индексу. Еще он нужен для
                search_ranked.
      _counts : dict[слово, сколько раз] - сколько раз слово встречается во всех
                документах вместе. Обновляется в add и remove, нужен для top_words.
    """

    def __init__(self):
        self._index = {}
        self._docs = {}
        self._counts = {}

    def add(self, doc_id, text):
        if doc_id in self._docs:
            self.remove(doc_id)
        words = {}
        for w in tokenize(text):
            words[w] = words.get(w, 0) + 1
        self._docs[doc_id] = words
        for w, n in words.items():
            self._index.setdefault(w, set()).add(doc_id)
            self._counts[w] = self._counts.get(w, 0) + n

    def remove(self, doc_id):
        words = self._docs.pop(doc_id, None)
        if words is None:
            raise KeyError(doc_id)
        for w, n in words.items():
            ids = self._index[w]
            ids.discard(doc_id)
            if not ids:
                del self._index[w]
            self._counts[w] -= n
            if not self._counts[w]:
                del self._counts[w]

    def _sets(self, words):
        return [self._index.get(w.lower(), set()) for w in words]

    def search_all(self, *words):
        if not words:
            return set()
        # начинаем с самого маленького множества: так меньше лишних проверок
        sets = sorted(self._sets(words), key=len)
        # делаем копию, чтобы снаружи нельзя было случайно испортить индекс
        result = set(sets[0])
        for s in sets[1:]:
            if not result:
                break
            result &= s
        return result

    def search_any(self, *words):
        return set().union(*self._sets(words))

    def top_words(self, n):
        # если количество одинаковое, сортируем по алфавиту, чтобы порядок всегда был одним
        return sorted(self._counts.items(), key=lambda p: (-p[1], p[0]))[:n]

    def search_ranked(self, query, limit=10):
        words = set(tokenize(query))
        scores = {}
        for w in words:
            for doc_id in self._index.get(w, ()):
                scores[doc_id] = scores.get(doc_id, 0) + self._docs[doc_id][w]
        ranked = sorted(scores, key=lambda d: (-scores[d], d))
        return ranked[:limit]

    def __len__(self):
        return len(self._docs)

    def __contains__(self, doc_id):
        return doc_id in self._docs


if __name__ == '__main__':
    idx = SearchIndex()
    idx.add(1, 'Python is a programming language.')
    idx.add(2, 'A dict is a hash table; a set is a hash table too!')
    idx.add(3, 'Python dict and set are fast.')
    assert idx.search_all('python') == {1, 3}
    assert idx.search_all('dict', 'set') == {2, 3}
    assert idx.search_all('python', 'hash') == set()
    assert idx.search_any('language', 'fast') == {1, 3}
    assert idx.search_all('PYTHON') == {1, 3}
    assert idx.search_all('nothing') == set()
    assert idx.top_words(2) == [('a', 5), ('is', 3)]

    # 3*: ранжирование
    # у документа 2 вес 2+2=4, у документов 1 и 3 по 1
    assert idx.search_ranked('hash table python') == [2, 1, 3]
    assert idx.search_ranked('a') == [2, 1]
    assert idx.search_ranked('a python', limit=2) == [2, 1]
    assert idx.search_ranked('nothing here') == []
    # повтор слова в запросе не удваивает вес
    assert idx.search_ranked('Dict, DICT dict!') == [2, 3]

    idx.remove(1)
    assert idx.search_all('python') == {3}
    assert idx.search_any('language', 'programming') == set()
    idx.add(3, 'Totally new text')
    assert idx.search_all('python') == set()
    assert idx.search_all('new') == {3}

    # свои проверки
    # слово пропало из индекса совсем
    assert 'python' not in idx._index and 'python' not in idx._counts
    assert 'language' not in idx._index
    assert idx.top_words(1) == [('a', 4)]
    assert idx.search_all() == set() and idx.search_any() == set()
    found = idx.search_all('new')
    # результат - копия, поэтому индекс не меняется
    found.add(999)
    assert idx.search_all('new') == {3}
    try:
        idx.remove(42)
        assert False, 'ожидали KeyError'
    except KeyError:
        pass

    e = SearchIndex()
    e.add('a', '')
    e.add('b', '!!! ...')
    assert e.top_words(5) == [] and e.search_any('x') == set() and len(e) == 2
    # \w находит и русские буквы, и _
    e.add('c', 'Кот и кот, КОТ_2 кот')
    assert e.search_all('кот') == {'c'} and e.search_all('кот_2') == {'c'}
    assert e.top_words(1) == [('кот', 3)]
    # повторный add заменяет текст и счетчики
    e.add('c', 'кот')
    assert e.top_words(5) == [('кот', 1)]
    e.remove('c')
    assert e.top_words(5) == [] and e._index == {}

    print('search_index: все проверки пройдены')
