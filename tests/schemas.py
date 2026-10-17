"""Схеми й початкові дані трьох наборів (збігаються з файлами data/schema_setN.sql) і параметри наборів."""

SCHEMAS = {1: '-- Набір 1: бібліотека\n'
    'CREATE TABLE book (\n'
    '    id     integer PRIMARY KEY,\n'
    '    title  text    NOT NULL,\n'
    '    copies integer NOT NULL CHECK (copies >= 0)\n'
    ');\n'
    'INSERT INTO book (id, title, copies) VALUES\n'
    "    (1, 'Лісова пісня', 10),\n"
    "    (2, 'Intermezzo', 6),\n"
    "    (3, 'Тіні забутих предків', 4);\n"
    '\n'
    'CREATE TABLE loan (\n'
    '    id      integer PRIMARY KEY,\n'
    '    book_id integer NOT NULL REFERENCES book (id),\n'
    '    reader  text    NOT NULL,\n'
    '    copies  integer NOT NULL\n'
    ');\n'
    'INSERT INTO loan (id, book_id, reader, copies) VALUES\n'
    "    (1, 1, 'Оксана', 1),\n"
    "    (2, 1, 'Тарас', 2),\n"
    "    (3, 2, 'Оксана', 1);\n"
    '\n'
    'CREATE TABLE librarian (\n'
    '    id        integer PRIMARY KEY,\n'
    '    full_name text    NOT NULL,\n'
    '    on_shift  boolean NOT NULL\n'
    ');\n'
    'INSERT INTO librarian (id, full_name, on_shift) VALUES\n'
    "    (1, 'Іваненко', true),\n"
    "    (2, 'Мельник', true),\n"
    "    (3, 'Коваль', false);\n"
    '\n'
    'CREATE TABLE hold (\n'
    '    id      integer PRIMARY KEY,\n'
    '    book_id integer NOT NULL REFERENCES book (id),\n'
    "    state   text    NOT NULL CHECK (state IN ('new', 'done')),\n"
    '    handler text\n'
    ');\n'
    'INSERT INTO hold (id, book_id, state, handler) VALUES\n'
    "    (1, 1, 'new', NULL),\n"
    "    (2, 2, 'new', NULL),\n"
    "    (3, 3, 'new', NULL),\n"
    "    (4, 1, 'done', 'Іваненко');\n",
 2: '-- Набір 2: магазин\n'
    'CREATE TABLE product (\n'
    '    id    integer PRIMARY KEY,\n'
    '    title text    NOT NULL,\n'
    '    stock integer NOT NULL CHECK (stock >= 0)\n'
    ');\n'
    'INSERT INTO product (id, title, stock) VALUES\n'
    "    (1, 'Бездротова миша', 25),\n"
    "    (2, 'Клавіатура', 14),\n"
    "    (3, 'Монітор', 8);\n"
    '\n'
    'CREATE TABLE purchase (\n'
    '    id         integer PRIMARY KEY,\n'
    '    product_id integer NOT NULL REFERENCES product (id),\n'
    '    customer   text    NOT NULL,\n'
    '    quantity   integer NOT NULL\n'
    ');\n'
    'INSERT INTO purchase (id, product_id, customer, quantity) VALUES\n'
    "    (1, 1, 'Андрій', 2),\n"
    "    (2, 1, 'Ірина', 1),\n"
    "    (3, 1, 'Максим', 3),\n"
    "    (4, 2, 'Ірина', 1);\n"
    '\n'
    'CREATE TABLE courier (\n'
    '    id        integer PRIMARY KEY,\n'
    '    full_name text    NOT NULL,\n'
    '    on_route  boolean NOT NULL\n'
    ');\n'
    'INSERT INTO courier (id, full_name, on_route) VALUES\n'
    "    (1, 'Бондар', true),\n"
    "    (2, 'Шевчук', true),\n"
    "    (3, 'Кравець', false);\n"
    '\n'
    'CREATE TABLE order_job (\n'
    '    id         integer PRIMARY KEY,\n'
    '    product_id integer NOT NULL REFERENCES product (id),\n'
    "    state      text    NOT NULL CHECK (state IN ('new', 'done')),\n"
    '    handler    text\n'
    ');\n'
    'INSERT INTO order_job (id, product_id, state, handler) VALUES\n'
    "    (1, 1, 'new', NULL),\n"
    "    (2, 2, 'new', NULL),\n"
    "    (3, 3, 'new', NULL),\n"
    "    (4, 1, 'done', 'Бондар');\n",
 3: '-- Набір 3: фітнес-клуб\n'
    'CREATE TABLE workout (\n'
    '    id    integer PRIMARY KEY,\n'
    '    title text    NOT NULL,\n'
    '    seats integer NOT NULL CHECK (seats >= 0)\n'
    ');\n'
    'INSERT INTO workout (id, title, seats) VALUES\n'
    "    (1, 'Йога', 12),\n"
    "    (2, 'Пілатес', 9),\n"
    "    (3, 'Кросфіт', 6);\n"
    '\n'
    'CREATE TABLE booking (\n'
    '    id         integer PRIMARY KEY,\n'
    '    workout_id integer NOT NULL REFERENCES workout (id),\n'
    '    member     text    NOT NULL,\n'
    '    places     integer NOT NULL\n'
    ');\n'
    'INSERT INTO booking (id, workout_id, member, places) VALUES\n'
    "    (1, 1, 'Марта', 1),\n"
    "    (2, 1, 'Денис', 2),\n"
    "    (3, 1, 'Софія', 1),\n"
    "    (4, 1, 'Роман', 1),\n"
    "    (5, 2, 'Марта', 1);\n"
    '\n'
    'CREATE TABLE trainer (\n'
    '    id        integer PRIMARY KEY,\n'
    '    full_name text    NOT NULL,\n'
    '    on_floor  boolean NOT NULL\n'
    ');\n'
    'INSERT INTO trainer (id, full_name, on_floor) VALUES\n'
    "    (1, 'Гнатюк', true),\n"
    "    (2, 'Лисенко', true),\n"
    "    (3, 'Павленко', false);\n"
    '\n'
    'CREATE TABLE signup (\n'
    '    id         integer PRIMARY KEY,\n'
    '    workout_id integer NOT NULL REFERENCES workout (id),\n'
    "    state      text    NOT NULL CHECK (state IN ('new', 'done')),\n"
    '    handler    text\n'
    ');\n'
    'INSERT INTO signup (id, workout_id, state, handler) VALUES\n'
    "    (1, 1, 'new', NULL),\n"
    "    (2, 2, 'new', NULL),\n"
    "    (3, 3, 'new', NULL),\n"
    "    (4, 1, 'done', 'Гнатюк');\n"}

