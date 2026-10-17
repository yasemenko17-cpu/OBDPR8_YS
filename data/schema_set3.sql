-- Набір 3: фітнес-клуб
CREATE TABLE workout (
    id    integer PRIMARY KEY,
    title text    NOT NULL,
    seats integer NOT NULL CHECK (seats >= 0)
);
INSERT INTO workout (id, title, seats) VALUES
    (1, 'Йога', 12),
    (2, 'Пілатес', 9),
    (3, 'Кросфіт', 6);

CREATE TABLE booking (
    id         integer PRIMARY KEY,
    workout_id integer NOT NULL REFERENCES workout (id),
    member     text    NOT NULL,
    places     integer NOT NULL
);
INSERT INTO booking (id, workout_id, member, places) VALUES
    (1, 1, 'Марта', 1),
    (2, 1, 'Денис', 2),
    (3, 1, 'Софія', 1),
    (4, 1, 'Роман', 1),
    (5, 2, 'Марта', 1);

CREATE TABLE trainer (
    id        integer PRIMARY KEY,
    full_name text    NOT NULL,
    on_floor  boolean NOT NULL
);
INSERT INTO trainer (id, full_name, on_floor) VALUES
    (1, 'Гнатюк', true),
    (2, 'Лисенко', true),
    (3, 'Павленко', false);

CREATE TABLE signup (
    id         integer PRIMARY KEY,
    workout_id integer NOT NULL REFERENCES workout (id),
    state      text    NOT NULL CHECK (state IN ('new', 'done')),
    handler    text
);
INSERT INTO signup (id, workout_id, state, handler) VALUES
    (1, 1, 'new', NULL),
    (2, 2, 'new', NULL),
    (3, 3, 'new', NULL),
    (4, 1, 'done', 'Гнатюк');
