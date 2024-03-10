
import requests
from bs4 import BeautifulSoup
import re
import json
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import psycopg2
from textblob import TextBlob
from nltk.probability import FreqDist
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter
import string
from flask import Flask, render_template, request,abort, url_for, redirect, session
from authlib.integrations.flask_client import OAuth
from nltk.tag import pos_tag
from urllib.error import HTTPError

nltk.download('all')


app = Flask(__name__)


oauth = OAuth(app)

app.config['SECRET_KEY'] = "Nikhil"
app.config['GITHUB_CLIENT_ID'] = "853644a43ddd0eb4edb4"
app.config['GITHUB_CLIENT_SECRET'] = "ba41924a1c124c8a3227624797cda79d8358a58c"

github = oauth.register(
    name='github',
    client_id=app.config["GITHUB_CLIENT_ID"],
    client_secret=app.config["GITHUB_CLIENT_SECRET"],
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)



# PostgreSQL Database Configuration.............
DB_HOSTS = 'dpg-cnmngba1hbls739hfl3g-a.oregon-postgres.render.com'
DB_NAME = 'nikhil'
DB_USER = 'nikhil_user'
DB_PASSWORD = 'enT0wQTf9twsljGbeciMprAqKpXny8xi'
DB_HOST = f"{DB_HOSTS}"

ADMIN_PASSWORD = 'Nikhil@sitare'

def connect_to_database():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port="5432"

        )
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)

def get_most_frequent_words(content):
    # Tokenize the content into words
    words = word_tokenize(content)

    # Get punctuation characters
    punctuation_chars = set(string.punctuation)

    # Get English stopwords
    stop_words = set(stopwords.words('english'))

    # Filter out punctuation and stop words
    filtered_words = [word.lower() for word in words if word.isalpha() and word.lower() not in punctuation_chars and word.lower() not in stop_words]

    # Count the occurrences of each word
    word_freq = nltk.FreqDist(filtered_words)

    # Get the 10 most frequent words
    most_frequent_words = word_freq.most_common(10)

    # Calculate the final length of words without counting punctuations
    word_count = sum(1 for word in words if word.isalpha())

    return most_frequent_words, word_count

def newsHindu(s):
    url = s
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    date1 = soup.find(class_="epaper-date")
    date2 = str(date1.get_text())
    try:
        name = soup.find(class_="bulletProj")
        person = str(name.get_text())
    except AttributeError:
            person = "From Source"

    title = soup.find(class_="native_story_title")
    topic = title.get_text()
    article = soup.find(class_="story_details")
    pera = article.find_all('p')
    content = ""
    for i in pera:
        content += " " + i.get_text()

    content = content.strip()

    stop_word = nltk.corpus.stopwords.words("english")
    words = word_tokenize(content)

    freq_10,word_count = get_most_frequent_words(content)

    stop_word_count = 0
    for i in words:
        if i in stop_word:
            stop_word_count+=1

    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', content)
    sentence_count = len(sentences)

    pos_tags = nltk.pos_tag(words, tagset="universal")
    dict1 = {}
    dict1["NOUN"] = 0
    dict1["PRONOUN"] = 0
    dict1["VERB"] = 0
    dict1["ADJECTIVE"] = 0
    dict1["ADVERB"] = 0
    dict1["Other_pos"] = 0

    for ele in pos_tags:
        if ele[1] == 'NOUN':
            dict1['NOUN'] += 1
        elif ele[1] == 'PRON':
            dict1["PRONOUN"] += 1
        elif ele[1] == 'VERB':
            dict1["VERB"] += 1
        elif ele[1] == 'ADJ':
            dict1["ADJECTIVE"] += 1
        elif ele[1] == 'ADV':
            dict1["ADVERB"] += 1
        else:
            dict1["Other_pos"] += 1

    return topic, content, word_count, sentence_count, dict1, date2, person,stop_word_count, freq_10

