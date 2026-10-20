# Метрики активности: рекорд или проблема?

Под каждым пунктом — строка «**Ответ:**» (числа и ответ на контрольный вопрос) и запрос в блоке ```sql. Запуск запросов: `python3 src/sqlmd.py reports/01_metrics.md`.

### 1. Период и пользователи

Контрольный вопрос: почему пользователей больше, чем зарегистрировалось за период, и кого из них ты будешь считать новичком?

**Ответ:** Выгрузка - с 2026-07-01 по 2026-09-28, 90 дней. В users 24907 человек, но за период зарегистрировались только 20907: ещё 4000- старые пользователи, которые зарегистрировались раньше (с 2026-01-01 по 2026-06-23). В activity 24906 человек: один старый пользователь (user_id 2667) за период ни разу не заходил. Новичок - тот, кто зарегистрировался с 1 июля 2026 (это 20907 строк таблицы newcomers): только у него в выгрузке видна вся история с дня регистрации.

```sql
SELECT MIN(date) AS first_day, MAX(date) AS last_day, COUNT(DISTINCT date) AS days FROM activity;
SELECT COUNT(*) AS users_total FROM users;
SELECT COUNT(DISTINCT user_id) AS users_active FROM activity;
SELECT signup_date >= '2026-07-01' AS registered_in_period, COUNT(*) AS users, MIN(signup_date) AS first_signup, MAX(signup_date) AS last_signup FROM users
GROUP BY signup_date >= '2026-07-01';
SELECT user_id, signup_date FROM users WHERE user_id NOT IN (SELECT user_id FROM activity);
```

### 2. DAU по дням

Контрольный вопрос: что повторяется каждую неделю? Какие из выписанных дней — это повторение, а какие — событие, и как ты их отличил?

**Ответ:** Топ-3 DAU: 2026-08-08 - 3901, 2026-08-09 - 3804, 2026-08-07 -3429. Минимум: 2026-08-19 - 935. Каждую неделю повторяется "выходной горб": суббота и воскресенье выше будней (в июле до всплеска: вс 1819, сб 1782, будни 1600-1695, т.е. примерно + 10%). Топ-3 дня - не повторение, а событие: 7-9 августа DAU вырос почти вдвое против предыдущих выходных (3901 против 2060 в сб 1 августа) и в эти же дни регистраций стало в 13 раз больше (1591 в пятницу 7 августа против 120 за день до этого). Минимум 19 августа (среда) - тоже событие, а не повторение: во вторник и четверг рядом DAU 2475 и 2542, в другие среды всё нормально. Отличил так: повторение - тот же день недели в соседние недели даёт похожее число; событие - число резко отличается от тех же дней соседних недель.

```sql
SELECT date, COUNT(DISTINCT user_id) AS dau FROM act GROUP BY date ORDER BY date;
SELECT date, COUNT(DISTINCT user_id) AS dau FROM act GROUP BY date ORDER BY dau DESC LIMIT 3;
SELECT date, COUNT(DISTINCT user_id) AS dau FROM act GROUP BY date ORDER BY dau ASC LIMIT 1;
SELECT strftime('%w', date) AS dow, ROUND(AVG(dau)) AS avg_dau
FROM (SELECT date, COUNT(DISTINCT user_id) AS dau FROM act WHERE date <= '2026-08-06' GROUP BY date)
GROUP BY dow
ORDER BY dow;
SELECT signup_date, COUNT(*) AS registered FROM users WHERE signup_date BETWEEN '2026-08-05' AND '2026-08-10' GROUP BY signup_date;
```

### 3. WAU по неделям

Контрольный вопрос: все ли недели в выгрузке полные? Каким запросом ты это проверил и что будет, если сравнить неполную неделю с полной?

**Ответ:** Нет, не все. Запрос считает для каждой недели число разных дней в данных (days_in_week). Первая неделя(с понедельника 2026-06-29) содержит только 5 дней (1-5 июля, выгрузка началась в среду), последняя (с понедельника 2026-09-28) - 1 день (28 сентября). Остальные 11 недель по 7 дней. Если сравнить неполную неделю с полной, получится ложный тренд: WAU первой недели 3445 против 4341 у следующей выглядит как "рост на 26%", а WAU последней недели 2661 против 6549 у предыдущей - как "обвал на 59%". На деле просто мало дней: WAU последней недели равен DAU одного дня.

```sql
SELECT week, COUNT(DISTINCT date) AS days_in_week, COUNT(DISTINCT user_id) AS wau FROM ACT
GROUP BY week
ORDER BY week;
```

### 4. MAU по месяцам

Контрольный вопрос: все ли месяцы полные? Почему MAU месяца не равен сумме DAU за этот месяц?

**Ответ:** MAU: июль 7917, август 17805, сентябрь 10618. Июль и август полные (31 из 31), сентябрь - 28 дней из 30. MAU не равен сумме DAU: MAU считает человека один раз за месяц, а сумма DAU - каждый день его захода (июль: 7917 против 50148).

```sql
SELECT month, COUNT(DISTINCT date) AS days_in_month, COUNT(DISTINCT user_id) AS mau, COUNT(*) AS sum_of_dau
FROM act
GROUP BY month
ORDER BY month;
```

### 5. Средний DAU и липкость

Контрольный вопрос: как менялась липкость, пока рос MAU, и что это говорит о тех, кто пришёл?

**Ответ:** Липкость = средний DAU/MAU: июль 20,4%, август 14,9%, сентябрь 25,4%. Пока MAU рос (июль- август в 2,25 раза), липкость упала: средний DAU вырос только в 1,6 раза - пришедшие в августе заходили редко.

```sql
SELECT month,
    COUNT (DISTINCT user_id) AS mau,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT date), 1) AS avg_dau,
    ROUND(COUNT(*) * 100.0 / COUNT(DISTINCT date) / COUNT(DISTINCT user_id), 1) AS stickiness_pct
