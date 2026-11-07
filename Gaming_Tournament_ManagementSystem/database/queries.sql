-- Academic SQL file mapped to synopsis implementation list
-- Run after schema.sql and seed.sql

-- 14. CRUD: SELECT / INSERT / UPDATE / DELETE (examples)
SELECT * FROM Player WHERE team_id = 1;
-- INSERT INTO Player (...) VALUES (...);
-- UPDATE Player SET role = 'Member' WHERE player_id = 2;
-- DELETE FROM Registration WHERE status = 'Rejected';

-- 16. Ordering & filtering
SELECT player_name, ingame_id, age
FROM Player
WHERE age BETWEEN 18 AND 22
  AND player_name LIKE 'A%'
ORDER BY age DESC, player_name;

-- 7. Inner join: players belonging to a particular team
SELECT p.player_name, p.role, t.team_name, t.coach_name
FROM Player p
INNER JOIN Team t ON t.team_id = p.team_id
WHERE t.team_name = 'Phoenix Esports';

-- 7. Left outer join: all matches, including those without results
SELECT m.match_id, m.round_name, a.team_name AS team1, b.team_name AS team2,
       r.team1_score, r.team2_score
FROM MatchEvent m
INNER JOIN Team a ON a.team_id = m.team1_id
INNER JOIN Team b ON b.team_id = m.team2_id
LEFT JOIN Result r ON r.match_id = m.match_id;

-- 7. Right-style outer join (SQLite has no RIGHT JOIN; written as LEFT with swapped sides)
SELECT v.venue_name, m.match_id, m.round_name
FROM MatchEvent m
LEFT JOIN Venue v ON v.venue_id = m.venue_id;

SELECT v.venue_name, m.match_id, m.round_name
FROM Venue v
LEFT JOIN MatchEvent m ON m.venue_id = v.venue_id;

-- 7. Self join: players and their mentors
SELECT mentee.player_name AS player,
       mentor.player_name AS mentor,
       t.team_name
FROM Player mentee
INNER JOIN Player mentor ON mentee.mentor_id = mentor.player_id
INNER JOIN Team t ON t.team_id = mentee.team_id;

-- 8–10. Aggregate + GROUP BY + HAVING
SELECT t.team_name, COUNT(p.player_id) AS player_count, AVG(p.age) AS avg_age
FROM Team t
INNER JOIN Player p ON p.team_id = t.team_id
GROUP BY t.team_name
HAVING COUNT(p.player_id) >= 3
ORDER BY player_count DESC;

-- Tournament-wise prize distribution (aggregate)
SELECT tn.tournament_name, SUM(pr.prize_amount) AS total_prize_pool
FROM Tournament tn
INNER JOIN Prize pr ON pr.tournament_id = tn.tournament_id
GROUP BY tn.tournament_name;

-- 11–12. Subquery / nested query: teams that won at least one match
SELECT team_name
FROM Team
WHERE team_id IN (
    SELECT DISTINCT winner_team_id
    FROM Result
    WHERE winner_team_id IS NOT NULL
);

-- Nested: players of the team with the highest points in a completed tournament
SELECT player_name, ingame_id
FROM Player
WHERE team_id = (
    SELECT team_id
    FROM v_team_rankings
    WHERE tournament_id = 1
    ORDER BY points DESC, wins DESC
    LIMIT 1
);

-- 13. Views
SELECT * FROM v_team_rankings WHERE tournament_id = 1 ORDER BY points DESC;
SELECT * FROM v_tournament_participants;
SELECT * FROM v_match_results;
SELECT * FROM v_prize_distribution;

-- 15. Set operations
SELECT player_name FROM Player WHERE team_id = 1
UNION
SELECT player_name FROM Player WHERE team_id = 2;

SELECT team_id FROM Registration WHERE tournament_id = 1 AND status = 'Approved'
INTERSECT
SELECT team_id FROM Registration WHERE tournament_id = 2 AND status = 'Approved';

SELECT team_id FROM Registration WHERE tournament_id = 1 AND status = 'Approved'
EXCEPT
SELECT team_id FROM Registration WHERE tournament_id = 3 AND status = 'Approved';
