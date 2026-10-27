"""Трекер домашней библиотеки.

Коллекции:
  list  -> self._books        : меняющийся упорядоченный набор записей
  tuple -> Book (NamedTuple)  : фиксированная структура одной записи
  dict  -> self._by_id        : быстрый поиск книги по id за O(1)
  set   -> self._authors, Book.tags (frozenset) : важна только уникальность
"""

from typing import NamedTuple


class Book(NamedTuple):
    """Одна запись. NamedTuple - это tuple: неизменяемый и hashable.

    tags хранится как frozenset (а не list/set), чтобы запись оставалась
    полностью неизменяемой и её можно было класть в set / использовать как ключ.
    """
    id: int
    title: str
    author: str
    year: int
    tags: frozenset[str] = frozenset()  # неизменяемый default => безопасно


class Library:
    def __init__(self) -> None:
        # каждый экземпляр получает свои коллекции (не атрибуты класса)
        self._books: list[Book] = []
        self._by_id: dict[int, Book] = {}
        self._authors: set[str] = set()
        self._next_id = 1

    def add(self, title: str, author: str, year: int,
            tags: list[str] | None = None) -> Book:
        # None вместо [] в аргументе по умолчанию - никакого общего списка
        book = Book(self._next_id, title, author, year,
                    frozenset(tags) if tags is not None else frozenset())
        self._next_id += 1
        self._books.append(book)
        self._by_id[book.id] = book
        self._authors.add(author)
        return book

    def get(self, book_id: int) -> Book | None:
        return self._by_id.get(book_id)

    def remove(self, book_id: int) -> bool:
        book = self._by_id.pop(book_id, None)
        if book is None:
            return False
        # не удаляем во время итерации по тому же списку - строим новый
        self._books = [b for b in self._books if b.id != book_id]
        # автора убираем, только если у него не осталось книг
        if all(b.author != book.author for b in self._books):
            self._authors.discard(book.author)
        return True

    def update_year(self, book_id: int, year: int) -> Book | None:
        """Запись неизменяема, поэтому создаём новую через _replace."""
        old = self._by_id.get(book_id)
        if old is None:
            return None
        new = old._replace(year=year)
        self._by_id[book_id] = new
        self._books = [new if b.id == book_id else b for b in self._books]
        return new

    def books(self) -> list[Book]:
        # отдаём копию, так внешний код не сможет случайно изменить внутренний список
        return list(self._books)

    def authors(self) -> frozenset[str]:
        # frozenset - снаружи нельзя изменить внутреннее множество
        return frozenset(self._authors)

    def sorted_by_year(self) -> list[Book]:
        # sorted() возвращает новый список и не трогает исходный
        return sorted(self._books, key=lambda b: b.year)

    def all_tags(self) -> set[str]:
        return set().union(*(b.tags for b in self._books))


if __name__ == "__main__":
    lib = Library()
    lib.add("Мастер и Маргарита", "Булгаков", 1967, ["роман", "классика"])
    lib.add("Собачье сердце", "Булгаков", 1925, ["повесть", "классика"])
    lib.add("Пикник на обочине", "Стругацкие", 1972, ["фантастика"])
    lib.add("Дюна", "Херберт", 1965)

    print("Все книги:")
    for b in lib.books():
        print(" ", b)

    print("\nПоиск по id=3:", lib.get(3))
    print("Уникальные авторы:", sorted(lib.authors()))
    print("Все теги:", sorted(lib.all_tags()))

    # попытка изменить снаружи не ломает библиотеку
    snapshot = lib.books()
    snapshot.clear()
    print("\nПосле очистки копии в библиотеке осталось:", len(lib.books()))

    # запись неизменяема
    try:
        lib.get(1).year = 2000
    except AttributeError as e:
        print("Запись изменить нельзя:", e)

    print("\nОбновили год:", lib.update_year(4, 1966))
    print("Удалили id=3:", lib.remove(3))
    print("Авторы после удаления:", sorted(lib.authors()))

    print("\nПо году:", [(b.title, b.year) for b in lib.sorted_by_year()])

    # Book hashable - можно класть в set
    print("Книги в set:", len(set(lib.books())))