CFG = {1: {'name': 'бібліотека',
     'item': 'book',
     'tcol': 'title',
     'qcol': 'copies',
     'item1': 'Лісова пісня',
     'q1': 10,
     'q2': 6,
     'lt': 'loan',
     'lfk': 'book_id',
     'lwho': 'reader',
     'lamt': 'copies',
     'lcount0': 2,
     'lrows0': 3,
     'lnext': 4,
     'who': 'Богдан',
     'staff': 'librarian',
     'sname': 'full_name',
     'sflag': 'on_shift',
     'queue': 'hold',
     'qfk': 'book_id',
     'dA': 3,
     'dB': 4,
     'nA': 1,
     'nB': 1},
 2: {'name': 'магазин',
     'item': 'product',
     'tcol': 'title',
     'qcol': 'stock',
     'item1': 'Бездротова миша',
     'q1': 25,
     'q2': 14,
     'lt': 'purchase',
     'lfk': 'product_id',
     'lwho': 'customer',
     'lamt': 'quantity',
     'lcount0': 3,
     'lrows0': 4,
     'lnext': 5,
     'who': 'Олена',
     'staff': 'courier',
     'sname': 'full_name',
     'sflag': 'on_route',
     'queue': 'order_job',
     'qfk': 'product_id',
     'dA': 5,
     'dB': 8,
     'nA': 1,
     'nB': 1},
 3: {'name': 'фітнес-клуб',
     'item': 'workout',
     'tcol': 'title',
     'qcol': 'seats',
     'item1': 'Йога',
     'q1': 12,
     'q2': 9,
     'lt': 'booking',
     'lfk': 'workout_id',
     'lwho': 'member',
     'lamt': 'places',
     'lcount0': 4,
     'lrows0': 5,
     'lnext': 6,
     'who': 'Юрій',
     'staff': 'trainer',
     'sname': 'full_name',
     'sflag': 'on_floor',
     'queue': 'signup',
     'qfk': 'workout_id',
     'dA': 2,
     'dB': 3,
     'nA': 1,
     'nB': 1}}
