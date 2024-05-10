# hello
from __future__ import unicode_literals
from flask import Flask, render_template, request, redirect, url_for, session
# from flask_mysqldb import MySQL
import mysql.connector
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib
import time
import spacy
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from datetime import date
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
# Import Heapq for Finding the Top N Sentences
from heapq import nlargest

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')
# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'password'
# app.config['MYSQL_DB'] = 'pythonlogin'

connection = mysql.connector.connect(
        host="15.207.107.112",
        user="prad",
        password="password",
        database="pythonlogin",
        auth_plugin='mysql_native_password'
    )

if not connection.is_connected():
    print("We dead!")
    exit(0)

# Intialize MySQL
# mysql = MySQL(app)

def text_summarizer(raw_docx):
    raw_text = raw_docx
    docx = nlp(raw_text)
    stopwords = list(STOP_WORDS)
    # Build Word Frequency # word.text is tokenization in spacy
    word_frequencies = {}  
    for word in docx:  
        if word.text not in stopwords:
            if word.text not in word_frequencies.keys():
                word_frequencies[word.text] = 1
            else:
                word_frequencies[word.text] += 1


    maximum_frequncy = max(word_frequencies.values())

    for word in word_frequencies.keys():  
        word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)
    # Sentence Tokens
    sentence_list = [ sentence for sentence in docx.sents ]

    # Sentence Scores
    sentence_scores = {}  
    for sent in sentence_list:  
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if len(sent.text.split(' ')) < 30:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word.text.lower()]
                    else:
                        sentence_scores[sent] += word_frequencies[word.text.lower()]


    summarized_sentences = nlargest(7, sentence_scores, key=sentence_scores.get)
    final_sentences = [ w.text for w in summarized_sentences ]
    summary = ' '.join(final_sentences)
    return summary

def readingTime(mytext):
    
    total_words = len([ token.text for token in nlp(mytext)])
    estimatedTime = total_words/200.0
    return estimatedTime


@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output a message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        # Check if account exists using MySQL
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('web.html', msg=msg)

@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            cursor.execute('INSERT INTO links VALUES (NULL, %s, %s,%s)', ( "nbc news", "https://www.nbcnews.com",username))
            cursor.execute('INSERT INTO links VALUES (NULL, %s, %s,%s)', ( "Indian express", "https://indianexpress.com",username))
            cursor.execute('INSERT INTO links VALUES (NULL, %s, %s,%s)', ( "hindustan times", "https://www.hindustantimes.com",username))
            connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

@app.route('/pythonlogin/home')
def home():
    # Check if the user is logged in
    if 'loggedin' in session:
        # def process_url():
        #  if request.method == 'POST':
        #     input_url = request.form['input_url']
        #     input_url = request.form['input_url']
        #     raw_text = get_text(input_url)
        #     final_summary = text_summarizer(raw_text)
        #     # User is loggedin show them the home page
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f'SELECT * FROM links WHERE accname = "{session["username"]}";')
        table = '''
        <table style="background: white;">
            <tr>
                <th style="padding: 10px; border: 3px solid black">Link Name</th>
                <th style="padding: 10px; border: 3px solid black">Summarized Text</th>
            </tr>
        '''
        links = cursor.fetchall()
        for linkData in links:
            linkName = linkData[1]
            link = linkData[2]
            raw_text = get_text(link)
            final_summary = text_summarizer(raw_text)
            table += f'''
            <tr><td style="padding: 10px; border: 3px solid black; font-weight: bold;">{linkName}</td><td style="padding: 10px; border: 3px solid black">{final_summary}</td></tr>
            '''
        table += "</table>"
        return render_template('home.html', username=session['username'], table = table)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/pythonlogin/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))

@app.route('/remove', methods = ['GET','POST','DELETE'])
def delete():
   if 'loggedin' in session:
    print(session)
    cur = connection.cursor()
    cur.execute(f"DELETE FROM accounts WHERE id = {session['id']};")
    connection.commit()
    return redirect('/pythonlogin')
   return redirect('/pythonlogin')

