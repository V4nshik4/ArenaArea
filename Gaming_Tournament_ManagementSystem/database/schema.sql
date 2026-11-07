-- Gaming Tournament Management System
-- Relational schema: 3NF, PKs, FKs, CHECK / UNIQUE / NOT NULL

PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS v_prize_distribution;
DROP VIEW IF EXISTS v_match_results;
DROP VIEW IF EXISTS v_tournament_participants;
DROP VIEW IF EXISTS v_team_rankings;

DROP TABLE IF EXISTS PrizeDistribution;
DROP TABLE IF EXISTS Prize;
DROP TABLE IF EXISTS Result;
DROP TABLE IF EXISTS MatchEvent;
DROP TABLE IF EXISTS Registration;
DROP TABLE IF EXISTS TournamentVenue;
DROP TABLE IF EXISTS Player;
DROP TABLE IF EXISTS Tournament;
DROP TABLE IF EXISTS Venue;
DROP TABLE IF EXISTS Team;

CREATE TABLE Team (
    team_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name    TEXT    NOT NULL UNIQUE,
    coach_name   TEXT    NOT NULL,
    founded_year INTEGER NOT NULL CHECK (founded_year BETWEEN 2000 AND 2100),
    status       TEXT    NOT NULL DEFAULT 'Active'
                         CHECK (status IN ('Active', 'Inactive'))
);

CREATE TABLE Player (
    player_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    ingame_id   TEXT    NOT NULL UNIQUE,
    role        TEXT    NOT NULL CHECK (role IN ('Captain', 'Member', 'Substitute')),
    age         INTEGER NOT NULL CHECK (age BETWEEN 13 AND 60),
    team_id     INTEGER NOT NULL,
    mentor_id   INTEGER,
    join_date   TEXT    NOT NULL,
    FOREIGN KEY (team_id)   REFERENCES Team(team_id)   ON DELETE RESTRICT,
    FOREIGN KEY (mentor_id) REFERENCES Player(player_id) ON DELETE SET NULL
);

CREATE TABLE Tournament (
    tournament_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_name TEXT    NOT NULL,
    game_title      TEXT    NOT NULL,
    start_date      TEXT    NOT NULL,
    end_date        TEXT    NOT NULL,
    status          TEXT    NOT NULL CHECK (status IN ('Upcoming', 'Ongoing', 'Completed')),
    organizer_name  TEXT    NOT NULL,
    max_teams       INTEGER NOT NULL CHECK (max_teams >= 2),
    CHECK (end_date >= start_date)
);

CREATE TABLE Venue (
    venue_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name TEXT    NOT NULL,
    venue_type TEXT    NOT NULL CHECK (venue_type IN ('Offline', 'Online')),
    location   TEXT    NOT NULL,
    capacity   INTEGER CHECK (capacity IS NULL OR capacity > 0)
);

CREATE TABLE TournamentVenue (
    tournament_id INTEGER NOT NULL,
    venue_id      INTEGER NOT NULL,
    PRIMARY KEY (tournament_id, venue_id),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE,
    FOREIGN KEY (venue_id)      REFERENCES Venue(venue_id)          ON DELETE RESTRICT
);

CREATE TABLE Registration (
    registration_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id     INTEGER NOT NULL,
    team_id           INTEGER NOT NULL,
    registration_date TEXT    NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'Pending'
                              CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    UNIQUE (tournament_id, team_id),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id)       REFERENCES Team(team_id)           ON DELETE RESTRICT
);

CREATE TABLE MatchEvent (
    match_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    team1_id      INTEGER NOT NULL,
    team2_id      INTEGER NOT NULL,
    venue_id      INTEGER NOT NULL,
    match_date    TEXT    NOT NULL,
    round_name    TEXT    NOT NULL
                          CHECK (round_name IN ('Group', 'Quarterfinal', 'Semifinal', 'Final', 'Third Place')),
    status        TEXT    NOT NULL DEFAULT 'Scheduled'
                          CHECK (status IN ('Scheduled', 'Live', 'Completed', 'Cancelled')),
    CHECK (team1_id <> team2_id),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE,
    FOREIGN KEY (team1_id)      REFERENCES Team(team_id),
    FOREIGN KEY (team2_id)      REFERENCES Team(team_id),
    FOREIGN KEY (venue_id)      REFERENCES Venue(venue_id)
);

CREATE TABLE Result (
    result_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id       INTEGER NOT NULL UNIQUE,
    winner_team_id INTEGER,
    team1_score    INTEGER NOT NULL CHECK (team1_score >= 0),
    team2_score    INTEGER NOT NULL CHECK (team2_score >= 0),
    remarks        TEXT,
    FOREIGN KEY (match_id)       REFERENCES MatchEvent(match_id) ON DELETE CASCADE,
    FOREIGN KEY (winner_team_id) REFERENCES Team(team_id)
);