# Create table news_data in the database if it doesn't already exist
def create_news_data_table():
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news1(
                id SERIAL PRIMARY KEY,
                url VARCHAR(10000),
                headline VARCHAR(5000),
                text VARCHAR(1000000),
                num_sentences VARCHAR(10000),
                num_words VARCHAR(5000),
                pos_tags VARCHAR(1000), publish_date text,
                art_writer text, stop_word_count int, sentiment text,
                Keywords text
            )
        """)
        conn.commit()
        conn.close()
    except psycopg2.Error as e:
        print("Error creating news_data table:", e)

def get_sentiment(text):
    """
    Function to analyze the sentiment of a given text.

    Parameters:
    text (str): The input text for sentiment analysis.

    Returns:
    str: The sentiment label ('positive', 'negative', or 'neutral').
    """
    # Initialize Sentiment Intensity Analyzer
    sia = SentimentIntensityAnalyzer()

    # Analyze sentiment of the text
    sentiment_score = sia.polarity_scores(text)['compound']

    # Determine sentiment label
    if sentiment_score > 0.1:
        return 'positive'
    elif sentiment_score < -0.1:
        return 'negative'
    else:
        return 'neutral'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit_url', methods=['POST'])
def submit_url():
    url = request.form['url']
    if "indianexpress" in url:
        topic, content, word_count, sentence_count, dict1 , date, writer, s_count, freq_10 = newsHindu(url)
    else:
        return abort(406)
    # Extract news text from the URL and clean it
    news_text = extract_news_text(url)
    cleaned_text = clean_text(news_text)

    if cleaned_text:
        # Remove comment lines
        cleaned_text = re.sub(r'(?:(?<=^)|(?<=[^A-Za-z]))COMMents.*?$', '', cleaned_text, flags=re.MULTILINE)

        # Analyze the text
        num_sentences = len(sent_tokenize(cleaned_text))
        pos_tags_count = count_pos_tags(cleaned_text)
        sentiment = get_sentiment(content)
        #pos_tags_dict = {tag: count for tag, count in pos_tags_count.items()}
        pos_dict = json.dumps(dict1)

        # Store data in PostgreSQL database
        try:
            conn = connect_to_database()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO news1(url, headline, text, num_sentences, num_words, pos_tags, publish_date, art_writer, stop_word_count, sentiment, Keywords) VALUES(%s, %s, %s, %s, %s, %s,%s,%s,%s, %s, %s)",
                            (url, topic, cleaned_text, num_sentences, word_count, pos_dict, date, writer, s_count, sentiment, freq_10))
            conn.commit()
            conn.close()
        except:
            pass

        return render_template('analysis.html', url=url, num_sentences=num_sentences, num_words=word_count, pos_tags_count=dict1, content=content, title=topic,date=date,writer=writer, s_count=s_count, sentiment=sentiment, freq_10 = freq_10)
    return "Failed to extract and clean news text from the provided URL."

# Function to extract news text from a URL
def extract_news_text(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract news text from the HTML content
        # For example, you can find and extract paragraphs containing news content
        news_text = ' '.join([p.get_text() for p in soup.find_all('p')])

        return news_text
    except Exception as e:
        print("Error extracting news text:", e)
        return None

# Function to clean text by removing HTML tags and special characters
def clean_text(text):
    # Clean the text (remove HTML tags, special characters, etc.)
    # Return the cleaned text
    # For simplicity, I'm just stripping leading and trailing whitespace
    return text.strip() if text else None

# Function to count POS tags in a text
def count_pos_tags(text):
    tokens = nltk.word_tokenize(text)
    pos_tags = nltk.pos_tag(tokens)
    count = {}
    for _, tag in pos_tags:
        count[tag] = count.get(tag, 0) + 1
    return count

@app.route('/login', methods=['GET','POST'])
def login():
    return render_template('signin.html')

# Endpoint for 'admin'
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password_attempt = request.form.get('password')
        if password_attempt == ADMIN_PASSWORD:
            # Password is correct, fetch the stored table information
            conn = connect_to_database()
            cur = conn.cursor()
            cur.execute("SELECT * FROM news1")
            data = cur.fetchall()
            conn.close()
            return render_template("admin.html", data=data)
        else:
            # Password is incorrect, render password prompt with error message
            return render_template("password.html", error="Incorrect password!")
    else:
        # Render the password prompt
        return render_template("password.html")

# Endpoint for displaying URL content
@app.route('/url_content', methods=['GET'])
def url_content():
    content = request.args.get('content')
    # freq_10 = request.args.get('freq_10')
    return render_template('url_content.html', content=content)


# if __name__ == '__main__':
#     app.run(debug=True)


# Function to fetch data from the database based on URL
def get_data_by_url(url):
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM news1 WHERE url = %s", (url,))
        data = cursor.fetchone()
        conn.close()
        return data
    except psycopg2.Error as e:
        print("Error fetching data from database:", e)
        return None
    

# Github login route
@app.route('/login/github')
def github_login():
    github = oauth.create_client('github')
    redirect_uri = url_for('github_authorize', _external=True)
    return github.authorize_redirect(redirect_uri)

# Github authorize route
@app.route('/login/github/authorize')
def github_authorize():
    github = oauth.create_client('github')
    token = github.authorize_access_token()
    session['github_token'] = token
    resp = github.get('user').json()
    print(f"\n{resp}\n")
    connection = connect_to_database()
    
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM news1")
    data = cursor.fetchall()

    connection.close()

    return render_template('analysis.html', data=data)
    # Redirect to a template or another route after successful authorization

# Logout route for GitHub
@app.route('/logout/github')
def github_logout():
    session.pop('github_token', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)


