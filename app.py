import json, sqlite3, click, functools, os, hashlib,time, random, sys
from flask import Flask, current_app, g, session, redirect, render_template, url_for, request




### DATABASE FUNCTIONS ###

def connect_db():
    return sqlite3.connect(app.database)

def init_db():
    """Initializes the database with our great SQL schema"""
    conn = connect_db()
    db = conn.cursor()
    db.executescript("""

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assocUser INTEGER NOT NULL,
    dateWritten DATETIME NOT NULL,
    note TEXT NOT NULL,
    publicID INTEGER NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

INSERT INTO users VALUES(null,"admin", "8f42a3f29ce02a9aefc3bbcc0648a4cfd5c0b47f39f68ac5a52d93de8b8e9e35");
INSERT INTO users VALUES(null,"bernardo", "2b4c6d7f1e094cf8849dcf7499fa10a1d8d8c40edcf57af3a6e84c03213a9968");
INSERT INTO notes VALUES(null,2,"1993-09-23 10:10:10","hello my friend",1234567890);
INSERT INTO notes VALUES(null,2,"1993-09-23 12:10:10","i want lunch pls",1234567891);

""")



### APPLICATION SETUP ###
app = Flask(__name__)
app.database = "db.sqlite3"
app.secret_key = os.urandom(32)
random.seed( hash(app.secret_key) + time.time_ns())

### ADMINISTRATOR'S PANEL ###
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return redirect(url_for('notes'))


@app.route("/notes/", methods=('GET', 'POST'))
@login_required
def notes():
    importerror=""
    #Posting a new note:
    if request.method == 'POST':
        if request.form['submit_button'] == 'add note':
            note = request.form['noteinput']
            db = connect_db()
            c = db.cursor()
            statement = """INSERT INTO notes(id,assocUser,dateWritten,note,publicID) VALUES(null,?,?,?,?);""" 
            print(statement)
            c.execute(statement, (session['userid'],time.strftime('%Y-%m-%d %H:%M:%S'),note,random.randrange(1000000000, 9999999999)))  # pyright: ignore[reportUnusedCallResult]
            db.commit()
            db.close()
        elif request.form['submit_button'] == 'import note':
            noteid = request.form['noteid']
            db = connect_db()
            c = db.cursor()
            statement = """SELECT * from NOTES where publicID = ?""" 
            c.execute(statement, (noteid,))  # pyright: ignore[reportUnusedCallResult]
            result = c.fetchall()
            if(len(result)>0):
                row = result[0]  # pyright: ignore[reportAny]
                statement = """INSERT INTO notes(id,assocUser,dateWritten,note,publicID) VALUES(null,?,?,?,?);""" 
                c.execute(statement, (session['userid'],row[2],row[3],row[4]))  # pyright: ignore[reportUnusedCallResult]
            else:
                importerror="No such note with that ID!"
            db.commit()
            db.close()
    
    db = connect_db()
    c = db.cursor()
    statement = "SELECT * FROM notes WHERE assocUser = ?;"
    print(statement)
    print(session['userid'])  # pyright: ignore[reportAny]
    c.execute(statement, (session['userid'],))  # pyright: ignore[reportUnusedCallResult]
    notes = c.fetchall()
    print(notes)
    
    return render_template('notes.html',notes=notes,importerror=importerror)

@app.route("/skud-ud/", methods=('GET',))
def skudud():
    return render_template('skud-ud.html')

@app.route("/login/", methods=('GET', 'POST'))
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = connect_db()
        c = db.cursor()
        statement = "SELECT * FROM users WHERE username = ? AND password = ?;"
        c.execute(statement, (username, password))
        result = c.fetchall()
        print(result)

        if len(result) > 0:
            session.clear()
            session['logged_in'] = True
            session['userid'] = result[0][0]
            session['username']=result[0][1]
            return redirect(url_for('index'))
        else:
            error = "Wrong username or password!"
    return render_template('login.html',error=error)


