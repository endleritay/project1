from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from werkzeug.exceptions import  RequestEntityTooLarge
import os


app = Flask(__name__)
app.secret_key = "2343dr3f4543t4t6gfgy565"

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "1123"
app.config['MYSQL_DB'] = "flask_database"
app.config['UPLOAD_DIRECTORY'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB
app.config['ALLOWED_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', 'gif']


mysql = MySQL(app)
login_manage = LoginManager()
login_manage.init_app(app)
bcrypt = Bcrypt(app)

# User Loader function
@login_manage.user_loader
def load_user(user_id):
    return User.get(user_id)

class User(UserMixin):
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email
    
    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT name,email from users where id = %s', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return User(user_id, result[0], result[1])
        
@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_DIRECTORY'])
    images = []

    for file in files:
        extension = os.path.splitext(file)[1].lower()
        if extension in app.config['ALLOWED_EXTENSIONS']:
            images.append(file)

    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try: 
        file = request.files['file']
        extension = os.path.splitext(file.filename)[1].lower()

        if file:

            if extension not in app.config['ALLOWED_EXTENSIONS']:
                return 'File is not an image.'

            file.save(os.path.join(
                app.config['UPLOAD_DIRECTORY'],
                secure_filename(file.filename)
            ))
    except  RequestEntityTooLarge:
        return 'File is larger than the 16MB limit.'

    return redirect('/')

@app.route('/serve-image/<filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_DIRECTORY'], filename)

@app.route('/photos')
def photos():
    files = os.listdir(app.config['UPLOAD_DIRECTORY'])
    images = []

    for file in files:
        images.append(file)

    return render_template('photos.html', images=images)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id,name,email, password from users where email = %s', (email,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data and bcrypt.check_password_hash(user_data[3], password):
            user = User(user_data[0],user_data[1],user_data[2])
            login_user(user)
            return render_template('main2.html')


    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists in the database
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
            # If the email exists, inform the user
            return render_template('register.html', error="Email already exists. Please login or use a different email.")

        # If email does not exist, hash the password and insert the user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (name,email,password) values(%s,%s,%s)', (name, email, hashed_password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/main2')
@login_required
def main2():
    return render_template('main2.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload_image')
@login_required
def upload_image():
    return render_template('upload.html')



    
if __name__ == '__main__':
    app.run(debug=True)




