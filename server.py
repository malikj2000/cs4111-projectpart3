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


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print(request.args)

    #
    # example of a database query
    #
    cursor = g.conn.execute("SELECT * FROM users")
    names = []
    for result in cursor:
        # can also be accessed using result[0]
        names.append(result['first_name'])
    cursor.close()

    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    context = dict(data=names)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)


@app.route('/landing')
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

    # get user's friend list

    return render_template("profile_main.html", **context)

# Example of adding new data to the database


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

# example data
# ImmutableMultiDict([('email', '1'), ('earliest_year', '23'), ('latest_year', '123'),
# ('Danceability', '123'), ('Acousticness', '123'), ('Energy', '123'),
# ('explicit', 'on'), ('action', '')])


@app.route('/submit_music_preference_survey', methods=['POST'])
def submit_music_preference_survey():
    print("creating preference list")
    print(request.form)
    email = request.form['email']

    # get user_id based on email
    cursor = g.conn.execute(
        "SELECT user_id from users WHERE email = %s", email)
    user_id = None
    for result in cursor:
        user_id = result['user_id']
    print("WORKING ON user_id {}".format(user_id))

    # insert data into quiz_answers table commented out for now
    cursor = g.conn.execute("""INSERT INTO quiz_answers(quiz_result_id, max_year, min_year, danceability_preference, acousticness, is_explicit, energy )
    VALUES({}, {}, {}, {}, {}, {}, {})""".format(randrange(100000), request.form['earliest_year'], request.form['latest_year'], request.form['Danceability'], request.form['Acousticness'], 1, request.form['Energy']))

    # check if user has already submitted a survey
    cursor = g.conn.execute(
        "SELECT * from recommendation_list NATURAL JOIN(SELECT user_id from users WHERE email = %s) as id", email)
    if cursor.rowcount == 0:
        # generate unique recommendation list id
        recommendation_list_id = 5
        while(g.conn.execute("SELECT * from recommendation_list WHERE recommendation_list_id = %s", recommendation_list_id).rowcount == 0):
            recommendation_list_id = randrange(100000)

        # insert user id and recommendation list id into receives table
        cursor = g.conn.execute("""INSERT INTO receives(user_id, recommendation_list_id) VALUES({}, {})""".format(
            user_id, recommendation_list_id))
        # user hasn't submitted a form yet
        print(request.form)
        # select all songs that match the user's preferences
        cursor = g.conn.execute("""SELECT * FROM songs WHERE release_year >= {} AND release_year <= {}
        AND danceability >= {} - 0.2 AND danceability <= {} + 0.2
        AND acousticness >= {} - 0.2 AND acousticness <= {} + 0.2
        AND energy >= {} - 0.2 AND energy <= {} + 0.2
        """.format(request.form['earliest_year'], request.form['latest_year'], request.form['Danceability'], request.form['Danceability'], request.form['Acousticness'], request.form['Acousticness'], request.form['Energy'], request.form['Energy'])
        )

        for song in cursor:
            # insert song and recommendation list id into contains song table
            cursor = g.conn.execute("""INSERT INTO contains_song(recommendation_list_id, song_id) VALUES({}, {})""".format(
                recommendation_list_id, song['song_id']))
    return redirect('/')


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
