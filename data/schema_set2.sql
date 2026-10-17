-- Набір 2: магазин
CREATE TABLE product (
    id    integer PRIMARY KEY,
    title text    NOT NULL,
    stock integer NOT NULL CHECK (stock >= 0)
);
INSERT INTO product (id, title, stock) VALUES
    (1, 'Бездротова миша', 25),
    (2, 'Клавіатура', 14),
    (3, 'Монітор', 8);

CREATE TABLE purchase (
    id         integer PRIMARY KEY,
    product_id integer NOT NULL REFERENCES product (id),
    customer   text    NOT NULL,
    quantity   integer NOT NULL
);
INSERT INTO purchase (id, product_id, customer, quantity) VALUES
    (1, 1, 'Андрій', 2),
    (2, 1, 'Ірина', 1),
    (3, 1, 'Максим', 3),
    (4, 2, 'Ірина', 1);

CREATE TABLE courier (
    id        integer PRIMARY KEY,
    full_name text    NOT NULL,
    on_route  boolean NOT NULL
);
INSERT INTO courier (id, full_name, on_route) VALUES
    (1, 'Бондар', true),
    (2, 'Шевчук', true),
    (3, 'Кравець', false);

CREATE TABLE order_job (
    id         integer PRIMARY KEY,
    product_id integer NOT NULL REFERENCES product (id),
    state      text    NOT NULL CHECK (state IN ('new', 'done')),
    handler    text
);
INSERT INTO order_job (id, product_id, state, handler) VALUES
    (1, 1, 'new', NULL),
    (2, 2, 'new', NULL),
    (3, 3, 'new', NULL),
    (4, 1, 'done', 'Бондар');
