import sqlite3
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for, flash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "gtms.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
SEED_PATH = BASE_DIR / "database" / "seed.sql"

app = Flask(__name__)
app.secret_key = "gtms-jiit-dbms-lab"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


def teams():
    return query("SELECT * FROM Team ORDER BY team_name")


def tournaments():
    return query("SELECT * FROM Tournament ORDER BY start_date")


def venues():
    return query("SELECT * FROM Venue ORDER BY venue_name")


@app.route("/")
def dashboard():
    stats = {
        "players": query("SELECT COUNT(*) AS c FROM Player", one=True)["c"],
        "teams": query("SELECT COUNT(*) AS c FROM Team", one=True)["c"],
        "tournaments": query("SELECT COUNT(*) AS c FROM Tournament", one=True)["c"],
        "matches": query("SELECT COUNT(*) AS c FROM MatchEvent", one=True)["c"],
    }
    recent = query(
        """
        SELECT * FROM v_match_results
        ORDER BY match_date DESC
        LIMIT 6
        """
    )
    prize_pool = query(
        """
        SELECT tn.tournament_name, SUM(pr.prize_amount) AS total
        FROM Tournament tn
        JOIN Prize pr ON pr.tournament_id = tn.tournament_id
        GROUP BY tn.tournament_name
        ORDER BY total DESC
        """
    )
    return render_template("dashboard.html", stats=stats, recent=recent, prize_pool=prize_pool)


@app.route("/players")
def players_list():
    search = request.args.get("q", "").strip()
    if search:
        rows = query(
            """
            SELECT p.*, t.team_name, m.player_name AS mentor_name
            FROM Player p
            JOIN Team t ON t.team_id = p.team_id
            LEFT JOIN Player m ON m.player_id = p.mentor_id
            WHERE p.player_name LIKE ? OR p.ingame_id LIKE ? OR t.team_name LIKE ?
            ORDER BY p.player_name
            """,
            (f"%{search}%", f"%{search}%", f"%{search}%"),
        )
    else:
        rows = query(
            """
            SELECT p.*, t.team_name, m.player_name AS mentor_name
            FROM Player p
            JOIN Team t ON t.team_id = p.team_id
            LEFT JOIN Player m ON m.player_id = p.mentor_id
            ORDER BY t.team_name, p.role, p.player_name
            """
        )
    return render_template("players.html", rows=rows, search=search)


