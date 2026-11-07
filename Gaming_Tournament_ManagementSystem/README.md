# Gaming Tournament Management System

JIIT Database Management Systems Lab (24B15CS213) project matching the synopsis: a relational database plus a Flask UI for organizing players, teams, tournaments, registrations, venues, matches, results, rankings, and prizes.

## Run

```bash
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Sample data loads automatically. Use **Reset sample data** in the sidebar to restore the seed.

## Synopsis mapping

| Synopsis item | Where it lives |
| --- | --- |
| Player / team / tournament / match / venue / registration / result / prize | Tables in `database/schema.sql`, CRUD screens in the app |
| ER flow Player → Team → Registration → Tournament → Match → Result | `/schema` page |
| PK, FK, NOT NULL, UNIQUE, CHECK | `database/schema.sql` |
| Normalization to 3NF | `/schema` and split of Prize vs PrizeDistribution |
| Inner, left/outer, self join | `/sql-lab` and `database/queries.sql` |
| Aggregate, GROUP BY, HAVING | Rankings view and SQL lab |
| Subqueries, nested queries, views | `v_team_rankings`, `v_match_results`, `v_prize_distribution` |
| INSERT / SELECT / UPDATE / DELETE | Every entity form |
| UNION / INTERSECT / EXCEPT, ORDER BY, WHERE, LIKE, BETWEEN | `database/queries.sql` and SQL lab |

SQLite is used so the project runs without a separate DBMS server. The SQL is standard enough to port to MySQL/Oracle for the lab viva if required.
