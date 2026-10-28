"""Задание 1. Своя хеш-таблица с цепочками (+ 1*: порядок вставки)

Как устроено (по схеме словаря с лекции):
  self._entries : все пары (key, value) подряд, в том порядке, в котором их добавили.
                  Если пару удалили, на ее месте остается None.
  self._buckets : список корзин. В корзине лежат пары (key, номер записи в _entries).
                  В какую корзину класть ключ: hash(key) % len(self._buckets).

Корзины нужны, чтобы быстро найти ключ, а _entries хранят значения и помнят порядок.
Внутри класса нет dict и set, только списки и кортежи.

Отличие от условия: в корзине лежит не (key, value), а (key, номер записи).
Так сделано ради пункта 1*: иначе не получится сохранить порядок добавления
(так понял что, это и есть подсказка про словарь с лекции). Коллизии, поиск через == и stats()
работают так же, как в условии
"""


class MyDict:
    def __init__(self, size=8):
        self._buckets = [[] for _ in range(size)]
        self._entries = []
        self._len = 0

    def _bucket(self, key):
        return self._buckets[hash(key) % len(self._buckets)]

    def _find(self, bucket, key):
        """Позиция пары с ключом key в корзине или -1."""
        for pos, (k, _) in enumerate(bucket):
            if k == key:
                return pos
        return -1

    def _resize(self, new_size):
        # заодно убираем из _entries все None, которые остались после удалений
        self._entries = [e for e in self._entries if e is not None]
        self._buckets = [[] for _ in range(new_size)]
        for i, (key, _) in enumerate(self._entries):
            self._bucket(key).append((key, i))

    def __setitem__(self, key, value):
        bucket = self._bucket(key)
        pos = self._find(bucket, key)
        if pos != -1:
            i = bucket[pos][1]
            # перезапись не меняет порядок
            self._entries[i] = (key, value)
            return
        bucket.append((key, len(self._entries)))
        self._entries.append((key, value))
        self._len += 1
        if self._len > len(self._buckets) * 2 / 3:
            self._resize(len(self._buckets) * 2)

    def __getitem__(self, key):
        bucket = self._bucket(key)
        pos = self._find(bucket, key)
        if pos == -1:
            raise KeyError(key)
        return self._entries[bucket[pos][1]][1]

    def __delitem__(self, key):
        bucket = self._bucket(key)
        pos = self._find(bucket, key)
        if pos == -1:
            raise KeyError(key)
        _, i = bucket.pop(pos)
        self._entries[i] = None
        self._len -= 1
        # если пустых мест (None) в _entries стало слишком много, чистим список
        if len(self._entries) > 2 * self._len + 8:
            self._resize(len(self._buckets))

    def __contains__(self, key):
        return self._find(self._bucket(key), key) != -1

    def __len__(self):
        return self._len

    def get(self, key, default=None):
        bucket = self._bucket(key)
        pos = self._find(bucket, key)
        if pos == -1:
            return default
        return self._entries[bucket[pos][1]][1]

    def stats(self):
        longest = max(len(b) for b in self._buckets)
        return len(self._buckets), self._len, longest

    def items(self):
        return [e for e in self._entries if e is not None]

    def keys(self):
        return [k for k, _ in self.items()]

    def values(self):
        return [v for _, v in self.items()]

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        body = ', '.join(f'{k!r}: {v!r}' for k, v in self.items())
        return f'MyDict({{{body}}})'


class BadKey:
    """Ключ, у которого хеш всегда одинаковый."""

    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, BadKey) and self.v == other.v

    def __hash__(self):
        return 42


