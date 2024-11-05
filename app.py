import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from flask import render_template, Flask, abort
import logging
import db

APP = Flask(__name__)

# Start page
@APP.route('/')
def index():
    stats = {}
    stats = db.execute('''
    SELECT * FROM
      (SELECT COUNT(*) n_games FROM Games)
    JOIN
      (SELECT COUNT(*) n_goals FROM Goals)
    JOIN
      (SELECT COUNT(*) n_teams FROM Teams)
    JOIN 
      (SELECT COUNT(*) n_competitions FROM Competitions)
    JOIN 
      (SELECT COUNT(*) n_players FROM Players)
    ''').fetchone()
    logging.info(stats)
    return render_template('index.html',stats=stats)

# Games
@APP.route('/games/')
def list_games():
    games = db.execute(
      '''
      select G.GameId, Date,H.TeamName as HName, A.TeamName as AName, HomeScore, AwayScore, Competitions.CompetitionName as comp, City, Country, Neutral 
    from games G
    join gamecompt on gamecompt.GameId=G.GameId
    join competitions on competitions.CompetitionId=gamecompt.CompetitionId
    join teams H on G.HomeTeamId=H.TeamId
    join teams A on G.AwayTeamId=A.teamId
    order by Date;
      ''').fetchall()
    return render_template('games-list.html', games=games)
@APP.route('/games/<int:id>/')
def get_games(id):
    game = db.execute(
      '''
      select G.GameId, Date,H.TeamName as HName, A.TeamName as AName, HomeScore, AwayScore, Competitions.CompetitionName, City, Country, Neutral 
    from games G
    join gamecompt on gamecompt.GameId=G.GameId
    join competitions on competitions.CompetitionId=gamecompt.CompetitionId
    join teams H on G.HomeTeamId=H.TeamId
    join teams A on G.AwayTeamId=A.teamId
      WHERE gamecompt.gameId = ?
      ''', [id]).fetchone()

    if game is None:
        abort(404, 'Game id {} does not exist.'.format(id))
    teams = db.execute(
      '''
      select t.TeamId, t.TeamName
from (
SELECT
gamecompt.GameId as id,
    h.TeamId AS TeamId,
    h.TeamName AS TeamName
FROM
    games g
    join
  gamecompt on gamecompt.GameId=g.GameId
JOIN
    teams h ON g.HomeTeamId = h.TeamId

UNION

SELECT
    gamecompt.GameId as id,
    a.TeamId AS TeamId,
    a.TeamName AS TeamName
FROM
    games g
    join
  gamecompt on gamecompt.GameId=g.GameId
JOIN
    teams a ON g.AwayTeamId = a.TeamId
    ) t
where t.id=?;
      ''', [id]).fetchall()
    
    competitions = db.execute(
      '''
        select competitions.CompetitionId, CompetitionName
  from games join
  gamecompt on gamecompt.GameId=Games.GameId
  join competitions on competitions.CompetitionId=gamecompt.CompetitionId
  where gamecompt.GameId=?;
      ''', [id]).fetchall()
    
    goals = db.execute(
      '''
      select GoalId, PlayerName, GameId, Minute
  from goals join games on goals.Game=games.GameId
  join Players on goals.Scorer=Players.PlayerId
  where goals.Game=?;
      ''', [id]).fetchall()
    
    return render_template('game.html', 
        game=game,teams=teams, competitions=competitions,goals=goals)

@APP.route('/gamesgoals/')
def list_gamesgoals():
    gamesgoals = db.execute('''
          SELECT games.GameId, H.TeamName as Home, A.TeamName as Away, HomeScore + AwayScore AS TotalGoals, HomeScore, AwayScore, competitions.CompetitionName

  FROM games join teams H on H.TeamId=games.HomeTeamId 
  join teams A on A.TeamId=games.AwayTeamId
  join competitions on competitions.CompetitionId=gamecompt.CompetitionId
  join gamecompt on gamecompt.GameId=games.GameId

  ORDER BY TotalGoals DESC 

  LIMIT 100; 

    ''').fetchall()
    return render_template('gamesgoals-list.html', gamesgoals=gamesgoals)

# GOALS
@APP.route('/goals/')
def list_goals():
    goals = db.execute('''
      select games.Date, Players.PlayerName as Scorer, Game, Minute, OwnGoal, Penalty, teams.TeamName
    from goals join Teams on goals.Team=teams.TeamId
    join games on goals.Game=games.GameId
    join Players on Goals.Scorer=Players.PlayerId
    order by Date;
    ''').fetchall()
    return render_template('goals-list.html', goals=goals)


