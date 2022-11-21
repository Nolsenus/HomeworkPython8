import sqlite3
from logger import log
from logger import log_return


DATABASE_NAME = 'students.db'


def get_tables():
    log('Попытка получить список таблиц...')
    con = sqlite3.connect(DATABASE_NAME)
    try:
        cur = con.cursor()
        tables = map(lambda x: x[0], cur.execute('SELECT name FROM sqlite_master'))
        tables = list(filter(lambda x: not x.startswith('sqlite'), tables))
        log('Успех.')
    except sqlite3.Error as error:
        tables = log_return(f'Ошибка: {error}')
    finally:
        con.close()
    return tables


def get_column_names(table: str):
    log(f'Попытка получить название столбцов из таблицы {table}...')
    con = sqlite3.connect(DATABASE_NAME)
    try:
        cur = con.cursor()
        result = list(map(lambda x: x[0], cur.execute(f"SELECT name FROM PRAGMA_TABLE_INFO('{table}')")))
        log('Успех.')
    except sqlite3.Error as error:
        result = log_return(f'Ошибка: {error}')
    finally:
        con.close()
    return result


def valid_condition(table: str, condition: list):
    log(f'Проверка условия {condition}...')
    if not condition:
        log('Успех, условия нет.')
        return True
    modded = []
    for cond in condition:
        mod = cond.replace('>', ';>').replace('<', ';<')
        if ';' not in mod:
            mod = mod.replace('=', ';=')
        modded.append(mod)
    splits = []
    for cond in modded:
        splits.append(cond.split(';'))
    columns = list(map(lambda x: x[0], splits))
    real_columns = get_column_names(table)
    real_columns.append('ROWID')
    for column in columns:
        if column not in real_columns:
            log('Успех, условие некорректно.')
            return False
    log('Успех, условие корректно.')
    return True


def condition_list_to_str(condition: list):
    return ' '.join(condition)


def add(row: dict, table: str):
    log(f'Попытка добавить строку {row} в таблицу {table}...')
    columns = get_column_names(table)
    if isinstance(columns, str):
        return log_return(columns)
    columns = columns[1:]
    con = sqlite3.connect(DATABASE_NAME)
    try:
        con.execute('PRAGMA foreign_keys = 1')
        cur = con.cursor()
        last_id = list(cur.execute(f'SELECT ROWID FROM {table} ORDER BY ROWID DESC LIMIT 1'))
        if last_id:
            last_id = last_id[0][0]
        else:
            last_id = 0
        if len(columns) == len(row.keys()):
            full_match = True
            values = [str(last_id + 1)]
            for column in columns:
                if column not in row.keys():
                    full_match = False
                    break
                values.append(row[column])
            if full_match:
                values = ', '.join(values)
                cur.execute(f'INSERT INTO {table} VALUES ({values});')
                con.commit()
                success = True
                log('Успех.')
            else:
                success = log_return('Ошибка: несовпадение столбцов в таблице и полученной строке.')
        else:
            success = log_return('Ошибка: '
                                 'количество столбцов таблицы не совпадает с количеством строк в полученной строке.')
    except sqlite3.Error as error:
        success = log_return(f'Ошибка: {error}.')
    finally:
        con.close()
    return success


def lookup(look_for: list, table: str, condition=None):
    log(f'Попытка поиска ({look_for}, {table}, {condition})...')
    columns = get_column_names(table)
    if isinstance(columns, str):
        return log_return(columns)
    columns = columns
    can_return = True
    for col in look_for:
        if col not in columns:
            can_return = False
            break
    if condition is None:
        condition = []
    if can_return and valid_condition(table, condition):
        if not look_for:
            look_for = '*'
        else:
            look_for = ', '.join(look_for)
        query = f'SELECT {look_for} FROM {table}'
        if condition:
            cond = condition_list_to_str(condition)
            query += ' WHERE ' + cond
        con = sqlite3.connect(DATABASE_NAME)
        try:
            cur = con.cursor()
            res = list(cur.execute(query))
            log('Успех.')
        except sqlite3.Error as error:
            res = log_return(f'Ошибка: {error}')
        finally:
            con.close()
    else:
        res = log_return('Ошибка: нельзя выделить указанные столбцы по указанному условию.')
    return res


