import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
import numpy as np
import matplotlib.pyplot as plt
from efficient_frontier import Portfolio
import pandas.io.data as web


app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flask_trade.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin'
))
app.config.from_envvar('FLASK_TRADE_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    # rv = [dict((cur.description[idx][0], value)
    #           for idx, value in enumerate(row)) for row in cur.fetchall()]
    # return (rv[0] if rv else None) if one else rv
    return cur.fetchall()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/', methods=['GET'])
def show_entries():
    entries = query_db('select * from entries where id = \
                       (select max(id) from entries)', one=False)
    return render_template('list.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not request.form['first']:
        return redirect(url_for('show_entries'))
    g.db.execute('insert into entries (first, second, third, fourth, fifth) \
                 values (?, ?, ?, ?, ?)', [request.form['first'],
                 request.form['second'], request.form['third'],
                 request.form['fourth'], request.form['fifth']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('render_plot'))  # ('show_entries'))


@app.route('/plot', methods=['GET'])
def render_plot():
    symbols = []
    entries = query_db('select * from entries where id = \
                       (select max(id) from entries)', one=False)
    ent = list(entries[0])[1:]
    for _ in ent:
        if _:
            symbols.append(_)
    beg_date = request.form.get('begdate')
    end_date = request.form.get('enddate')
    beg_date = int(beg_date) if beg_date else None
    end_date = int(end_date) if end_date else None
    p = Portfolio(symbols=symbols, beg_date=beg_date, end_date=end_date)
    stock_num = p.stock_levels()
    weights = stock_num * [1. / stock_num, ]
    # yr_ret, yr_vol, covar_matrix = p.min_risk_return()
    p.min_risk_return()
    p.stats(weights)
    p.min_func_sharpe(weights)
    opt_mix, ret_risk_sharpe_opt = p.opt_stats()
    ret, risk, sharpe = ret_risk_sharpe_opt
    # takes a while to generate plots, time sleep or js option
    plots = ['static/stock_levels.png', 'static/min_risk_return.png']
    return render_template('plots.html', plots=plots, assets=opt_mix,
                           returns=ret, risk=risk, sharpe=sharpe,
                           symbols=symbols, beg_date=beg_date, end_date=end_date)


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run()

# Starting over
# delete flask_trade.db file and then type
# sqlite3 ~/Desktop/flask_trade/flask_trade.db < schema.sql
# to start the db clean