@APP.route('/goals/<int:id>/')
def view_goals_by_id(id):
    goals = db.execute(
        '''
        select GoalId, games.Date, Players.PlayerName as Scorer, Game, Minute, OwnGoal, Penalty, teams.TeamName 
    from goals join Teams on goals.Team=teams.TeamId
    join games on goals.Game=games.GameId
    join Players on Goals.Scorer=Players.PlayerId
        WHERE GoalId = ?
        ''', [id]).fetchone()

    if goals is None:
        abort(404, 'Goal id {} does not exist.'.format(id))
    teams = db.execute(
      '''
      select goals.Team, teams.TeamName as nome
      from goals, teams on goals.Team=teams.TeamId
      where GoalId=?;
      ''', [id]).fetchall()
    
    
    games = db.execute(
      '''
    select GameId,H.TeamName as HName, A.TeamName as AName, HomeScore, AwayScore
    from (games G
    join teams H on G.HomeTeamId=H.TeamId
    join teams A on G.AwayTeamId=A.teamId) t
    join goals on goals.Game=G.GameId
  where GoalId=?;
      ''', [id]).fetchall()
    
    return render_template('goal.html', 
        goals=goals,teams=teams, games=games) 

# Competitions
@APP.route('/competitions/')
def list_competitions():
    competitions = db.execute('''
      select *
from competitions
order by CompetitionName;
    ''').fetchall()
    return render_template('competitions-list.html', competitions=competitions)

@APP.route('/competitions/<int:id>/')
def view_competitions_by_id(id):
    competitions = db.execute(
        '''
        select *
    from competitions
    where CompetitionId = ?
        ''', [id]).fetchone()

    if competitions is None:
        abort(404, 'Competition id {} does not exist.'.format(id))
    njogos=db.execute(
        '''
        select Count(*) as nr
    from games
    join gamecompt on gamecompt.GameId=Games.GameId
    join competitions on competitions.CompetitionId=gamecompt.CompetitionId
    where competitions.CompetitionId=?;
        ''',[id]).fetchall()
    games = db.execute(
      '''
    select t.GameId,H.TeamName as HName, A.TeamName as AName, HomeScore, AwayScore, Date
    from (games G
    join teams H on G.HomeTeamId=H.TeamId
    join teams A on G.AwayTeamId=A.teamId) t
    join gamecompt on gamecompt.GameId=t.GameId
    join competitions on competitions.CompetitionId=gamecompt.CompetitionId
    where competitions.CompetitionId=?;
      ''', [id]).fetchall()
    
    return render_template('competition.html', 
        competitions=competitions,games=games,njogos=njogos)

