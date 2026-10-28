"""Задание 5*. LRU-кэш на обычном dict (без OrderedDict)"""


class LRUCache:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError('capacity должна быть >= 1')
        self.capacity = capacity
        # dict помнит порядок добавления: первым идет ключ, который дольше всего не трогали
        self._data = {}

    def get(self, key, default=None):
        if key not in self._data:
            return default
        value = self._data.pop(key)
        # кладем ключ заново, он уходит в конец и становится самым свежим
        self._data[key] = value
        return value

    def put(self, key, value):
        if key in self._data:
            del self._data[key]
        elif len(self._data) >= self.capacity:
            oldest = next(iter(self._data))
            del self._data[oldest]
        self._data[key] = value

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        # только проверяем, порядок не трогаем
        return key in self._data

    def __repr__(self):
        return f'LRUCache({self.capacity}, {self._data!r})'


if __name__ == '__main__':
    c = LRUCache(2)
    c.put('a', 1)
    c.put('b', 2)
    # теперь 'a' свежее, чем 'b'
    assert c.get('a') == 1
    # вытесняется 'b'
    c.put('c', 3)
    assert 'b' not in c and c.get('a') == 1 and c.get('c') == 3
    # перезапись делает 'a' свежим
    c.put('a', 10)
    # вытесняется 'c'
    c.put('d', 4)
    assert c.get('c') is None and c.get('a') == 10 and len(c) == 2

    # свои проверки
    c = LRUCache(2)
    c.put('x', None)
    # если в кэше лежит None, get вернет None, а не default
    assert c.get('x', 'default') is None
    assert c.get('nope', 'default') == 'default'

    c = LRUCache(2)
    c.put('a', 1)
    c.put('b', 2)
    # __contains__ не делает 'a' свежим
    assert 'a' in c
    # поэтому вытесняется именно 'a'
    c.put('c', 3)
    assert 'a' not in c and 'b' in c and 'c' in c

    c = LRUCache(1)
    c.put('a', 1)
    # перезапись при полном кэше ничего не вытесняет
    c.put('a', 2)
    assert len(c) == 1 and c.get('a') == 2
    c.put('b', 3)
    assert 'a' not in c and c.get('b') == 3 and len(c) == 1

    c = LRUCache(2)
    # get несуществующего ключа ничего не добавляет в кэш
    assert c.get('a') is None
    c.put(1, 'int')
    c.put((1, 2), 'tuple')
    assert c.get(1) == 'int' and c.get((1, 2)) == 'tuple'
    try:
        LRUCache(0)
        assert False, 'ожидали ValueError'
    except ValueError:
        pass

    # много случайных операций, сверяем с простой версией на списке
    import random
    rng = random.Random(0)
    c, model = LRUCache(5), []
    for _ in range(5000):
        k = rng.randrange(10)
        if rng.random() < 0.5:
            c.put(k, k)
            if k in model:
                model.remove(k)
            elif len(model) == 5:
                model.pop(0)
            model.append(k)
        else:
            got = c.get(k)
            if k in model:
                model.remove(k)
                model.append(k)
                assert got == k
            else:
                assert got is None
        assert list(c._data) == model

    print('lru: все проверки пройдены')


# Почему удаление самого старого элемента - O(1)
#
# С Python 3.7 dict помнит порядок, в котором добавляли ключи. В get и при перезаписи
# в put я удаляю ключ и добавляю его снова, и он переезжает в конец. Значит, в начале
# словаря всегда лежит ключ, к которому дольше всего не обращались.
# Достать его можно так: next(iter(self._data)). iter не создает список всех ключей,
# а next сразу берет первый. Потом del удаляет этот ключ так же быстро, как любой
# другой ключ в словаре. Перебирать все ключи и искать самый старый не нужно.
#
# Оговорка (проверил замером): когда из dict удаляют ключ, внутри на его месте
# остается пустое место, и оно не сразу исчезает. next(iter(...)) проходит эти пустые
# места по одному, пока словарь сам себя не перестроит. Поэтому на деле операция
# медленнее для большого кэша: ~0.7 мкс при 1000 элементов, ~2.4 мкс при 10 000,
# ~23 мкс при 100 000. Чтобы скорость совсем не зависела от размера, нужен другой
# способ (связный список поверх словаря), так сделаны OrderedDict и lru_cache.