@app.route("/players/new", methods=["GET", "POST"])
def player_new():
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO Player (player_name, email, ingame_id, role, age, team_id, mentor_id, join_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.form["player_name"],
                    request.form["email"],
                    request.form["ingame_id"],
                    request.form["role"],
                    int(request.form["age"]),
                    int(request.form["team_id"]),
                    int(request.form["mentor_id"]) if request.form.get("mentor_id") else None,
                    request.form["join_date"],
                ),
            )
            flash("Player added.", "ok")
            return redirect(url_for("players_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template(
        "player_form.html",
        item=None,
        teams=teams(),
        mentors=query("SELECT player_id, player_name FROM Player ORDER BY player_name"),
    )


@app.route("/players/<int:player_id>/edit", methods=["GET", "POST"])
def player_edit(player_id):
    item = query("SELECT * FROM Player WHERE player_id = ?", (player_id,), one=True)
    if not item:
        flash("Player not found.", "err")
        return redirect(url_for("players_list"))
    if request.method == "POST":
        try:
            execute(
                """
                UPDATE Player
                SET player_name=?, email=?, ingame_id=?, role=?, age=?, team_id=?, mentor_id=?, join_date=?
                WHERE player_id=?
                """,
                (
                    request.form["player_name"],
                    request.form["email"],
                    request.form["ingame_id"],
                    request.form["role"],
                    int(request.form["age"]),
                    int(request.form["team_id"]),
                    int(request.form["mentor_id"]) if request.form.get("mentor_id") else None,
                    request.form["join_date"],
                    player_id,
                ),
            )
            flash("Player updated.", "ok")
            return redirect(url_for("players_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template(
        "player_form.html",
        item=item,
        teams=teams(),
        mentors=query(
            "SELECT player_id, player_name FROM Player WHERE player_id <> ? ORDER BY player_name",
            (player_id,),
        ),
    )


@app.route("/players/<int:player_id>/delete", methods=["POST"])
def player_delete(player_id):
    execute("UPDATE Player SET mentor_id = NULL WHERE mentor_id = ?", (player_id,))
    execute("DELETE FROM Player WHERE player_id = ?", (player_id,))
    flash("Player deleted.", "ok")
    return redirect(url_for("players_list"))


@app.route("/teams")
def teams_list():
    rows = query(
        """
        SELECT t.*, COUNT(p.player_id) AS player_count
        FROM Team t
        LEFT JOIN Player p ON p.team_id = t.team_id
        GROUP BY t.team_id
        ORDER BY t.team_name
        """
    )
    return render_template("teams.html", rows=rows)


@app.route("/teams/new", methods=["GET", "POST"])
def team_new():
    if request.method == "POST":
        try:
            execute(
                "INSERT INTO Team (team_name, coach_name, founded_year, status) VALUES (?, ?, ?, ?)",
                (
                    request.form["team_name"],
                    request.form["coach_name"],
                    int(request.form["founded_year"]),
                    request.form["status"],
                ),
            )
            flash("Team created.", "ok")
            return redirect(url_for("teams_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("team_form.html", item=None)


@app.route("/teams/<int:team_id>/edit", methods=["GET", "POST"])
def team_edit(team_id):
    item = query("SELECT * FROM Team WHERE team_id = ?", (team_id,), one=True)
    if not item:
        return redirect(url_for("teams_list"))
    if request.method == "POST":
        try:
            execute(
                "UPDATE Team SET team_name=?, coach_name=?, founded_year=?, status=? WHERE team_id=?",
                (
                    request.form["team_name"],
                    request.form["coach_name"],
                    int(request.form["founded_year"]),
                    request.form["status"],
                    team_id,
                ),
            )
            flash("Team updated.", "ok")
            return redirect(url_for("teams_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("team_form.html", item=item)


@app.route("/teams/<int:team_id>/delete", methods=["POST"])
def team_delete(team_id):
    try:
        execute("DELETE FROM Team WHERE team_id = ?", (team_id,))
        flash("Team deleted.", "ok")
    except sqlite3.IntegrityError:
        flash("Cannot delete team that is referenced by players, matches, or registrations.", "err")
    return redirect(url_for("teams_list"))


@app.route("/tournaments")
def tournaments_list():
    rows = query("SELECT * FROM Tournament ORDER BY start_date DESC")
    return render_template("tournaments.html", rows=rows)


@app.route("/tournaments/new", methods=["GET", "POST"])
def tournament_new():
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO Tournament
                (tournament_name, game_title, start_date, end_date, status, organizer_name, max_teams)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.form["tournament_name"],
                    request.form["game_title"],
                    request.form["start_date"],
                    request.form["end_date"],
                    request.form["status"],
                    request.form["organizer_name"],
                    int(request.form["max_teams"]),
                ),
            )
            flash("Tournament created.", "ok")
            return redirect(url_for("tournaments_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("tournament_form.html", item=None)


@app.route("/tournaments/<int:tournament_id>/edit", methods=["GET", "POST"])
def tournament_edit(tournament_id):
    item = query("SELECT * FROM Tournament WHERE tournament_id = ?", (tournament_id,), one=True)
    if not item:
        return redirect(url_for("tournaments_list"))
    if request.method == "POST":
        try:
            execute(
                """
                UPDATE Tournament
                SET tournament_name=?, game_title=?, start_date=?, end_date=?,
                    status=?, organizer_name=?, max_teams=?
                WHERE tournament_id=?
                """,
                (
                    request.form["tournament_name"],
                    request.form["game_title"],
                    request.form["start_date"],
                    request.form["end_date"],
                    request.form["status"],
                    request.form["organizer_name"],
                    int(request.form["max_teams"]),
                    tournament_id,
                ),
            )
            flash("Tournament updated.", "ok")
            return redirect(url_for("tournaments_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("tournament_form.html", item=item)


@app.route("/tournaments/<int:tournament_id>/delete", methods=["POST"])
def tournament_delete(tournament_id):
    execute("DELETE FROM Tournament WHERE tournament_id = ?", (tournament_id,))
    flash("Tournament deleted.", "ok")
    return redirect(url_for("tournaments_list"))


@app.route("/venues")
def venues_list():
    rows = query(
        """
        SELECT v.*, COUNT(m.match_id) AS match_count
        FROM Venue v
        LEFT JOIN MatchEvent m ON m.venue_id = v.venue_id
        GROUP BY v.venue_id
        ORDER BY v.venue_name
        """
    )
    return render_template("venues.html", rows=rows)


@app.route("/venues/new", methods=["GET", "POST"])
def venue_new():
    if request.method == "POST":
        cap = request.form.get("capacity") or None
        execute(
            "INSERT INTO Venue (venue_name, venue_type, location, capacity) VALUES (?, ?, ?, ?)",
            (
                request.form["venue_name"],
                request.form["venue_type"],
                request.form["location"],
                int(cap) if cap else None,
            ),
        )
        flash("Venue added.", "ok")
        return redirect(url_for("venues_list"))
    return render_template("venue_form.html", item=None)


@app.route("/venues/<int:venue_id>/edit", methods=["GET", "POST"])
def venue_edit(venue_id):
    item = query("SELECT * FROM Venue WHERE venue_id = ?", (venue_id,), one=True)
    if request.method == "POST":
        cap = request.form.get("capacity") or None
        execute(
            "UPDATE Venue SET venue_name=?, venue_type=?, location=?, capacity=? WHERE venue_id=?",
            (
                request.form["venue_name"],
                request.form["venue_type"],
                request.form["location"],
                int(cap) if cap else None,
                venue_id,
            ),
        )
        flash("Venue updated.", "ok")
        return redirect(url_for("venues_list"))
    return render_template("venue_form.html", item=item)


@app.route("/venues/<int:venue_id>/delete", methods=["POST"])
def venue_delete(venue_id):
    try:
        execute("DELETE FROM Venue WHERE venue_id = ?", (venue_id,))
        flash("Venue deleted.", "ok")
    except sqlite3.IntegrityError:
        flash("Cannot delete a venue that is assigned to matches or tournaments.", "err")
    return redirect(url_for("venues_list"))


@app.route("/registrations")
def registrations_list():
    rows = query(
        """
        SELECT r.*, t.tournament_name, tm.team_name
        FROM Registration r
        JOIN Tournament t ON t.tournament_id = r.tournament_id
        JOIN Team tm ON tm.team_id = r.team_id
        ORDER BY r.registration_date DESC
        """
    )
    return render_template("registrations.html", rows=rows)


@app.route("/registrations/new", methods=["GET", "POST"])
def registration_new():
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO Registration (tournament_id, team_id, registration_date, status)
                VALUES (?, ?, ?, ?)
                """,
                (
                    int(request.form["tournament_id"]),
                    int(request.form["team_id"]),
                    request.form["registration_date"],
                    request.form["status"],
                ),
            )
            flash("Registration saved.", "ok")
            return redirect(url_for("registrations_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("registration_form.html", item=None, tournaments=tournaments(), teams=teams())


@app.route("/registrations/<int:registration_id>/edit", methods=["GET", "POST"])
def registration_edit(registration_id):
    item = query("SELECT * FROM Registration WHERE registration_id = ?", (registration_id,), one=True)
    if request.method == "POST":
        try:
            execute(
                """
                UPDATE Registration
                SET tournament_id=?, team_id=?, registration_date=?, status=?
                WHERE registration_id=?
                """,
                (
                    int(request.form["tournament_id"]),
                    int(request.form["team_id"]),
                    request.form["registration_date"],
                    request.form["status"],
                    registration_id,
                ),
            )
            flash("Registration updated.", "ok")
            return redirect(url_for("registrations_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("registration_form.html", item=item, tournaments=tournaments(), teams=teams())


@app.route("/registrations/<int:registration_id>/delete", methods=["POST"])
def registration_delete(registration_id):
    execute("DELETE FROM Registration WHERE registration_id = ?", (registration_id,))
    flash("Registration removed.", "ok")
    return redirect(url_for("registrations_list"))


@app.route("/matches")
def matches_list():
    rows = query("SELECT * FROM v_match_results ORDER BY match_date DESC")
    return render_template("matches.html", rows=rows)


@app.route("/matches/new", methods=["GET", "POST"])
def match_new():
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO MatchEvent
                (tournament_id, team1_id, team2_id, venue_id, match_date, round_name, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(request.form["tournament_id"]),
                    int(request.form["team1_id"]),
                    int(request.form["team2_id"]),
                    int(request.form["venue_id"]),
                    request.form["match_date"].replace("T", " "),
                    request.form["round_name"],
                    request.form["status"],
                ),
            )
            flash("Match scheduled.", "ok")
            return redirect(url_for("matches_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template(
        "match_form.html",
        item=None,
        tournaments=tournaments(),
        teams=teams(),
        venues=venues(),
    )


@app.route("/matches/<int:match_id>/edit", methods=["GET", "POST"])
def match_edit(match_id):
    item = query("SELECT * FROM MatchEvent WHERE match_id = ?", (match_id,), one=True)
    if request.method == "POST":
        try:
            execute(
                """
                UPDATE MatchEvent
                SET tournament_id=?, team1_id=?, team2_id=?, venue_id=?, match_date=?, round_name=?, status=?
                WHERE match_id=?
                """,
                (
                    int(request.form["tournament_id"]),
                    int(request.form["team1_id"]),
                    int(request.form["team2_id"]),
                    int(request.form["venue_id"]),
                    request.form["match_date"].replace("T", " "),
                    request.form["round_name"],
                    request.form["status"],
                    match_id,
                ),
            )
            flash("Match updated.", "ok")
            return redirect(url_for("matches_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template(
        "match_form.html",
        item=item,
        tournaments=tournaments(),
        teams=teams(),
        venues=venues(),
    )


@app.route("/matches/<int:match_id>/delete", methods=["POST"])
def match_delete(match_id):
    execute("DELETE FROM MatchEvent WHERE match_id = ?", (match_id,))
    flash("Match deleted.", "ok")
    return redirect(url_for("matches_list"))


@app.route("/results")
def results_list():
    rows = query("SELECT * FROM v_match_results ORDER BY match_date DESC")
    return render_template("results.html", rows=rows)


@app.route("/results/new", methods=["GET", "POST"])
def result_new():
    open_matches = query(
        """
        SELECT m.match_id, t.tournament_name, a.team_name AS team1, b.team_name AS team2
        FROM MatchEvent m
        JOIN Tournament t ON t.tournament_id = m.tournament_id
        JOIN Team a ON a.team_id = m.team1_id
        JOIN Team b ON b.team_id = m.team2_id
        LEFT JOIN Result r ON r.match_id = m.match_id
        WHERE r.result_id IS NULL AND m.status <> 'Cancelled'
        ORDER BY m.match_date
        """
    )
    if request.method == "POST":
        match_id = int(request.form["match_id"])
        match = query("SELECT * FROM MatchEvent WHERE match_id = ?", (match_id,), one=True)
        s1 = int(request.form["team1_score"])
        s2 = int(request.form["team2_score"])
        if s1 > s2:
            winner = match["team1_id"]
        elif s2 > s1:
            winner = match["team2_id"]
        else:
            winner = None
        try:
            execute(
                """
                INSERT INTO Result (match_id, winner_team_id, team1_score, team2_score, remarks)
                VALUES (?, ?, ?, ?, ?)
                """,
                (match_id, winner, s1, s2, request.form.get("remarks") or None),
            )
            execute("UPDATE MatchEvent SET status = 'Completed' WHERE match_id = ?", (match_id,))
            flash("Result recorded.", "ok")
            return redirect(url_for("results_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("result_form.html", matches=open_matches)


@app.route("/results/<int:match_id>/delete", methods=["POST"])
def result_delete(match_id):
    execute("DELETE FROM Result WHERE match_id = ?", (match_id,))
    execute("UPDATE MatchEvent SET status = 'Scheduled' WHERE match_id = ?", (match_id,))
    flash("Result cleared.", "ok")
    return redirect(url_for("results_list"))


@app.route("/prizes")
def prizes_list():
    rows = query(
        """
        SELECT pr.*, t.tournament_name, tm.team_name AS awarded_to, pd.awarded_date, pd.distribution_id
        FROM Prize pr
        JOIN Tournament t ON t.tournament_id = pr.tournament_id
        LEFT JOIN PrizeDistribution pd ON pd.prize_id = pr.prize_id
        LEFT JOIN Team tm ON tm.team_id = pd.team_id
        ORDER BY t.start_date DESC, pr.position
        """
    )
    return render_template("prizes.html", rows=rows)


@app.route("/prizes/new", methods=["GET", "POST"])
def prize_new():
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO Prize (tournament_id, position, prize_amount, prize_description)
                VALUES (?, ?, ?, ?)
                """,
                (
                    int(request.form["tournament_id"]),
                    int(request.form["position"]),
                    float(request.form["prize_amount"]),
                    request.form["prize_description"],
                ),
            )
            flash("Prize added.", "ok")
            return redirect(url_for("prizes_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    return render_template("prize_form.html", tournaments=tournaments())


@app.route("/prizes/<int:prize_id>/award", methods=["GET", "POST"])
def prize_award(prize_id):
    prize = query(
        """
        SELECT pr.*, t.tournament_name
        FROM Prize pr JOIN Tournament t ON t.tournament_id = pr.tournament_id
        WHERE pr.prize_id = ?
        """,
        (prize_id,),
        one=True,
    )
    if request.method == "POST":
        try:
            execute(
                "INSERT INTO PrizeDistribution (prize_id, team_id, awarded_date) VALUES (?, ?, ?)",
                (prize_id, int(request.form["team_id"]), request.form["awarded_date"]),
            )
            flash("Prize awarded.", "ok")
            return redirect(url_for("prizes_list"))
        except sqlite3.IntegrityError as exc:
            flash(str(exc), "err")
    eligible = query(
        """
        SELECT tm.team_id, tm.team_name
        FROM Registration r
        JOIN Team tm ON tm.team_id = r.team_id
        WHERE r.tournament_id = ? AND r.status = 'Approved'
        ORDER BY tm.team_name
        """,
        (prize["tournament_id"],),
    )
    return render_template("prize_award.html", prize=prize, teams=eligible)


@app.route("/prizes/<int:prize_id>/delete", methods=["POST"])
def prize_delete(prize_id):
    execute("DELETE FROM Prize WHERE prize_id = ?", (prize_id,))
    flash("Prize removed.", "ok")
    return redirect(url_for("prizes_list"))


@app.route("/rankings")
def rankings():
    tourney_id = request.args.get("tournament_id", type=int)
    all_t = tournaments()
    if not tourney_id and all_t:
        tourney_id = all_t[0]["tournament_id"]
    rows = query(
        """
        SELECT * FROM v_team_rankings
        WHERE tournament_id = ?
        ORDER BY points DESC, wins DESC, team_name
        """,
        (tourney_id,),
    ) if tourney_id else []
    return render_template("rankings.html", rows=rows, tournaments=all_t, tournament_id=tourney_id)


SQL_DEMOS = [
    {
        "id": "filter",
        "title": "Ordering & filtering",
        "topic": "WHERE, LIKE, BETWEEN, ORDER BY",
        "sql": """
SELECT player_name, ingame_id, age
FROM Player
WHERE age BETWEEN 18 AND 22
  AND player_name LIKE 'A%'
ORDER BY age DESC, player_name
""",
    },
    {
        "id": "inner",
        "title": "Inner join",
        "topic": "Players belonging to a team",
        "sql": """
SELECT p.player_name, p.role, t.team_name, t.coach_name
FROM Player p
INNER JOIN Team t ON t.team_id = p.team_id
WHERE t.team_name = 'Phoenix Esports'
""",
    },
    {
        "id": "left",
        "title": "Left outer join",
        "topic": "Matches with or without results",
        "sql": """
SELECT m.match_id, m.round_name, a.team_name AS team1, b.team_name AS team2,
       r.team1_score, r.team2_score
FROM MatchEvent m
INNER JOIN Team a ON a.team_id = m.team1_id
INNER JOIN Team b ON b.team_id = m.team2_id
LEFT JOIN Result r ON r.match_id = m.match_id
""",
    },
    {
        "id": "right",
        "title": "Outer join (venues)",
        "topic": "Venues even if unused (RIGHT JOIN equivalent)",
        "sql": """
SELECT v.venue_name, v.venue_type, m.match_id, m.round_name
FROM Venue v
LEFT JOIN MatchEvent m ON m.venue_id = v.venue_id
""",
    },
    {
        "id": "self",
        "title": "Self join",
        "topic": "Player and mentor on the same table",
        "sql": """
SELECT mentee.player_name AS player,
       mentor.player_name AS mentor,
       t.team_name
FROM Player mentee
INNER JOIN Player mentor ON mentee.mentor_id = mentor.player_id
INNER JOIN Team t ON t.team_id = mentee.team_id
""",
    },
    {
        "id": "agg",
        "title": "Aggregate + GROUP BY + HAVING",
        "topic": "Squad size and average age",
        "sql": """
SELECT t.team_name, COUNT(p.player_id) AS player_count, ROUND(AVG(p.age), 1) AS avg_age
FROM Team t
INNER JOIN Player p ON p.team_id = t.team_id
GROUP BY t.team_name
HAVING COUNT(p.player_id) >= 3
ORDER BY player_count DESC
""",
    },
    {
        "id": "sub",
        "title": "Subquery",
        "topic": "Teams that have won at least one match",
        "sql": """
SELECT team_name
FROM Team
WHERE team_id IN (
    SELECT DISTINCT winner_team_id
    FROM Result
    WHERE winner_team_id IS NOT NULL
)
""",
    },
    {
        "id": "nested",
        "title": "Nested query",
        "topic": "Players of the top-ranked team in Valorant Cup",
        "sql": """
SELECT player_name, ingame_id
FROM Player
WHERE team_id = (
    SELECT team_id
    FROM v_team_rankings
    WHERE tournament_id = 1
    ORDER BY points DESC, wins DESC
    LIMIT 1
)
""",
    },
    {
        "id": "view",
        "title": "View",
        "topic": "Tournament-wise prize distribution",
        "sql": """
SELECT * FROM v_prize_distribution ORDER BY tournament_name, position
""",
    },
    {
        "id": "union",
        "title": "Set operations",
        "topic": "UNION / INTERSECT / EXCEPT",
        "sql": """
SELECT 'Phoenix or Wolves player' AS source, player_name FROM Player WHERE team_id = 1
UNION
SELECT 'Phoenix or Wolves player', player_name FROM Player WHERE team_id = 2
""",
    },
]


@app.route("/sql-lab")
def sql_lab():
    selected = request.args.get("q", SQL_DEMOS[0]["id"])
    demo = next((d for d in SQL_DEMOS if d["id"] == selected), SQL_DEMOS[0])
    columns, rows, error = [], [], None
    try:
        fetched = query(demo["sql"])
        if fetched:
            columns = fetched[0].keys()
            rows = fetched
    except sqlite3.Error as exc:
        error = str(exc)
    return render_template("sql_lab.html", demos=SQL_DEMOS, demo=demo, columns=columns, rows=rows, error=error)


@app.route("/schema")
def schema_page():
    return render_template("schema.html")


@app.route("/reset", methods=["POST"])
def reset_db():
    close_db(None)
    init_db()
    flash("Database reset to sample data.", "ok")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    if not DB_PATH.exists():
        init_db()
    app.run(debug=True, port=5000)
