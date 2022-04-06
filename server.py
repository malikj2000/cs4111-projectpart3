#!/usr/bin/env python


"""
Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from random import randrange

tmpl_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


DATABASEURI = "postgresql://maj2187:5379@35.211.155.104/proj1part2"
engine = create_engine(DATABASEURI)

# Example of running queries in your database

# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute(
#     """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


@app.route('/')
def landing():
    return render_template("landing.html")


@app.route('/landing_fail')
def landing_fail():
    return render_template("landing_fail.html")


@app.route('/create_account')
def create_account():
    return render_template("create_account.html")


@app.route('/survey_page')
def survey_page():
    print("called")
    return render_template("survey_page.html")


@app.route('/profile_main.html')
def profile_main(user_id):
    context = {}
    # get first name last name and add it to context
    cursor = g.conn.execute(
        "SELECT first_name, last_name FROM users WHERE user_id = %s", user_id)
    for result in cursor:
        context['first_name'] = result['first_name']
        context['last_name'] = result['last_name']
    cursor.close()

    # get a user's song recommendations
    cursor = g.conn.execute(
        """SELECT title, artist, album, release_year FROM recommendation_list NATURAL JOIN contains_song NATURAL JOIN songs WHERE user_id = %s""", user_id)
    # add songs to context
    songs = []
    # generate dictionary for each song
    for result in cursor:
        songs.append(result)

    context['songs'] = songs

    # get user's friend list
    cursor = g.conn.execute(
        """ SELECT first_name, last_name, user_id FROM users WHERE user_id IN (SELECT friend_id FROM friends_with WHERE user_id = %s)""", user_id)
    friends = []
    for result in cursor:
        friends.append(result)
    if(len(friends) > 0):
        context['friends'] = friends
    # get song recommendations of friends
    print(context)

    # add user_id to context
    context['user_id'] = user_id

    return render_template("profile_main.html", **context)

# Example of adding new data to the database


@app.route('/add_friend', methods=['POST'])
def add_friend():
    print("attempting to add friend")
    user_id = request.form['user_id']
    friend_username = request.form['friend_username']
    # check if friend exists
    cursor = g.conn.execute(
        """ SELECT user_id FROM users WHERE email = %s""", friend_username)
    if cursor.rowcount == 0:
        print("friend not found")
        return profile_main(user_id)
    # get friend user_id
    friend_id = None
    for result in cursor:
        friend_id = result['user_id']
    if(user_id == friend_id):
        print("cannot add yourself as a friend")
        return profile_main(user_id)
    # check if user is already friends with friend
    cursor = g.conn.execute(
        """ SELECT * FROM friends_with WHERE user_id = %s AND friend_id = %s""", user_id, friend_id)
    if cursor.rowcount != 0:
        print("already friends")
        return profile_main(user_id)
    # add friend to friends_with table
    g.conn.execute(
        """ INSERT INTO friends_with (user_id, friend_id) VALUES (%s, %s)""", user_id, friend_id)

    return profile_main(user_id)


@ app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    print("logging in {} {}".format(email, password))
    cursor = g.conn.execute("SELECT * FROM users WHERE email = %s", email)
    if cursor.rowcount == 0:
        print("no user found")
        return redirect("landing_fail")
    else:
        print("user found")
        for result in cursor:
            if result['user_password'] == password:
                print("password correct")
                # get user id
                user_id = result['user_id']
                cursor = g.conn.execute(
                    "SELECT * FROM inputs WHERE user_id = %s", user_id)
                if cursor.rowcount == 0:
                    print("survey not done")
                    return render_template("survey_page.html", user_id=user_id)
                else:
                    print("survey done")
                    return profile_main(user_id)
            else:
                print("password incorrect")
                return render_template("landing_fail.html")
    return redirect('/')


@app.route('/create_account_post', methods=['POST'])
def create_account_post():
    user_id = randrange(100000)
    username = request.form['email']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    dob = request.form['dob']
    gender = 1 if request.form['gender'] == "M" else 0
    print("creating account with user: {} and password: {}".format(username, password))
    cursor = g.conn.execute("INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, 0)",
                            user_id, first_name, last_name, username, dob, password, gender)
    print("account created")
    return render_template("survey_page.html")