@app.route('/pythonlogin/links', methods = ['GET','POST'])
def links():
    msg = ""
    table = ""
    if request.method == 'POST':
        if 'loggedin' in session:
            if "site" in request.form:
                site = request.form['site']
                link = request.form['input_url']
                userid = session["username"]
                # We need all the account info for the user so we can display it on the profile page
                cursor = connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO links (site_name, url, accname) VALUES (%s, %s, %s)', (site, link, userid,))
                connection.commit()
                # Show the profile page with account info
                msg = "<script>alert('Successfully added the link.');</script>"
            else:
                linkid = ""
                for x in request.form:
                    linkid = x
                cur = connection.cursor()
                cur.execute(f"DELETE FROM links WHERE urlid = {linkid};")
                connection.commit()
                msg = "<script>alert('Successfully deleted the link.');</script>"
        # User is not logged in redirect to login page
        else:
            return redirect(url_for('login'))
    # Check if the user is logged in
    else:
        if 'loggedin' not in session:
            # def process_url():
            #  if request.method == 'POST':
            #     input_url = request.form['input_url']
            #     input_url = request.form['input_url']
            #     raw_text = get_text(input_url)
            #     final_summary = text_summarizer(raw_text)
            #     # User is loggedin show them the home page
        # User is not loggedin redirect to login page
            return redirect(url_for('login'))
    if "loggedin" in session:
        cursor = connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f'SELECT * FROM links WHERE accname = "{session["username"]}";')
        table = '''
            <table style="background: white;">
                <tr>
                    <th style="padding: 10px; border: 3px solid black">Link Name</th>
                    <th style="padding: 10px; border: 3px solid black">Link URL</th>
                    <th style="padding: 10px; border: 3px solid black">Action</th>
                </tr>
        '''
        links = cursor.fetchall()
        for linkData in links:
            linkName = linkData[1]
            link = linkData[2]
            table += f'''
                <tr>
                <td style="padding: 10px; border: 3px solid black; font-weight: bold;">
                {linkName}
                </td>
                <td style="padding: 10px; border: 3px solid black">
                {link}
                </td>
                <td style="padding: 10px; border: 3px solid black">
                <form method="POST" action="/pythonlogin/links"><input type="submit" value="Delete" name="{linkData[0]}"></form>
                </td>
                </tr>
                '''
        table += "</table>"
    return render_template('links.html', username=session['username'], msg = msg, table=table)
 
@app.route('/')
def index():
    return render_template('index.html')




def get_text(url):
    req = Request(url,headers={'User-Agent' : "Magic Browser"})
    page = urlopen(req)
    soup = BeautifulSoup(page)
    fetched_text = ' '.join(map(lambda p:p.text,soup.find_all('p')))
    return fetched_text


@app.route('/process',methods=['GET','POST'])
def analyze():
	start = time.time()

	if request.method == 'POST':

		rawtext = request.form['input_text']
		final_reading_time = readingTime(rawtext)
		final_summary = text_summarizer(rawtext)
		summary_reading_time = readingTime(final_summary)
		end = time.time()
		final_time = end-start
	return render_template('result.html',ctext=rawtext,final_summary=final_summary,final_time=final_time,final_reading_time=final_reading_time,summary_reading_time=summary_reading_time)
	

@app.route('/process_url',methods=['GET','POST'])
def process_url():
    start = time.time()
    if request.method == 'POST':
        if 'loggedin' in session:
            site = request.form['site']
            link = request.form['input_url']
            userid = session["id"]
            # We need all the account info for the user so we can display it on the profile page
            cursor = connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO links (site_name, url, accname) VALUES (%s, %s, %s)', (site, link, userid,))
            # Show the profile page with account info
            return redirect(url_for("/pythonlogin/links?success=true"))
        # User is not logged in redirect to login page
        return redirect(url_for('login'))
        # input_url = request.form['input_url']
        # raw_text = get_text(input_url)
        # final_reading_time = readingTime(raw_text)
        # final_summary = text_summarizer(raw_text)
        # summary_reading_time = readingTime(final_summary)
        # end = time.time()
        # final_time = end-start
    # return render_template('result.html',ctext=raw_text,
    #                     final_summary=final_summary,
    #                     final_time=final_time,
    #                     final_reading_time=final_reading_time,
    #                     summary_reading_time=summary_reading_time)