if __name__ == '__main__':
    import time

    d = MyDict()
    for i in range(1000):
        d[f'key{i}'] = i
    assert len(d) == 1000
    assert d['key42'] == 42
    assert 'key7' in d and 'nope' not in d
    d['key42'] = -1
    assert d['key42'] == -1 and len(d) == 1000
    del d['key42']
    assert 'key42' not in d and len(d) == 999
    assert d.get('nope') is None and d.get('nope', 0) == 0
    for bad in (lambda: d['nope'], lambda: d.__delitem__('nope')):
        try:
            bad()
            assert False, 'ожидали KeyError'
        except KeyError:
            pass
    buckets, size, longest = d.stats()
    assert size == 999 and size <= buckets * 2 / 3
    print(d.stats())

    # граничные случаи
    e = MyDict(size=1)
    assert len(e) == 0 and repr(e) == 'MyDict({})' and list(e) == []
    e[None] = 0
    e[(1, 2)] = 'tuple'
    # hash(-1) == hash(-2), значит оба ключа попадут в одну корзину
    e[-1] = 'neg'
    e[-2] = 'neg2'
    assert e[None] == 0 and e[(1, 2)] == 'tuple' and e[-1] == 'neg' and e[-2] == 'neg2'
    # если значение равно 0, get все равно возвращает его, а не default
    assert e.get(None, 'x') == 0
    e[1] = 'one'
    # 1 == True и хеши у них одинаковые, поэтому это один и тот же ключ, как в dict
    assert e[True] == 'one'
    try:
        e[[1]] = 1
        assert False, 'ожидали TypeError'
    except TypeError:
        pass
    assert repr(MyDict()) == 'MyDict({})'
    small = MyDict()
    small['a'] = 1
    small['b'] = 2
    assert repr(small) == "MyDict({'a': 1, 'b': 2})"

    # 1*: порядок добавления не ломается после увеличения таблицы и удалений
    o = MyDict()
    ref = {}
    for i in range(200):
        o[f'k{i}'] = i
        ref[f'k{i}'] = i
    for i in range(0, 200, 3):
        del o[f'k{i}']
        del ref[f'k{i}']
    # перезапись не меняет позицию
    o['k1'] = 'new'
    ref['k1'] = 'new'
    # ключ, который удалили и добавили снова, встает в конец
    o['k0'] = 'back'
    ref['k0'] = 'back'
    assert o.keys() == list(ref.keys())
    assert o.values() == list(ref.values())
    assert o.items() == list(ref.items())
    assert list(o) == list(ref)
    for k in list(ref):
        del o[k]
    assert len(o) == 0 and o.items() == [] and o.stats()[1] == 0

    # Эксперимент к вопросу 2
    def fill(keys):
        t = MyDict()
        start = time.perf_counter()
        for k in keys:
            t[k] = 1
        return time.perf_counter() - start, t.stats()

    t_str, st_str = fill([f'key{i}' for i in range(1000)])
    t_bad, st_bad = fill([BadKey(i) for i in range(1000)])
    print(f'строки:  stats={st_str}, вставка 1000 ключей: {t_str * 1000:.2f} мс')
    print(f'hash=42: stats={st_bad}, вставка 1000 ключей: {t_bad * 1000:.2f} мс')
    assert st_bad[2] == 1000

    print('my_dict: все проверки пройдены')


# Ответы на вопросы
#
# 1. Номер корзины считается как hash(key) % len(self._buckets), то есть зависит от того,
#    сколько всего корзин. Когда корзин становится в 2 раза больше, у того же ключа номер
#    корзины может поменяться: был i, а станет i или i + n. Если просто скопировать пары
#    на старые места, то при поиске мы посчитаем новый номер, заглянем не в ту корзину
#    и не найдем ключ, хотя он есть в таблице.
#
# 2. Для 1000 строк stats() выдает примерно (2048, 1000, 3): корзин в 2 раза больше,
#    чем ключей, хеши у строк разные, и ключи раскладываются по корзинам почти поровну.
#    В самой длинной корзине всего 3-5 ключей, поэтому поиск почти не зависит от размера
#    таблицы, это O(1) в среднем.
#    Если __hash__ всегда возвращает 42, все ключи падают в одну корзину:
#    stats() = (2048, 1000, 1000). Остальные 2047 корзин пустые, и по сути вся таблица
#    превращается в один длинный список. Каждый новый ключ приходится сравнивать через ==
#    со всеми, кто уже лежит в корзине, поэтому время растет как n^2. У меня вставка 1000
#    строк заняла ~2 мс, а 1000 таких ключей ~45 мс, примерно в 20 раз дольше. При 2000
#    ключей время выросло еще в 4 раза, а не в 2: это и есть рост как n^2.
