from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'chidiya'
app.config['SECRET_KEY'] = 'your_secret_key'
mysql = MySQL(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username, profile_pic):
        self.id = id
        self.username = username
        self.profile_pic = profile_pic

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username, profile_pic FROM users WHERE id = %s', (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    return User(user_data[0], user_data[1], user_data[2]) if user_data else None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        profile_pics = request.files['profile_pic']
        profile_pic_filename = profile_pics.filename
        
        profile_pics.save(os.path.join('static/profile_pics', profile_pic_filename))
        
        hashed_password = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, profile_pic) VALUES (%s, %s, %s)',
                           (username, hashed_password, profile_pic_filename))
            mysql.connection.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Username already exists.', 'danger')
        finally:
            cursor.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, password, profile_pic FROM users WHERE username = %s', (username,))
        user_data = cursor.fetchone()

        if user_data and check_password_hash(user_data[1], password):
            user = User(user_data[0], username, user_data[2])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

        cursor.close()

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        uploader_id = current_user.id  # Set uploader_id as the current user's ID
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO topics (title, description, uploader_id) VALUES (%s, %s, %s)', 
                       (title, description, uploader_id))
        mysql.connection.commit()
        cursor.close()

        flash('Topic created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_topic.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT topics.id, topics.title, topics.description, users.username, users.id
        FROM topics
        JOIN users ON topics.uploader_id = users.id
    ''')
    topics = cursor.fetchall()

    # Fetch replies for each topic
    topic_data = []
    for topic in topics:
        cursor.execute('SELECT replies.id, replies.content, users.username FROM replies JOIN users ON replies.user_id = users.id WHERE replies.topic_id = %s', (topic[0],))
        replies = cursor.fetchall()
        topic_data.append({
            'topic': topic,
            'replies': replies
        })

    cursor.close()
    return render_template('dashboard.html', topic_data=topic_data)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT username, profile_pic FROM users WHERE id = %s', (user_id,))
    profile_data = cursor.fetchone()
    cursor.close()
    return render_template('profile.html', profile=profile_data)

@app.route('/reply/<int:topic_id>', methods=['POST'])
@login_required
def reply(topic_id):
    content = request.form['reply_content']
    user_id = current_user.id
    
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO replies (content, topic_id, user_id) VALUES (%s, %s, %s)',
                   (content, topic_id, user_id))
    mysql.connection.commit()
    cursor.close()
    
    flash('Reply added successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
