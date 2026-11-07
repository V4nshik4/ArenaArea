-- Sample data for demonstration and viva

INSERT INTO Team (team_name, coach_name, founded_year, status) VALUES
('Phoenix Esports', 'Rahul Mehta', 2021, 'Active'),
('Shadow Wolves', 'Ananya Kapoor', 2020, 'Active'),
('Neon Titans', 'Vikram Singh', 2022, 'Active'),
('Apex Legion', 'Sneha Iyer', 2019, 'Active'),
('Pixel Knights', 'Arjun Nair', 2023, 'Inactive');

INSERT INTO Player (player_name, email, ingame_id, role, age, team_id, mentor_id, join_date) VALUES
('Aarav Sharma', 'aarav@phoenix.in', 'AaravAce', 'Captain', 21, 1, NULL, '2022-01-15'),
('Diya Patel', 'diya@phoenix.in', 'DiyaDash', 'Member', 19, 1, 1, '2023-03-10'),
('Kabir Khan', 'kabir@phoenix.in', 'KabirKill', 'Member', 20, 1, 1, '2023-06-01'),
('Meera Joshi', 'meera@wolves.in', 'MeeraAim', 'Captain', 22, 2, NULL, '2021-08-20'),
('Rohan Gupta', 'rohan@wolves.in', 'RohanRush', 'Member', 18, 2, 4, '2024-01-12'),
('Ishita Verma', 'ishita@wolves.in', 'IshitaIQ', 'Substitute', 19, 2, 4, '2024-05-08'),
('Yash Malhotra', 'yash@titans.in', 'YashNova', 'Captain', 23, 3, NULL, '2022-11-02'),
('Priya Nair', 'priya@titans.in', 'PriyaPulse', 'Member', 20, 3, 7, '2023-09-18'),
('Aditya Rao', 'aditya@titans.in', 'AdiFrag', 'Member', 21, 3, 7, '2024-02-14'),
('Sana Sheikh', 'sana@apex.in', 'SanaSnap', 'Captain', 24, 4, NULL, '2020-04-01'),
('Nikhil Bose', 'nikhil@apex.in', 'NikClutch', 'Member', 22, 4, 10, '2021-12-11'),
('Tanya Gill', 'tanya@apex.in', 'TanyaTilt', 'Member', 18, 4, 10, '2025-01-20'),
('Harsh Vardhan', 'harsh@knights.in', 'HarshHold', 'Captain', 25, 5, NULL, '2023-07-07');

INSERT INTO Tournament (tournament_name, game_title, start_date, end_date, status, organizer_name, max_teams) VALUES
('Valorant Champions Cup 2026', 'Valorant', '2026-01-10', '2026-01-20', 'Completed', 'JIIT Esports Cell', 8),
('BGMI Winter Invitational', 'BGMI', '2026-02-01', '2026-02-15', 'Ongoing', 'Campus LAN League', 8),
('FIFA Campus League', 'EA Sports FC', '2026-03-05', '2026-03-12', 'Upcoming', 'Sports Club JIIT', 4);

INSERT INTO Venue (venue_name, venue_type, location, capacity) VALUES
('JIIT Main Arena', 'Offline', 'Sector 62, Noida', 200),
('AB-10 LAN Lab', 'Offline', 'JIIT Campus, Noida', 40),
('Discord Stage Alpha', 'Online', 'discord.gg/gtms-alpha', NULL),
('Twitch Studio Hub', 'Online', 'twitch.tv/gtms_official', NULL);

INSERT INTO TournamentVenue (tournament_id, venue_id) VALUES
(1, 1), (1, 3),
(2, 2), (2, 4),
(3, 1);

INSERT INTO Registration (tournament_id, team_id, registration_date, status) VALUES
(1, 1, '2025-12-01', 'Approved'),
(1, 2, '2025-12-02', 'Approved'),
(1, 3, '2025-12-03', 'Approved'),
(1, 4, '2025-12-04', 'Approved'),
(2, 1, '2026-01-05', 'Approved'),
(2, 2, '2026-01-06', 'Approved'),
(2, 3, '2026-01-07', 'Approved'),
(2, 4, '2026-01-08', 'Pending'),
(3, 1, '2026-02-10', 'Approved'),
(3, 4, '2026-02-11', 'Rejected');

INSERT INTO MatchEvent (tournament_id, team1_id, team2_id, venue_id, match_date, round_name, status) VALUES
(1, 1, 2, 1, '2026-01-12 16:00', 'Semifinal', 'Completed'),
(1, 3, 4, 1, '2026-01-12 19:00', 'Semifinal', 'Completed'),
(1, 1, 3, 1, '2026-01-20 18:00', 'Final', 'Completed'),
(1, 2, 4, 3, '2026-01-20 15:00', 'Third Place', 'Completed'),
(2, 1, 2, 2, '2026-02-05 17:00', 'Group', 'Completed'),
(2, 2, 3, 4, '2026-02-07 17:00', 'Group', 'Scheduled'),
(2, 1, 3, 2, '2026-02-09 17:00', 'Group', 'Live');

INSERT INTO Result (match_id, winner_team_id, team1_score, team2_score, remarks) VALUES
(1, 1, 13, 8,  'Phoenix closed on Bind'),
(2, 3, 13, 11, 'Overtime avoided, Neon Titans clutch'),
(3, 1, 13, 10, 'Phoenix Esports crowned champions'),
(4, 2, 13, 7,  'Shadow Wolves take bronze'),
(5, 1, 2, 1,   'BGMI Erangel circle win');

INSERT INTO Prize (tournament_id, position, prize_amount, prize_description) VALUES
(1, 1, 50000, 'Champion trophy + cash'),
(1, 2, 25000, 'Runner-up cash'),
(1, 3, 10000, 'Second runner-up cash'),
(2, 1, 30000, 'BGMI winner purse'),
(2, 2, 15000, 'BGMI runner-up purse');

INSERT INTO PrizeDistribution (prize_id, team_id, awarded_date) VALUES
(1, 1, '2026-01-20'),
(2, 3, '2026-01-20'),
(3, 2, '2026-01-20');
