from logger import log
from dbwork import get_tables
from dbwork import get_column_names
from dbwork import add
from dbwork import delete
from dbwork import update
from dbwork import lookup
from dbwork import table_as_list_of_tuples


def start(mode):
    if mode == 'console':
        console()


def notify(mode, message):
    if mode == 'console':
        print(message)


def console():
    log('Запущен консольный интерфейс.')
    while True:
        log('Запущено меню.')
        command = input('Введите команду, чтобы увидеть список команд введите "помощь": ')
        match command.lower():
            case 'помощь':
                log('Вызван список команд.')
                print('помощь - вывод списка команд.\n'
                      'добавить - переход в режим добавления строк в таблицы.\n'
                      'поиск - переход в режим поиска по базе данных.\n'
                      'удалить - переход в режим удаления записей из базы данных.\n'
                      'изменить - переход в режим изменения записей в базе данных.\n'
                      'показать - переход в режим показа таблиц.\n'
                      'выход - завершение работы программы.')
            case 'добавить': console_add()
            case 'поиск': console_lookup()
            case 'удалить': console_delete()
            case 'изменить': console_update()
            case 'показать': console_show()
            case 'выход': break
            case _: print('Вы ввели что-то не то, попробуйте снова.')


def console_choose_table():
    log('Выбор таблицы.')
    tables = get_tables()
    tables.append('назад')
    while True:
        table = input('Введите название таблицы, с которой хотите работать '
                      f'({", ".join(tables[:-1])}) или "назад", чтобы вернуться в меню: ')
        if table in tables:
            if table == 'назад':
                log('Отмена.')
            else:
                log(f'Выбрана таблица {table}.')
            return table
        print(f'Таблицы {table} не существует.')


def console_add():
    log('Переход в режим добавления строк в таблицы.')
    while True:
        table = console_choose_table()
        if table == 'назад':
            return
        columns = get_column_names(table)[1:]
        while True:
            if isinstance(columns, str):
                notify('console', columns)
                break
            row = dict({})
            canceled = False
            log('Ввод строки.')
            print('Вводите строку таблицы для добавления.')
            for column in columns:
                log(f'Ввод значения для столбца {column}.')
                inp = input(f'Введите значение для столбца {column}, '
                            'строчные значения обёртывайте в двойные кавычки ("пример"),'
                            'или введите "отмена" для возвращения к выбору таблицы: ')
                if inp.lower() == 'отмена':
                    canceled = True
                    log('Отмена.')
                    break
                log(f'Введено значение {inp}.')
                row[column] = inp
            if canceled:
                break
            res = add(row, table)
            if res is True:
                res = 'Успех.'
            notify('console', res)


def parse_condition(string: str):
    string = string.replace('*', ' AND;').replace('+', ' OR;')
    conditions = string.split(';')
    return conditions


def console_lookup():
    log('Переход в режим поиска по базе данных.')
    while True:
        table = console_choose_table()
        if table == 'назад':
            break
        columns = get_column_names(table)
        columns_copy = []
        for col in columns:
            columns_copy.append(col)
        canceled = False
        log('Выбор возвращаемых столбцов.')
        look_for = []
        while True:
            while True:
                inp = input(f'Введите название столбца из списка ({", ".join(columns_copy)}), '
                            f'данные из которого вы хотели бы получить,\n'
                            f'чтобы выбрать все столбцы сразу введите "все",\n'
                            f'чтобы закончить выбирать введите "дальше",\n'
                            f'чтобы вернуться к выбору таблицы введите "отмена": ')
                if inp.lower() == 'отмена':
                    canceled = True
                    log('Отмена.')
                    break
                elif inp.lower() == 'дальше':
                    if look_for:
                        log(f'Выбранные столбцы: {look_for}')
                        break
                    else:
                        print('Необходимо выбрать хотя бы оин столбец.')
                elif inp == 'все':
                    for col in columns_copy:
                        look_for.append(col)
                    log('Выбраны все столбцы.')
                    break
                elif inp in columns_copy:
                    columns_copy.remove(inp)
                    look_for.append(inp)
                    if not columns_copy:
                        log('Выбраны все столбцы.')
                        break
                else:
                    print('Вы ввели что-то не то.')
            if canceled:
                break
            log('Ввод условия.')
            condition = parse_condition(input('Введите условие, по которому отбирать строки, вместо и ставьте "*", '
                                              'вместо или ставьте"+", '
                                              'чтобы вывести все строки, введите пустую строку: '))
            if condition == ['']:
                res = lookup(look_for, table)
            else:
                res = lookup(look_for, table, condition)
            if isinstance(res, list):
                print_rows(res)
            else:
                notify('console', res)
            if columns != columns_copy:
                columns_copy = []
                for col in columns:
                    columns_copy.append(col)
            look_for = []


def print_rows(rows: list):
    for row in rows:
        print(row)


def console_delete():
    log('Переход в режим удаления строк из базы данных.')
    while True:
        table = console_choose_table()
        if table == 'назад':
            break
        while True:
            inp = input('Введите условие, по которому удалять записи из таблицы, '
                        'чтобы удалить все записи введите пустую строку, '
                        'чтобы вернуться к выбору таблицы введите "отмена": ')
            if inp.lower() == 'отмена':
                break
            condition = parse_condition(inp)
            res = delete(table, condition)
            if res is True:
                res = 'Успех.'
            notify('console', res)


def console_update():
    log('Переход в режим изменения данных в таблице.')
    while True:
        table = console_choose_table()
        if table == 'назад':
            break
        columns = get_column_names(table)
        log('Выбор столбца.')
        column_to_replace = ''
        while True:
            inp = input(f'Введите название столбца из списка ({", ".join(columns)}), '
                        f'данные из которого вы хотели бы заменить,\n'
                        f'чтобы вернуться к выбору таблицы введите "отмена": ')
            if inp.lower() == 'отмена':
                log('Отмена.')
                break
            if inp in columns:
                column_to_replace = inp
                log(f'Выбран столбец {column_to_replace}')
                break
            else:
                print('Вы ввели что-то не то.')
        value = None
        if column_to_replace:
            log('Ввод значения.')
            inp = input('Введите значение, на которое хотите заменить данные выбранного столбца, '
                        'для отмены введите "отмена": ')
            if inp.lower() != 'отмена':
                value = inp
                log(f'Введённое значение - {value}')
            else:
                log('Отмена.')
        if value:
            inp = input('Введите условие, по которому отбирать строчки, в которых производить замену, '
                        'чтобы произвести замену во всех записях введите пустую строку, '
                        'чтобы вернуться к выбору таблицы введите "отмена": ')
            if inp.lower() == 'отмена':
                log('Отмена.')
                break
            if inp:
                inp = parse_condition(inp)
                res = update(table, [column_to_replace], [value], inp)
            else:
                res = update(table, [column_to_replace], [value])
            if res is True:
                res = 'Успех.'
            notify('console', res)


def console_show():
    log('Переход в режим показа таблиц.')
    while True:
        table = console_choose_table()
        if table == 'назад':
            break
        print_rows(table_as_list_of_tuples(table))
