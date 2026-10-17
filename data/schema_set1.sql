-- Набір 1: бібліотека
CREATE TABLE book (
    id     integer PRIMARY KEY,
    title  text    NOT NULL,
    copies integer NOT NULL CHECK (copies >= 0)
);
INSERT INTO book (id, title, copies) VALUES
    (1, 'Лісова пісня', 10),
    (2, 'Intermezzo', 6),
    (3, 'Тіні забутих предків', 4);

CREATE TABLE loan (
    id      integer PRIMARY KEY,
    book_id integer NOT NULL REFERENCES book (id),
    reader  text    NOT NULL,
    copies  integer NOT NULL
);
INSERT INTO loan (id, book_id, reader, copies) VALUES
    (1, 1, 'Оксана', 1),
    (2, 1, 'Тарас', 2),
    (3, 2, 'Оксана', 1);

CREATE TABLE librarian (
    id        integer PRIMARY KEY,
    full_name text    NOT NULL,
    on_shift  boolean NOT NULL
);
INSERT INTO librarian (id, full_name, on_shift) VALUES
    (1, 'Іваненко', true),
    (2, 'Мельник', true),
    (3, 'Коваль', false);

CREATE TABLE hold (
    id      integer PRIMARY KEY,
    book_id integer NOT NULL REFERENCES book (id),
    state   text    NOT NULL CHECK (state IN ('new', 'done')),
    handler text
);
INSERT INTO hold (id, book_id, state, handler) VALUES
    (1, 1, 'new', NULL),
    (2, 2, 'new', NULL),
    (3, 3, 'new', NULL),
    (4, 1, 'done', 'Іваненко');
