"""Задание 2. Хешируемый неизменяемый класс-значение Money."""


class Money:
    __slots__ = ('amount', 'currency')

    def __init__(self, amount, currency):
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError('amount - целое число копеек')
        if not isinstance(currency, str):
            raise TypeError('currency - строка')
        # self.amount = ... не сработает из-за нашего __setattr__, поэтому пишем через object
        object.__setattr__(self, 'amount', amount)
        object.__setattr__(self, 'currency', currency)

    def __setattr__(self, name, value):
        raise AttributeError(f'Money неизменяем: нельзя установить {name!r}')

    def __delattr__(self, name):
        raise AttributeError(f'Money неизменяем: нельзя удалить {name!r}')

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return (self.amount, self.currency) == (other.amount, other.currency)

    def __hash__(self):
        # хеш считаем по тем же полям, что и сравнение: если a == b, то и хеши равны
        return hash((self.amount, self.currency))

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f'нельзя сложить {self.currency} и {other.currency}')
        return Money(self.amount + other.amount, self.currency)

    def __repr__(self):
        return f'Money({self.amount}, {self.currency!r})'


def total_by_currency(payments):
    totals = {}
    for m in payments:
        totals[m.currency] = totals[m.currency] + m if m.currency in totals else m
    return totals


if __name__ == '__main__':
    assert len({Money(100, 'RUB'), Money(100, 'RUB'), Money(100, 'USD')}) == 2
    prices = {Money(100, 'RUB'): 'сто рублей'}
    assert prices[Money(100, 'RUB')] == 'сто рублей'
    assert Money(100, 'RUB') + Money(50, 'RUB') == Money(150, 'RUB')
    for action in (lambda m: setattr(m, 'amount', 5), lambda m: setattr(m, 'extra', 1)):
        try:
            action(Money(1, 'RUB'))
            assert False, 'ожидали AttributeError'
        except AttributeError:
            pass
    try:
        Money(1, 'RUB') + Money(1, 'USD')
        assert False, 'ожидали ValueError'
    except ValueError:
        pass
    pays = [Money(100, 'RUB'), Money(5, 'USD'), Money(250, 'RUB')]
    assert total_by_currency(pays) == {'RUB': Money(350, 'RUB'), 'USD': Money(5, 'USD')}

    # свои проверки
    a, b = Money(100, 'RUB'), Money(100, 'RUB')
    assert a == b and a is not b and hash(a) == hash(b)
    assert Money(100, 'RUB') != Money(100, 'USD') and Money(1, 'RUB') != Money(2, 'RUB')
    assert Money(100, 'RUB').__eq__(100) is NotImplemented
    assert Money(100, 'RUB') != 100 and Money(100, 'RUB') != (100, 'RUB')
    assert repr(Money(1500, 'RUB')) == "Money(1500, 'RUB')"
    assert eval(repr(Money(-7, 'USD'))) == Money(-7, 'USD')

    # + возвращает новый объект, исходные не меняются
    s = a + b
    assert s is not a and a == Money(100, 'RUB') and s == Money(200, 'RUB')
    try:
        a + 5
        assert False, 'ожидали TypeError'
    except TypeError:
        pass

    for bad in (lambda: delattr(a, 'amount'), lambda: setattr(a, 'currency', 'USD')):
        try:
            bad()
            assert False, 'ожидали AttributeError'
        except AttributeError:
            pass
    assert not hasattr(a, '__dict__')
    assert a == Money(100, 'RUB')

    for bad_args in ((1.5, 'RUB'), ('100', 'RUB'), (True, 'RUB'), (100, None)):
        try:
            Money(*bad_args)
            assert False, 'ожидали TypeError'
        except TypeError:
            pass

    assert total_by_currency([]) == {}
    original = [Money(1, 'RUB')]
    totals = total_by_currency(original)
    assert totals == {'RUB': Money(1, 'RUB')} and original == [Money(1, 'RUB')]

    print('money: все проверки пройдены')


# Что сломалось бы, если бы поля можно было менять
#
# set и dict выбирают корзину для объекта по его хешу один раз, когда объект добавляют,
# и потом этот хеш не пересчитывают. В примере с Point из лекции (p = Point(1, 2);
# visited = {p}; p.x = 100; p in visited -> False) после изменения поля у объекта стал
# другой хеш. Поэтому поиск идет в другую корзину и не находит p, хотя p лежит в множестве.
# А если искать Point(1, 2), то корзина будет правильная, но объект в ней уже равен
# Point(100, 2), и сравнение не сработает. Получается, что элемент нельзя ни найти,
# ни удалить, в множество можно добавить его "второй раз", а значение в словаре по такому
# ключу уже не достать. Money изменить нельзя, поэтому его хеш всегда остается тем же,
# с которым его положили.
