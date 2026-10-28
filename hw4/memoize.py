"""Задание 4. Кэширование через замыкание"""


def memoize(func):
    # кэш лежит во внешней функции, а wrapper видит его через замыкание
    cache = {}

    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        try:
            hash(key)
        except TypeError:
            # аргументы нельзя захешировать (например, список), поэтому просто вызываем функцию
            return func(*args, **kwargs)
        if key in cache:
            wrapper.hits += 1
            return cache[key]
        wrapper.misses += 1
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    def cache_clear():
        cache.clear()
        wrapper.hits = 0
        wrapper.misses = 0

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    # у функции есть свой __dict__, как у любого объекта, туда кладем счетчики и метод
    wrapper.hits = 0
    wrapper.misses = 0
    wrapper.cache_clear = cache_clear
    return wrapper


if __name__ == '__main__':
    import time

    calls = []

    def slow_square(x, power=2):
        '''Возводит в степень.'''
        calls.append(x)
        return x ** power

    sq = memoize(slow_square)
    assert sq(3) == 9 and sq(3) == 9 and sq(3, power=3) == 27
    assert calls == [3, 3]
    assert (sq.hits, sq.misses) == (1, 2)
    assert sq.__name__ == 'slow_square' and sq.__doc__ == 'Возводит в степень.'
    total = memoize(sum)
    # нехешируемый аргумент: вызов без кэша
    assert total([1, 2, 3]) == 6 and total([1, 2, 3]) == 6
    assert (total.hits, total.misses) == (0, 0)
    sq.cache_clear()
    assert (sq.hits, sq.misses) == (0, 0)
    sq(3)
    assert calls[-1] == 3

    # свои проверки
    def f(a, b=0, c=0):
        calls.append((a, b, c))
        return a + b + c

    mf = memoize(f)
    calls.clear()
    # разные kwargs - разные ключи
    assert mf(1, b=2) == 3 and mf(1, b=3) == 4
    # порядок kwargs не важен
    assert mf(1, b=2, c=3) == 6 and mf(1, c=3, b=2) == 6
    assert len(calls) == 3 and (mf.hits, mf.misses) == (1, 3)
    mlen = memoize(lambda seq, extra=(): len(seq) + len(extra))
    # кортежи хешируемы - кэшируются
    assert mlen((1, 2)) == 2 and mlen((1, 2)) == 2
    assert (mlen.hits, mlen.misses) == (1, 1)
    # нехешируемый kwarg - без кэша
    assert mlen((1,), extra=[1, 2]) == 3
    assert (mlen.hits, mlen.misses) == (1, 1)

    none_calls = []

    def returns_none():
        none_calls.append(1)

    mn = memoize(returns_none)
    mn()
    mn()
    # None тоже кэшируется
    assert len(none_calls) == 1 and (mn.hits, mn.misses) == (1, 1)

    def boom(x):
        raise TypeError('ошибка внутри функции')

    try:
        # если ошибка TypeError возникла в самой функции, ее не прячем
        memoize(boom)(1)
        assert False, 'ожидали TypeError'
    except TypeError as e:
        assert 'внутри' in str(e)

    # у каждой обертки свой кэш
    other = memoize(slow_square)
    assert (other.hits, other.misses) == (0, 0)

    # Эксперимент с рекурсией
    def fib(n):
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    # вариант A
    fast_fib = memoize(fib)
    start = time.perf_counter()
    assert fast_fib(30) == 832040
    t_a = time.perf_counter() - start
    print(f'A: fast_fib = memoize(fib): misses={fast_fib.misses}, {t_a:.3f} c')

    # вариант B
    fib = memoize(fib)
    start = time.perf_counter()
    assert fib(30) == 832040
    t_b = time.perf_counter() - start
    print(f'B: fib = memoize(fib):      misses={fib.misses}, {t_b * 1000:.3f} мс')
    print(f'B быстрее A в {t_a / t_b:.0f} раз')
    assert fast_fib.misses == 1 and fib.misses == 31

    print('memoize: все проверки пройдены')


# Почему вариант B ускоряет, а A почти нет (правило LEGB)
#
# Внутри fib стоит вызов fib(n - 1). Python ищет, что такое fib, не когда функцию
# написали, а каждый раз, когда этот вызов выполняется. Поиск идет по LEGB: в Local
# (внутри fib) такого имени нет, в Enclosing тоже нет, и оно находится в Global.
# Вариант A: мы создали новое имя fast_fib, а имя fib в Global по-прежнему указывает на
# обычную функцию без кэша. Через кэш проходит только первый вызов fast_fib(30)
# (misses = 1), а все рекурсивные вызовы (~1.3 млн) идут в обычную fib, мимо кэша.
# Поэтому работает так же медленно, как без memoize.
# Вариант B: мы записали обертку в то же имя fib. Когда старая функция внутри вызывает
# fib(n - 1), она ищет fib в Global и находит уже обертку с кэшем. Каждое значение от
# fib(0) до fib(30) считается только один раз (misses = 31), дальше берется из кэша.
# Вместо ~1.3 млн вызовов получается около 60, и у меня это ~0.07 мс против ~0.1 с,
# примерно в 1600 раз быстрее.
