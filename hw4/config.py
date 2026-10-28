"""Задание 6*. Конфиг с доступом к вложенному словарю через точку"""


class Config:
    def __init__(self, data):
        # self._data = data вызвал бы наш __setattr__, и _data стал бы ключом в словаре
        object.__setattr__(self, '_data', data)

    def __getattr__(self, name):
        # этот метод вызывается, только если атрибут не нашелся обычным способом
        if name == '_data':
            # _data может не быть, если объект создан без __init__ (например, через copy).
            # Без этой проверки self._data ниже снова вызвал бы __getattr__, и так по кругу
            raise AttributeError(name)
        try:
            value = self._data[name]
        except KeyError:
            raise AttributeError(f'в конфиге нет ключа {name!r}') from None
        if isinstance(value, dict):
            # оборачиваем тот же самый словарь, а не копию
            return Config(value)
        return value

    def __setattr__(self, name, value):
        if isinstance(value, Config):
            value = value._data
        self._data[name] = value

    def __delattr__(self, name):
        try:
            del self._data[name]
        except KeyError:
            raise AttributeError(name) from None

    def __dir__(self):
        # обычные атрибуты объекта плюс ключи словаря
        return sorted(set(object.__dir__(self)) | self._data.keys())

    def to_dict(self):
        return self._data

    def __repr__(self):
        return f'Config({self._data!r})'


if __name__ == '__main__':
    raw = {'db': {'host': 'localhost', 'port': 5432}, 'debug': True}
    cfg = Config(raw)
    assert cfg.debug is True
    assert cfg.db.host == 'localhost' and cfg.db.port == 5432
    assert getattr(cfg, 'timeout', 30) == 30
    assert hasattr(cfg.db, 'user') is False
    # запись меняет исходный словарь
    cfg.db.port = 6543
    assert raw['db']['port'] == 6543
    cfg.timeout = 10
    assert raw['timeout'] == 10
    assert cfg.to_dict() is raw
    # подсказка: метод __dir__
    assert 'db' in dir(cfg)

    # свои проверки
    assert 'host' in dir(cfg.db) and 'to_dict' in dir(cfg)
    assert cfg.db.to_dict() is raw['db']
    try:
        cfg.missing
        assert False, 'ожидали AttributeError'
    except AttributeError:
        pass

    # новый словарь внутри конфига тоже доступен через точку
    cfg.cache = {'ttl': 60}
    assert cfg.cache.ttl == 60
    cfg.cache.ttl = 120
    assert raw['cache'] == {'ttl': 120}

    # если присвоить Config, в словарь запишется словарь, а не обертка
    cfg.db_copy = cfg.db
    assert raw['db_copy'] is raw['db']

    del cfg.timeout
    assert 'timeout' not in raw and not hasattr(cfg, 'timeout')

    deep = Config({'a': {'b': {'c': {'d': 1}}}})
    deep.a.b.c.d = 2
    assert deep.to_dict()['a']['b']['c']['d'] == 2

    lst = Config({'items': [1, 2], 'nothing': None})
    assert lst.items == [1, 2] and lst.nothing is None
    # ключ есть, хотя значение у него None
    assert hasattr(lst, 'nothing')

    import copy
    # без проверки на _data в __getattr__ тут была бы ошибка RecursionError
    c2 = copy.copy(cfg)
    assert c2.db.host == 'localhost'

    print('config: все проверки пройдены')


# 1. hasattr(obj, name) и getattr(obj, name, default) ловят только AttributeError.
#    Для Python это сигнал "такого атрибута нет". Если __getattr__ бросит KeyError,
#    getattr не вернет default, а hasattr не вернет False: ошибка просто вылетит
#    наружу, и любой код, который проверяет настройку через hasattr или getattr,
#    будет падать.
#
# 2. Словарь лежит в атрибуте _data. Записываю его через object.__setattr__, минуя
#    свой __setattr__, иначе _data попал бы ключом в сам словарь. Когда потом читаем
#    self._data, Python находит его обычным способом в __dict__ объекта, и __getattr__
#    вообще не вызывается, поэтому зацикливания нет.
#    Но объект можно создать и без __init__ (так делает copy.copy). Тогда _data нет,
#    и self._data внутри __getattr__ снова вызвал бы __getattr__, тот снова self._data,
#    и так до RecursionError. Поэтому в начале __getattr__ стоит проверка: если просят
#    _data, сразу бросаем AttributeError.
