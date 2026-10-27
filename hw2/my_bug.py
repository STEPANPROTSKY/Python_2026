# багованный код 
students = ["Anna", "Bob", "Kate"]
homework = dict.fromkeys(students, [])   # у каждого студента свой список сданных ДЗ?

homework["Anna"].append("hw1")
homework["Bob"].append("hw2")

print(homework)
# {'Anna': ['hw1', 'hw2'], 'Bob': ['hw1', 'hw2'], 'Kate': ['hw1', 'hw2']}

# что происходит и почему
# Список [] создаётся один раз при вызове, и dict.fromkeys неявно раздаёт ссылку
# на этот один объект всем ключам - в коде нет ни одного присваивания, которое
# выдавало бы алиас. Поэтому append через любой ключ меняет общий список,
# и «сданные» ДЗ появляются у всех студентов.

# исправленная версия
students = ["Anna", "Bob", "Kate"]
homework = {name: [] for name in students}   # новый список на каждой итерации

homework["Anna"].append("hw1")
homework["Bob"].append("hw2")

print(homework)
# {'Anna': ['hw1'], 'Bob': ['hw2'], 'Kate': []}
