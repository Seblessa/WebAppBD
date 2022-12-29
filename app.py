import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from flask import abort, render_template, Flask,request
import logging
import db

APP = Flask(__name__)

# Start page
@APP.route('/')
def index():

    stats = {}
    x = db.execute('SELECT COUNT(*) AS g FROM game').fetchone()
    stats.update(x)
    x = db.execute('SELECT COUNT(*) AS p FROM publisher').fetchone()
    stats.update(x)
    x = db.execute('SELECT COUNT(*) AS t FROM tag').fetchone()
    stats.update(x)
    x = db.execute('SELECT COUNT(*) AS pl FROM platform').fetchone()
    stats.update(x)
    x = db.execute('SELECT COUNT(*) AS r FROM reviews').fetchone()
    stats.update(x)
    logging.info(stats)

    return render_template('index.html',stats=stats)

@APP.route('/game_year_count/')
def listYearCount():
    count = db.execute(
        '''
        select release_year, count(*) as year_count
        from game
        group by release_year
        order by release_year
        ''').fetchall()


    return render_template('game_year_count.html', count=count)

@APP.route('/game_in_year/<int:year>')
def GetGames_year(year):

    game = db.execute(
        '''
        SELECT g.id ,g.name,g.release_year,COUNT(t.name) AS tags_count
        FROM GAME g
        JOIN GAME_TAG GT on g.id = gt.game_id
        JOIN TAG t on t.id = gt.tag_id
        WHERE g.release_year = %s
        group by g.id ,g.name,g.release_year
        ''',year).fetchall()


    return render_template('game_in_year.html', game=game,year=year)


@APP.route('/game/3waySearch/')
def GetGame3waySearch():
    return render_template('game-3way-search.html')

@APP.route('/game/3waySearchResult/')
def GetGame3waySearchResult():
    Publisher  = request.args.get('Publisher', type=str ,default='')
    Tag  = request.args.get('Tag',type=str , default='')
    Platform  = request.args.get('Platform',type=str , default='')

    search = db.execute(
        '''
        SELECT g.id as g_id,g.name as g_name,p.id as p_id,p.name as p_name,t.id as t_id,t.name as t_name,pl.id as pl_id,pl.name as pl_name
        from GAME g
        join PUBLISHER p on p.id = g.publisher_id
        join GAME_TAG gt on g.id = gt.game_id
        join TAG t on t.id = gt.tag_id
        join PLATFORM_GAME pg on g.id = pg.game_id
        join PLATFORM pl on pl.id = pg.platform_id
        where p.name = '%s' and t.name = '%s' and pl.name='%s'
        order by g.name
        '''%(Publisher,Tag,Platform)).fetchall()



    return render_template('game-3way-search-result.html',search=search,Publisher=Publisher,Tag=Tag,Platform=Platform)



                                        #GAME
@APP.route('/game/')
def listGame():

    game = db.execute(
        '''
        SELECT g.id as g_id,p.id as p_id,p.name as p_name,g.name as g_name,g.price,g.release_year,g.description
        FROM GAME g
        join PUBLISHER p on g.publisher_id = p.id
        ORDER BY g.name
        ''').fetchall()


    return render_template('game-list.html', game=game)


@APP.route('/game/<int:id>/')
def getGame(id):
    game = db.execute(
        '''
        SELECT g.id g_id ,g.name g_name ,p.id p_id ,p.name p_name, g.price,g.release_year, g.description
        FROM PUBLISHER p
        join GAME g on g.publisher_id = p.id
        WHERE g.id = %s
        ''', id).fetchone()

    if game is None:
        abort(404, 'Game id {} does not exist.'.format(id))


    tag = db.execute(
        '''
        SELECT t.id, t.name 
        FROM TAG as t
        join GAME_TAG GT on t.id = GT.tag_id
        join GAME G on G.id = GT.game_id
        WHERE g.id = %s 
        order by t.name
        ''', id).fetchall()

    platform = db.execute(
        '''
        SELECT p.id, p.name
        FROM PLATFORM as p 
        JOIN PLATFORM_GAME on p.id = PLATFORM_GAME.platform_id
        join GAME G on PLATFORM_GAME.game_id = G.id
        WHERE game_id = %s
        ''', id).fetchall()

    reviews = db.execute(
        ''' 
        SELECT id, rating,review
        FROM REVIEWS
        WHERE game_id = %s
        ''', id).fetchall()


    return render_template('game.html',game=game, tag=tag, platform=platform, reviews=reviews)

@APP.route('/game/search/<expr>/')
def searchGame(expr):
    search = { 'expr': expr }
    expr = '%' + expr + '%'
    game = db.execute(
        '''
        SELECT id,name 
        FROM GAME 
        WHERE name LIKE %s 
        order by name
        '''
        ,expr).fetchall()
    return render_template('game-search.html', search=search,game=game)

                                          #PUBLISHER
