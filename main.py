import sqlite3

from ui import start
from logger import log
from dbwork import init
from pathlib import Path
from dbwork import add
from dbwork import lookup
from dbwork import table_as_list_of_tuples
from dbwork import update
from dbwork import delete


def main():
    log('Программа запущена.')
    can_start = False
    mode = ''
    while not can_start:
        user_input = input('Введите "консоль", чтобы работать с консолью '
                           'или "Отмена", чтобы прекратить работу программы: ')
        if user_input.lower() == 'консоль':
            mode = 'console'
            can_start = True
            log('Выбран консольный интерфейс.')
        elif user_input.lower() == 'отмена':
            can_start = True
            log('Отмена.')
        else:
            print('Вы ввели что-то не то, попробуйте снова.')
            log(f'Введено "{user_input}", повтор.')
    if mode:
        db = Path('./students.db')
        if not db.is_file():
            success = init()
            if success is not True:
                print(success)
                return
        start(mode)
    log('Завершение работы программы.')


def test():
    print(bool(None))


if __name__ == '__main__':
    main()