CREATE TABLE Prize (
    prize_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id     INTEGER NOT NULL,
    position          INTEGER NOT NULL CHECK (position BETWEEN 1 AND 10),
    prize_amount      REAL    NOT NULL CHECK (prize_amount >= 0),
    prize_description TEXT    NOT NULL,
    UNIQUE (tournament_id, position),
    FOREIGN KEY (tournament_id) REFERENCES Tournament(tournament_id) ON DELETE CASCADE
);

CREATE TABLE PrizeDistribution (
    distribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prize_id        INTEGER NOT NULL UNIQUE,
    team_id         INTEGER NOT NULL,
    awarded_date    TEXT    NOT NULL,
    FOREIGN KEY (prize_id) REFERENCES Prize(prize_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id)  REFERENCES Team(team_id)
);

CREATE INDEX idx_player_team ON Player(team_id);
CREATE INDEX idx_reg_tournament ON Registration(tournament_id);
CREATE INDEX idx_match_tournament ON MatchEvent(tournament_id);
CREATE INDEX idx_prize_tournament ON Prize(tournament_id);

-- View: team rankings from completed match results (3 pts win, 1 pt draw)
CREATE VIEW v_team_rankings AS
SELECT
    t.tournament_id,
    t.tournament_name,
    tm.team_id,
    tm.team_name,
    COUNT(r.result_id) AS matches_played,
    COALESCE(SUM(CASE WHEN r.winner_team_id = tm.team_id THEN 1 ELSE 0 END), 0) AS wins,
    COALESCE(SUM(CASE
            WHEN r.result_id IS NOT NULL AND r.winner_team_id IS NULL THEN 1
            ELSE 0
        END), 0) AS draws,
    COALESCE(SUM(CASE
            WHEN r.winner_team_id IS NOT NULL AND r.winner_team_id <> tm.team_id THEN 1
            ELSE 0
        END), 0) AS losses,
    COALESCE(SUM(CASE
            WHEN r.winner_team_id = tm.team_id THEN 3
            WHEN r.result_id IS NOT NULL AND r.winner_team_id IS NULL THEN 1
            ELSE 0
        END), 0) AS points
FROM Team tm
JOIN Registration rg
    ON rg.team_id = tm.team_id AND rg.status = 'Approved'
JOIN Tournament t
    ON t.tournament_id = rg.tournament_id
LEFT JOIN MatchEvent m
    ON m.tournament_id = t.tournament_id
   AND (m.team1_id = tm.team_id OR m.team2_id = tm.team_id)
   AND m.status = 'Completed'
LEFT JOIN Result r
    ON r.match_id = m.match_id
GROUP BY t.tournament_id, t.tournament_name, tm.team_id, tm.team_name;

CREATE VIEW v_tournament_participants AS
SELECT
    t.tournament_id,
    t.tournament_name,
    t.game_title,
    tm.team_id,
    tm.team_name,
    r.registration_date,
    r.status AS registration_status,
    COUNT(p.player_id) AS squad_size
FROM Tournament t
INNER JOIN Registration r ON r.tournament_id = t.tournament_id
INNER JOIN Team tm ON tm.team_id = r.team_id
LEFT JOIN Player p ON p.team_id = tm.team_id
GROUP BY t.tournament_id, t.tournament_name, t.game_title,
         tm.team_id, tm.team_name, r.registration_date, r.status;

CREATE VIEW v_match_results AS
SELECT
    m.match_id,
    t.tournament_name,
    t.game_title,
    m.round_name,
    m.match_date,
    v.venue_name,
    a.team_name AS team1,
    b.team_name AS team2,
    r.team1_score,
    r.team2_score,
    w.team_name AS winner,
    m.status
FROM MatchEvent m
INNER JOIN Tournament t ON t.tournament_id = m.tournament_id
INNER JOIN Venue v ON v.venue_id = m.venue_id
INNER JOIN Team a ON a.team_id = m.team1_id
INNER JOIN Team b ON b.team_id = m.team2_id
LEFT JOIN Result r ON r.match_id = m.match_id
LEFT JOIN Team w ON w.team_id = r.winner_team_id;

CREATE VIEW v_prize_distribution AS
SELECT
    t.tournament_name,
    pr.position,
    pr.prize_amount,
    pr.prize_description,
    tm.team_name AS awarded_to,
    pd.awarded_date
FROM Prize pr
INNER JOIN Tournament t ON t.tournament_id = pr.tournament_id
LEFT JOIN PrizeDistribution pd ON pd.prize_id = pr.prize_id
LEFT JOIN Team tm ON tm.team_id = pd.team_id;