@APP.route('/publisher/')
def listPublisher():
    publisher = db.execute('''
      SELECT p.id,p.name,p.followers, count(p.name) as game_count
      FROM PUBLISHER p
      join GAME G on p.id = G.publisher_id
      group by p.id, p.name
      ORDER BY p.name
    ''').fetchall()
    return render_template('publisher-list.html', publisher=publisher)


@APP.route('/publisher/<int:id>/')
def getPublisher(id):
    publisher = db.execute(
        '''
        SELECT id, name,followers
        FROM PUBLISHER 
        WHERE id = %s
        ''', id).fetchone()

    if publisher is None:
        abort(404, 'Publisher id {} does not exist.'.format(id))

    game = db.execute(
        '''
        SELECT id,name
        FROM GAME
        WHERE publisher_id = %s
        ORDER BY name
        ''', id).fetchall()

    return render_template('publisher.html', publisher=publisher, game=game)


@APP.route('/publisher/search/<expr>/')
def searchPublisher(expr):
    search = { 'expr': expr }
    expr = '%' + expr + '%'
    publisher = db.execute(
        ''' 
        SELECT id,name
        FROM PUBLISHER
        WHERE name LIKE %s
        ''', expr).fetchall()
    return render_template('publisher-search.html', search=search,publisher=publisher)



                                                     #TAGS
@APP.route('/tag/')
def listTag():
    tag = db.execute('''
        SELECT t.id, t.name, COUNT(t.name) AS game_count
        FROM tag t
        JOIN game_tag gt ON t.id = gt.tag_id
        JOIN game g ON g.id = gt.game_id
        GROUP BY t.id, t.name
        ORDER BY t.name
    ''').fetchall()
    return render_template('tag-list.html', tag=tag)

@APP.route('/tag/<int:id>/')
def getTag(id):
    tag = db.execute(
        '''
        SELECT id,name
        FROM TAG
        WHERE id = %s
        ''', id).fetchone()
    game = db.execute(
        '''
        SELECT g.id,g.name
        FROM GAME g
        join GAME_TAG GT on g.id = GT.game_id
        join TAG T on T.id = GT.tag_id
        WHERE T.id = %s
        ORDER BY g.name
        ''', id).fetchall()

    if tag is None:
        abort(404, 'Tag id {} does not exist.'.format(id))

    return render_template('tag.html', tag=tag,game=game)


@APP.route('/tag/search/<expr>/')
def search_tag(expr):
    search = { 'expr': expr }
    #expr = '%' + expr + '%'
    game = db.execute(
        ''' 
        SELECT G.id,G.name
        FROM GAME G
        join GAME_TAG GT on G.id = GT.game_id
        join TAG T on T.id = GT.tag_id
        WHERE T.name = %s
        order by G.name
        ''', expr).fetchall()
    return render_template('tag-search.html', search=search,game=game)




                                                    #PLATFORM
@APP.route('/platform/<int:id>/')
def getPlatform(id):
    platform = db.execute(
        '''
        SELECT p.id,p.name,g.id,g.name
        FROM GAME as g
        join PLATFORM_GAME PG on PG.game_id = g.id
        join PLATFORM p on p.id = PG.platform_id
        WHERE p.id = %s
        ''', id).fetchone()
    game = db.execute(
        '''
        SELECT g.id,g.name
        FROM GAME g
        join PLATFORM_GAME PG on PG.game_id = g.id
        join PLATFORM p on p.id = PG.platform_id
        WHERE p.id = %s
        ORDER BY name
        ''', id).fetchall()

    if platform is None:
        abort(404, 'Platform id {} does not exist.'.format(id))

    return render_template('platform.html', platform=platform,game=game)

@APP.route('/platform/')
def listPlatform():
    platform = db.execute(
        '''
        SELECT p.id,p.name,count(p.name) as game_count
        FROM PLATFORM p
        join PLATFORM_GAME PG on p.id = PG.platform_id
        join GAME G on G.id = PG.game_id
        group by p.id,p.name
        ORDER BY p.id
        ''').fetchall()
    return render_template('platform-list.html', platform=platform)


                                                   # REVIEWS
@APP.route('/reviews/<int:id>/')
def getReviews(id):
    reviews = db.execute(
        '''
        SELECT R.rating,R.review,R.id as r_id,G.id as g_id,G.name
        FROM REVIEWS R
        join GAME G on G.id = R.game_id
        WHERE R.id = %s
        ''', id).fetchone()

    if reviews is None:
        abort(404, 'Reviews  id {} does not exist.'.format(id))

    return render_template('reviews.html', reviews=reviews)


@APP.route('/reviews/')
def listReviews():
    reviews = db.execute(
        '''
        SELECT R.rating,R.review,R.id as r_id,G.id as g_id,G.name
        FROM REVIEWS R
        join GAME G on G.id = R.game_id
        ORDER BY R.id
        ''').fetchall()
    return render_template('reviews-list.html', reviews=reviews)