-- ==========================================
-- ServiceMonitor: SQL-запросы проекта
-- ==========================================
-- Каждый запрос снабжён комментарием с назначением.
-- Знаком ? обозначены параметры: значения передаются
-- из Python отдельно, а не подставляются в текст запроса.
-- Запросы сгруппированы по видам:
--   выборка списков, фильтрация WHERE, соединение JOIN,
--   агрегатные функции, группировка GROUP BY, HAVING.


-- ------------------------------------------
-- Выборка списков
-- ------------------------------------------

-- Запрос 1. Список всех сервисов (для страницы «Сервисы»)
SELECT
    id,
    name,
    url,
    description
FROM services
ORDER BY name;

-- Запрос 2. Список сервисов с названием группы (список + JOIN)
SELECT
    services.id,
    services.name,
    services.url,
    groups.name AS group_name
FROM services
LEFT JOIN groups ON groups.id = services.group_id
ORDER BY services.name;

-- Запрос 3. Список групп с числом сервисов в каждой (список + GROUP BY)
SELECT
    groups.id,
    groups.name,
    COUNT(services.id) AS services_count
FROM groups
LEFT JOIN services ON services.group_id = groups.id
GROUP BY groups.id, groups.name
ORDER BY groups.name;


-- ------------------------------------------
-- Фильтрация (WHERE)
-- ------------------------------------------

-- Запрос 4. Поиск сервисов по части названия
SELECT
    id,
    name,
    url
FROM services
WHERE name LIKE ?
ORDER BY name;

-- Запрос 5. Сервисы выбранной группы
SELECT
    services.name,
    services.url
FROM services
JOIN groups ON groups.id = services.group_id
WHERE groups.name = ?
ORDER BY services.name;

-- Запрос 6. Недоступные проверки (available = 0)
SELECT
    id,
    service_id,
    code,
    checked_at
FROM checks
WHERE available = 0
ORDER BY checked_at DESC;


-- ------------------------------------------
-- Соединение таблиц (JOIN)
-- ------------------------------------------

-- Запрос 7. Полная информация о проверке (JOIN трёх таблиц)
SELECT
    checks.id,
    services.name AS service_name,
    groups.name AS group_name,
    checks.available,
    checks.code,
    checks.checked_at
FROM checks
JOIN services ON services.id = checks.service_id
LEFT JOIN groups ON groups.id = services.group_id
ORDER BY checks.checked_at DESC;

-- Запрос 8. Сервисы, которые ещё ни разу не проверялись
SELECT
    services.name,
    services.url
FROM services
LEFT JOIN checks ON checks.service_id = services.id
WHERE checks.id IS NULL
ORDER BY services.name;


-- ------------------------------------------
-- Агрегатные функции
-- ------------------------------------------

-- Запрос 9. Общее количество проверок
SELECT
    COUNT(*) AS checks_total
FROM checks;

-- Запрос 10. Количество доступных и недоступных проверок
SELECT
    SUM(available) AS available_count,
    SUM(1 - available) AS unavailable_count
FROM checks;

-- Запрос 11. Последняя проверка каждого сервиса (агрегат + JOIN)
SELECT
    services.name,
    MAX(checks.checked_at) AS last_checked_at
FROM services
JOIN checks ON checks.service_id = services.id
GROUP BY services.id, services.name
ORDER BY services.name;


-- ------------------------------------------
-- Группировка (GROUP BY) и HAVING
-- ------------------------------------------

-- Запрос 12. Количество проверок по каждому сервису (GROUP BY + LEFT JOIN)
SELECT
    services.name AS service_name,
    COUNT(checks.id) AS checks_count
FROM services
LEFT JOIN checks ON checks.service_id = services.id
GROUP BY services.id, services.name
ORDER BY checks_count DESC, services.name;

-- Запрос 13. Количество сервисов в каждой группе (GROUP BY)
SELECT
    groups.name AS group_name,
    COUNT(services.id) AS services_count
FROM groups
LEFT JOIN services ON services.group_id = groups.id
GROUP BY groups.id, groups.name
ORDER BY services_count DESC, groups.name;

-- Запрос 14. Сервисы с числом проверок больше заданного (HAVING)
SELECT
    services.name AS service_name,
    COUNT(checks.id) AS checks_count
FROM services
JOIN checks ON checks.service_id = services.id
GROUP BY services.id, services.name
HAVING COUNT(checks.id) > ?
ORDER BY checks_count DESC;

-- Запрос 15. Группы более чем с одним сервисом (HAVING)
SELECT
    groups.name AS group_name,
    COUNT(services.id) AS services_count
FROM groups
JOIN services ON services.group_id = groups.id
GROUP BY groups.id, groups.name
HAVING COUNT(services.id) > 1
ORDER BY services_count DESC, groups.name;