def update(table: str, columns: list, values: list, condition=None):
    log(f'Попытка заменить столбцы {columns} в таблице {table} на значения {values} по условию {condition}...')
    if len(columns) != len(values):
        res = log_return('Ошибка: количество заменяемых значений не совпадает с количеством подставляемых значений.')
        return res
    column_names = get_column_names(table)[1:]
    columns_exist = True
    for column in columns:
        if column not in column_names:
            columns_exist = False
            break
    if condition is None:
        condition = []
    if columns_exist and valid_condition(table, condition):
        replacements = ', '.join(map(lambda x: '' + columns[x] + ' = ' + values[x], range(len(columns))))
        condition = condition_list_to_str(condition)
        con = sqlite3.connect(DATABASE_NAME)
        try:
            con.execute('PRAGMA foreign_keys = 1')
            cur = con.cursor()
            if condition:
                cur.execute(f'UPDATE {table} SET {replacements} WHERE {condition}')
            else:
                cur.execute(f'UPDATE {table} SET {replacements}')
            con.commit()
            log('Успех.')
            res = True
        except sqlite3.Error as error:
            res = log_return(f'Ошибка: {error}')
        finally:
            con.close()
    elif columns_exist:
        res = log_return(f'Ошибка: некорректное условие {condition}.')
    else:
        res = log_return(f'Ошибка: некорректные столбцы для замены {columns}.')
    return res


def update_ids(table):
    log('Обновление id...')
    ids = list(map(lambda x: x[0], lookup(['ROWID'], table)))
    if not ids:
        log('Успех - не осталось элементов.')
        return True
    con = sqlite3.connect(DATABASE_NAME)
    try:
        cur = con.cursor()
        if len(ids) == 1:
            if ids[0] != 1:
                cur.execute(f'UPDATE {table} SET ROWID = 1')
                log('Успех - id единственного оставшегося элемента установлен на 1.')
            else:
                log('Успех - id единственного оставшегося элемента уже 1.')
        else:
            correct_ids = list(range(1, 1 + len(ids)))
            if not correct_ids == ids:
                for i in range(len(ids)):
                    cur.execute(f'UPDATE {table} SET ROWID = {correct_ids[i]} WHERE ROWID = {ids[i]}')
                log('Успех - все id установлены на корректные значения.')
            else:
                log('Успех - все id уже установлены на корректные значения.')
        con.commit()
        res = True
    except sqlite3.Error as error:
        res = log_return(f'Ошибка: {error}')
    finally:
        con.close()
    return res


def delete(table: str, condition: list):
    log(f'Попытка удалить записи из таблицы {table} по условию {condition}...')
    if condition == ['']:
        condition = []
    if valid_condition(table, condition):
        con = sqlite3.connect(DATABASE_NAME)
        try:
            con.execute('PRAGMA foreign_keys = 1')
            cur = con.cursor()
            if condition:
                condition = condition_list_to_str(condition)
                cur.execute(f'DELETE FROM {table} WHERE {condition}')
            else:
                cur.execute(f'DELETE FROM {table}')
            con.commit()
            update_ids(table)
            log('Успех.')
            res = True
        except sqlite3.Error as error:
            res = log_return(f'Ошибка: {error}')
        finally:
            con.close()
    else:
        res = log_return(f'Ошибка: некорректное условие: {condition}')
    return res


def table_as_list_of_tuples(table: str):
    log(f'Попытка передать таблицу {table}...')
    con = sqlite3.connect(DATABASE_NAME)
    try:
        cur = con.cursor()
        res = list(cur.execute(f'SELECT * FROM {table}'))
        log('Успех.')
    except sqlite3.Error as error:
        res = log_return(f'Ошибка: {error}')
    finally:
        con.close()
    return res


def init():
    log('Инициализация базы данных...')
    connection = sqlite3.connect(DATABASE_NAME)
    try:
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE classes(
                           class_id INTEGER PRIMARY KEY ASC,
                           class_name TEXT NOT NULL UNIQUE);''')
        cursor.execute('''CREATE TABLE grades(
                               grade_id INTEGER PRIMARY KEY ASC,
                               grade_name TEXT NOT NULL UNIQUE);''')
        cursor.execute('''CREATE TABLE students(
                              id INTEGER PRIMARY KEY ASC,
                              s_surname TEXT NOT NULL,
                              s_name TEXT NOT NULL,
                              s_patronymic TEXT,
                              class INTEGER NOT NULL,
                              grade INTEGER NOT NULL,
                              FOREIGN KEY(class) REFERENCES classes(class_id),
                              FOREIGN KEY(grade) REFERENCES grades(grade_id));''')
        cursor.execute('''CREATE TABLE parents(
                              parent_id INTEGER PRIMARY KEY ASC,
                              p_surname TEXT NOT NULL,
                              p_name TEXT NOT NULL,
                              p_patronymic TEXT,
                              student_id INTEGER NOT NULL,
                              phone_number TEXT NOT NULL,
                              relation TEXT NOT NULL,
                              FOREIGN KEY(student_id) REFERENCES students(id));''')
        log('Успех.')
        res = True
    except sqlite3.Error as error:
        res = f'Ошибка - {str(error)}.'
    finally:
        connection.close()
    return res