FROM act
GROUP BY month
ORDER BY month;
```

### 6. Новички месяца в MAU

Контрольный вопрос: чья липкость изменилась, а чья осталась прежней?

**Ответ:** Липкость новичков месяца: июль 14,7%, август 8,9%, сентябрь 14,7%; остальных: 26,3%, 29,6%, 32,5%. Изменилась у новчиков августа. Старые пользователи (до июля) стабильны: 26,3% - 25,9% - 26,5%. Новички - 12675 из 17805 человек MAU августа (71%).

```sql
SELECT month,
    CASE WHEN signup_month = month THEN 'новички месяца' ELSE 'остальные' END AS grp,
    COUNT(DISTINCT user_id) AS mau,
    ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT date), 1) AS avg_dau,
    ROUND(COUNT(*) * 100.0 / COUNT(DISTINCT date) / COUNT(DISTINCT user_id), 1) AS stickiness_pct
FROM act
GROUP BY month, grp
ORDER BY month, grp;
SELECT month,
    CASE WHEN signup_month = month THEN '1 новички месяца'
        WHEN signup_month < '2026-07' THEN '2 старые (до июля)'
        ELSE '3 новички прошлых месяцев' END AS grp,
    COUNT(DISTINCT user_id) AS mau,
    ROUND(COUNT(*) * 100.0 / COUNT(DISTINCT date) / COUNT(DISTINCT user_id), 1) AS stickiness_pct
FROM act
GROUP BY month, grp
ORDER BY month, grp;
```

### 7. Кто остался

Контрольный вопрос: если бы новички августа удерживались так же, как новички июля, сколько из них заходило бы в сентябре? Сколько людей мы недосчитались?

**Ответ:** Новичков июля 4003, в августе заходили 1219 (30,5%). Новчиков августа 12675, в сентябре заходили 1864 (14,7%). При июльском удержании в сентябре зашло бы около 3860 человек, значит недосчитались около 1996, то есть примерно 2000.

```sql
SELECT COUNT(*) AS july_newcomers FROM newcomers WHERE signup_month = '2026-07';
SELECT COUNT(DISTINCT user_id) AS july_newcomers_in_august FROM act WHERE signup_month = '2026-07' AND month = '2026-08';
SELECT COUNT(*) AS august_newcomers FROM newcomers WHERE signup_month = '2026-08';
SELECT COUNT(DISTINCT user_id) AS august_newcomers_in_september FROM act WHERE signup_month = '2026-08' AND month = '2026-09';
SELECT ROUND(1219 * 100.0 / 4003, 1) AS july_share_pct,
    ROUND (1864 * 100.0 / 12675, 1) AS august_share_pct,
    ROUND (12675 * 1219.0 / 4003) AS expected_in_september,
    ROUND (12675 * 1219.0 / 4003) - 1864 AS missing_people;
```

## Вывод

Есть ли проблема? Одно число, которое это показывает. Почему рекордный MAU её не опровергает.
