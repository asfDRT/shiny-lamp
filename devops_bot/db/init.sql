-- Создаем необходимые таблицы
CREATE TABLE email_table (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE phone_table (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL
);


-- Для теста добавим данные
INSERT INTO email_table (id, email) VALUES 
    (DEFAULT, 'asdfasdf@mail.ru'), 
    (DEFAULT, 'adsghadfgfff@gmail.com');

INSERT INTO phone_table (id, phone_number) VALUES 
    (DEFAULT, '81234567890'), 
    (DEFAULT, '+71233341299');


-- Создаем пользователя из env
CREATE USER $DB_REPL_USER WITH REPLICATION ENCRYPTED PASSWORD '$DB_REPL_PASSWORD';


SELECT pg_create_physical_replication_slot('replication_slot');