@APP.route('/competitions/search/<expr>/')
def search_competition(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  competitions = db.execute(
      ''' 
      SELECT CompetitionId, CompetitionName
      from competitions
      WHERE CompetitionName LIKE ?
      ''', [expr]).fetchall()
  return render_template('competition-search.html',
           search=search,competitions=competitions)
    

# Teams
@APP.route('/teams/')
def list_teams():
    teams = db.execute('''
        SELECT *
        from teams
        order by TeamName;
    ''').fetchall()
    return render_template('teams-list.html', teams=teams)

@APP.route('/teams/<int:id>/')
def view_teams_by_id(id):
    teams = db.execute(
        '''
        SELECT *
        FROM teams 
        WHERE TeamId = ?
        ''', [id]).fetchone()

    if teams is None:
        abort(404, 'Team id {} does not exist.'.format(id))
    games = db.execute(
      '''
    SELECT
    g.GameId,
    g.HomeTeamId,
    homeTeam.TeamName AS HomeTeamName,
    g.AwayTeamId,
    awayTeam.TeamName AS AwayTeamName,
    g.Date,
    g.HomeScore,
    g.AwayScore
FROM
    games g
JOIN
    teams homeTeam ON g.HomeTeamId = homeTeam.TeamId
JOIN
    teams awayTeam ON g.AwayTeamId = awayTeam.TeamId
WHERE
    ? IN (g.HomeTeamId, g.AwayTeamId);

      ''', [id]).fetchall()
    
    return render_template('team.html', 
        teams=teams,games=games)
@APP.route('/teams/search/<expr>/')
def search_team(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  teams = db.execute(
      ''' 
      SELECT TeamId, TeamName
      from teams
      WHERE TeamName LIKE ?
      ''', [expr]).fetchall()
  return render_template('team-search.html',
           search=search,teams=teams)

# PLAYERS
@APP.route('/players/')
def list_players():
    players = db.execute('''
      select PlayerId, PlayerName
      from players
      order by PlayerName;
    ''').fetchall()
    return render_template('players-list.html', players=players)


@APP.route('/players/<int:id>/')
def view_players_by_id(id):
    players = db.execute(
        '''
        select PlayerId, PlayerName
        from players
        WHERE PlayerId=?;
        ''', [id]).fetchone()

    if players is None:
        abort(404, 'Player id {} does not exist.'.format(id))
    
    goals = db.execute(
      '''
      select GoalId, Minute, Team, H.TeamName as Home, A.TeamName as Away
      from goals join players on goals.Scorer=players.PlayerId
      join games on games.GameId=goals.Game
      join teams H on H.TeamId=games.HomeTeamId
      join teams A on A.TeamId=games.AwayTeamId
      where PlayerId=?;
      ''', [id]).fetchall()
    teams=goals = db.execute(
      '''
      select GoalId, Minute, Team, H.TeamName as Home, A.TeamName as Away
      from goals join players on goals.Scorer=players.PlayerId
      join games on games.GameId=goals.Game
      join teams H on H.TeamId=games.HomeTeamId
      join teams A on A.TeamId=games.AwayTeamId
      where PlayerId=?;
      ''', [id]).fetchall()
    
    goalsscored = db.execute(
      '''
      select count(*) as gscored
      from goals join players on goals.Scorer=players.PlayerId
      where PlayerId=?;
      ''', [id]).fetchall()
    
    return render_template('player.html', 
        players=players, goals=goals, goalsscored=goalsscored)
@APP.route('/players/search/<expr>/')
def search_player(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  players = db.execute(
      ''' 
      SELECT PLayerId, PlayerName
      from players
      WHERE PlayerName LIKE ?
      ''', [expr]).fetchall()
  return render_template('player-search.html',
           search=search,players=players)

# BESTSCORERS
@APP.route('/bestscorers/')
def list_bestscorers():
    competitions = db.execute('''
      select *
from competitions
order by CompetitionName;
    ''').fetchall()
    return render_template('bestscorers-list.html', competitions=competitions)

@APP.route('/bestscorers/<int:id>/')
def view_bestscorers_by_competitionid(id):
    competitions = db.execute(
        '''
        select *
        from competitions
        where CompetitionId=?;
        ''', [id]).fetchone()

    if competitions is None:
        abort(404, 'Competition id {} does not exist.'.format(id))
    scorers = db.execute(
  '''
  select PlayerId, PlayerName, count(*) as nrgolos
  from players join goals on players.PlayerId=goals.Scorer
  join games on games.GameId=goals.Game
  join gamecompt on games.GameId=gamecompt.GameId
  join competitions on competitions.CompetitionId=gamecompt.CompetitionId
  group by gamecompt.CompetitionId, playerId
  having gamecompt.CompetitionId=?
  order by nrgolos desc
  limit 100;
  ''', [id]).fetchall()
    if scorers is None:
        abort(404, 'There is no data available for this competition. Try, for example, the FIFA World Cup')
    return render_template('bestscorer.html', 
        scorers=scorers, competitions=competitions)
        

# BSCORERS 2
@APP.route('/scorerscompetitions/')
def list_scorerscompetitions():
    scorerscompetitions = db.execute('''
      SELECT players.PlayerName,players.PlayerId, teams.TeamName, competitions.CompetitionName, COUNT(goals.GoalId) AS total_gols
FROM players
JOIN teams ON goals.Team = teams.TeamId
JOIN goals ON players.PlayerId = goals.Scorer
JOIN games ON goals.Game = games.GameId
join gamecompt on games.GameId=gamecompt.GameId
JOIN competitions ON gamecompt.CompetitionId = competitions.CompetitionId
GROUP BY players.PlayerId, teams.TeamName, competitions.CompetitionName
ORDER BY total_gols DESC
limit 100;
    ''').fetchall()
    return render_template('scorerscompetitions-list.html', scorerscompetitions=scorerscompetitions)
@APP.route('/stats/')
def stats():
    stats = db.execute('''
SELECT
    Teams.TeamId,
    Teams.TeamName,
    COUNT(CASE
        WHEN (Teams.TeamId = Games.HomeTeamId AND Games.HomeScore > Games.AwayScore)
             OR (Teams.TeamId = Games.AwayTeamId AND Games.AwayScore > Games.HomeScore)
        THEN Games.GameId
    END) AS Wins,
    COUNT(CASE
        WHEN Games.HomeScore = Games.AwayScore
        THEN Games.GameId
    END) AS Draws,
    COUNT(CASE
        WHEN (Teams.TeamId = Games.HomeTeamId AND Games.HomeScore < Games.AwayScore)
             OR (Teams.TeamId = Games.AwayTeamId AND Games.AwayScore < Games.HomeScore)
        THEN Games.GameId
    END) AS Losses
FROM
    Teams
JOIN
    Games ON Teams.TeamId = Games.HomeTeamId OR Teams.TeamId = Games.AwayTeamId
GROUP BY
    Teams.TeamId, Teams.TeamName;
                              ''').fetchall()
    return render_template('stats.html', stats=stats)