# example data
# ImmutableMultiDict([('email', '1'), ('earliest_year', '23'), ('latest_year', '123'),
# ('Danceability', '123'), ('Acousticness', '123'), ('Energy', '123'),
# ('explicit', 'on'), ('action', '')])


@app.route('/submit_music_preference_survey', methods=['POST'])
def submit_music_preference_survey():
    print("creating preference list")
    email = request.form['email']

    # get user_id based on email
    cursor = g.conn.execute(
        "SELECT user_id from users WHERE email = %s", email)
    user_id = None
    for result in cursor:
        user_id = result['user_id']
    print("WORKING ON user_id {}".format(user_id))
    quiz_result_id = randrange(100000)
    # insert data into quiz_answers table commented out for now
    cursor = g.conn.execute("""INSERT INTO quiz_answers(quiz_result_id, max_year, min_year, danceability_preference, acousticness, is_explicit, energy )
    VALUES({}, {}, {}, {}, {}, {}, {})""".format(quiz_result_id, request.form['latest_year'], request.form['earliest_year'], request.form['Danceability'], request.form['Acousticness'], 1, request.form['Energy']))

    # insert data into inputs table
    cursor = g.conn.execute(
        "INSERT INTO inputs(user_id, quiz_result_id) VALUES({}, {})".format(user_id, quiz_result_id))

    # check if user has already submitted a survey

    # generate unique recommendation list id
    recommendation_list_id = randrange(100000)
    while(g.conn.execute("SELECT * from recommendation_list WHERE recommendation_list_id = %s", recommendation_list_id).rowcount != 0):
        recommendation_list_id = randrange(100000)
    print("hi")

    # insert data into recommendation_list table
    cursor = g.conn.execute("""INSERT INTO recommendation_list(recommendation_list_id, user_id) VALUES({}, {})""".format(
        recommendation_list_id, user_id))
    print("yo")

    # select all songs that match the user's preferences
    cursor = g.conn.execute("""SELECT * FROM songs WHERE release_year >= {} AND release_year <= {}
    AND danceability >= {} - 0.2 AND danceability <= {} + 0.2
    AND acousticness >= {} - 0.2 AND acousticness <= {} + 0.2
    AND energy >= {} - 0.2 AND energy <= {} + 0.2
    """.format(request.form['earliest_year'], request.form['latest_year'], request.form['Danceability'], request.form['Danceability'], request.form['Acousticness'], request.form['Acousticness'], request.form['Energy'], request.form['Energy'])
    )

    print("uncle")

    for song in cursor:
        # insert song and recommendation list id into contains song table
        cursor = g.conn.execute("""INSERT INTO contains_song(recommendation_list_id, song_id) VALUES({}, {})""".format(
            recommendation_list_id, song['song_id']))
    print("songs selected")

    # select all albums that match the user's preferences
    cursor = g.conn.execute("""SELECT * FROM albums WHERE release_year >= {} AND release_year <= {}
    AND danceability >= {} - 0.2 AND danceability <= {} + 0.2
    AND acousticness >= {} - 0.2 AND acousticness <= {} + 0.2
    AND energy >= {} - 0.2 AND energy <= {} + 0.2
    """.format(request.form['earliest_year'], request.form['latest_year'], request.form['Danceability'], request.form['Danceability'], request.form['Acousticness'], request.form['Acousticness'], request.form['Energy'], request.form['Energy'])
    )

    print("albums selected")

    for album in cursor:
        # insert song and recommendation list id into contains song table
        cursor = g.conn.execute("""INSERT INTO contains_album(recommendation_list_id, song_id) VALUES({}, {})""".format(
            recommendation_list_id, album['album_id']))
    print('added')

    # insert user id and recommendation list id into receives table
    cursor = g.conn.execute("""INSERT INTO receives(user_id, recommendation_list_id) VALUES({}, {})""".format(
        user_id, recommendation_list_id))

    return profile_main(user_id)


@ app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
    return redirect('/')


if __name__ == "__main__":
    import click

    @ click.command()
    @ click.option('--debug', is_flag=True)
    @ click.option('--threaded', is_flag=True)
    @ click.argument('HOST', default='0.0.0.0')
    @ click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=True, threaded=threaded)

    run()
