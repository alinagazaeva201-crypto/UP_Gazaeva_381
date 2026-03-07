CREATE TABLE IF NOT EXISTS request_statuses (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS device_types (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS clients (
    client_id SERIAL PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS technicians (
    technician_id SERIAL PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    specialization VARCHAR(200),
    phone VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS repair_requests (
    request_id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(client_id) ON DELETE CASCADE,
    technician_id INTEGER REFERENCES technicians(technician_id) ON DELETE SET NULL,
    device_type_id INTEGER REFERENCES device_types(type_id) ON DELETE RESTRICT,
    device_model VARCHAR(200) NOT NULL,
    problem_description TEXT,
    status_id INTEGER REFERENCES request_statuses(status_id) ON DELETE RESTRICT DEFAULT 1,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_date DATE
);

INSERT INTO request_statuses (status_name) VALUES
    ('Новая'),
    ('В работе'),
    ('Выполнена'),
    ('Отложена'),
    ('Требуются запчасти')
ON CONFLICT (status_name) DO NOTHING;

INSERT INTO device_types (type_name) VALUES
    ('Стиральная машина'),
    ('Холодильник'),
    ('Телевизор'),
    ('Ноутбук'),
    ('Плита'),
    ('Микроволновка'),
    ('Пылесос'),
    ('Посудомоечная машина')
ON CONFLICT (type_name) DO NOTHING;

INSERT INTO technicians (last_name, first_name, middle_name, specialization, phone) VALUES
    ('Сергеев', 'Андрей', 'Николаевич', 'Крупная бытовая техника', '+7(901)111-11-11'),
    ('Кузнецова', 'Елена', 'Владимировна', 'Мелкая бытовая техника', '+7(902)222-22-22'),
    ('Петров', 'Дмитрий', 'Сергеевич', 'Цифровая техника', '+7(903)333-33-33')
ON CONFLICT (phone) DO NOTHING;

INSERT INTO clients (last_name, first_name, middle_name, phone, email) VALUES
    ('Иванов', 'Иван', 'Иванович', '+7(904)444-44-44', 'ivanov@mail.ru'),
    ('Петрова', 'Мария', 'Сергеевна', '+7(905)555-55-55', 'petrova@yandex.ru'),
    ('Сидоров', 'Петр', 'Алексеевич', '+7(906)666-66-66', NULL)
ON CONFLICT (phone) DO NOTHING;
 
INSERT INTO repair_requests (client_id, technician_id, device_type_id, device_model, problem_description, status_id, creation_date) VALUES
    (1, 1, 1, 'Samsung WW90T', 'Не сливает воду, ошибка на дисплее', 2, '2024-02-15 10:30:00'),
    (2, NULL, 2, 'LG DoorCooling+', 'Не морозит, компрессор работает постоянно', 1, '2024-02-20 14:15:00'),
    (3, 2, 4, 'HP Pavilion 15', 'Не включается, индикатор питания не горит', 3, '2024-02-10 09:00:00')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role_id INTEGER REFERENCES roles(role_id) ON DELETE RESTRICT,
    technician_id INTEGER UNIQUE REFERENCES technicians(technician_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

INSERT INTO roles (role_name) VALUES
    ('Администратор'),
    ('Менеджер'),
    ('Мастер')
ON CONFLICT (role_name) DO NOTHING;

INSERT INTO users (username, password_hash, role_id) VALUES
    ('admin', 'sha256$admin123', 1),
    ('manager', 'sha256$manager123', 2),
    ('master1', 'sha256$master123', 3)
ON CONFLICT (username) DO NOTHING;

CREATE TABLE IF NOT EXISTS request_history (
    history_id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES repair_requests(request_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    old_status_id INTEGER REFERENCES request_statuses(status_id),
    new_status_id INTEGER REFERENCES request_statuses(status_id),
    comment TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_requests_client ON repair_requests(client_id);
CREATE INDEX IF NOT EXISTS idx_requests_technician ON repair_requests(technician_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON repair_requests(status_id);
CREATE INDEX IF NOT EXISTS idx_requests_date ON repair_requests(creation_date);
CREATE INDEX IF NOT EXISTS idx_history_request ON request_history(request_id);