@app.route("/register/", methods=('GET', 'POST'))
def register():
    errored = False
    usererror = ""
    passworderror = ""
    if request.method == 'POST':
        

        username = request.form['username']
        password = request.form['password']
        db = connect_db()
        c = db.cursor()
        # pass_statement = """SELECT * FROM users WHERE password = ?;""" 
        user_statement = """SELECT * FROM users WHERE username = ?;"""
        # c.execute(pass_statement, (password))
        # if(len(c.fetchall())>0):
        #     errored = True
        #     passworderror = "That password is already in use by someone else!"

        c.execute(user_statement, (username,))
        if(len(c.fetchall())>0):
            errored = True
            usererror = "That username is already in use by someone else!"

        if(not errored):
            statement = """INSERT INTO users(id,username,password) VALUES(null,?,?);"""
            print(statement)
            c.execute(statement, (username, password))
            db.commit()
            db.close()
            return f"""<html>
                        <head>
                            <meta http-equiv="refresh" content="2;url=/" />
                        </head>
                        <body>
                            <h1>SUCCESS!!! Redirecting in 2 seconds...</h1>
                        </body>
                        </html>
                        """
        
        db.commit()
        db.close()
    return render_template('register.html',usererror=usererror,passworderror=passworderror)


@app.route("/logout/")
@login_required
def logout():
    """Logout: clears the session"""
    session.clear()
    return redirect(url_for('index'))

@app.route("/admin/")
@login_required
def admin():
    """Admin dashboard with SQL statistics"""
    # Check if user is admin
    if session.get('username') != 'admin':
        return redirect(url_for('notes'))
    
    db = connect_db()
    c = db.cursor()
    
    # Get total users
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    # Get total notes
    c.execute("SELECT COUNT(*) FROM notes")
    total_notes = c.fetchone()[0]
    
    # Calculate average notes per user
    if total_users > 0:
        avg_notes_per_user = round(total_notes / total_users, 1)
    else:
        avg_notes_per_user = 0
    
    # Get database file size
    import os
    try:
        db_size_bytes = os.path.getsize(app.database)
        db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
        if db_size_mb < 1:
            db_size = f"{round(db_size_bytes / 1024, 1)} KB"
        else:
            db_size = f"{db_size_mb} MB"
    except:
        db_size = "Unknown"
        db_size_mb = 0
    
    # Get detailed user statistics
    c.execute("""
        SELECT u.id, u.username, COUNT(n.id) as note_count, MAX(n.dateWritten) as latest_note
        FROM users u
        LEFT JOIN notes n ON u.id = n.assocUser
        GROUP BY u.id, u.username
        ORDER BY note_count DESC
    """)
    user_details = []
    for row in c.fetchall():
        user_details.append({
            'id': row[0],
            'username': row[1],
            'note_count': row[2],
            'latest_note': row[3]
        })
    
    # Get recent notes with usernames
    c.execute("""
        SELECT n.id, n.dateWritten, n.note, n.publicID, u.username
        FROM notes n
        JOIN users u ON n.assocUser = u.id
        ORDER BY n.dateWritten DESC
        LIMIT 10
    """)
    recent_notes = []
    for row in c.fetchall():
        recent_notes.append({
            'id': row[0],
            'dateWritten': row[1],
            'note': row[2],
            'publicID': row[3],
            'username': row[4]
        })
    
    db.close()
    
    stats = {
        'total_users': total_users,
        'total_notes': total_notes,
        'avg_notes_per_user': avg_notes_per_user,
        'db_size': db_size,
        'db_size_mb': db_size_mb,
        'user_details': user_details,
        'recent_notes': recent_notes
    }
    
    return render_template('admin.html', stats=stats)

if __name__ == "__main__":
    #create database if it doesn't exist yet
    if not os.path.exists(app.database):  # pyright: ignore[reportAttributeAccessIssue]
        init_db()
    runport = 5000
    if(len(sys.argv)==2):
        runport = sys.argv[1]
    try:
        app.run(host='0.0.0.0', port=runport) # runs on machine ip address to make it visible on netowrk  # pyright: ignore[reportArgumentType]
    except:
        print("Something went wrong. the usage of the server is either")
        print("'python3 app.py' (to start on port 5000)")
        print("or")
        print("'sudo python3 app.py 80' (to run on any other port)")
