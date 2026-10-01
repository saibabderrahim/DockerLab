CREATE TABLE IF NOT EXISTS products (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    price_cents INTEGER NOT NULL
);

INSERT INTO products (name, price_cents) VALUES
    ('Widget A', 1999),
    ('Widget B', 4999),
    ('Widget C', 999)
ON CONFLICT DO NOTHING;