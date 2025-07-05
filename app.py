from flask import Flask, request, redirect, url_for, render_template, session, flash, send_from_directory
import pymysql
import pymysql.cursors
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

upload_image = os.path.join(app.root_path, 'static/profile_image')
app.config['upload_image'] = upload_image


def connect():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'), 
        user=os.environ.get('DB_USER'), 
        password=os.environ.get('DB_PASSWORD'), 
        db=os.environ.get('DB_NAME'), 
        charset='utf8mb4', 
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route("/", methods=['GET', 'POST'])
def login(): 
    if request.method == 'POST':
        user_id = request.form['user_id']
        user_pw = request.form['user_pw']
        
        db = connect()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
        db.close()
        
        if user and check_password_hash(user['user_pw'], user_pw):
            session['user_id'] = user['user_id']
            session['user_name'] = user['user_name']
            return redirect(url_for('home'))
        else:
            flash("아이디 혹은 비밀번호가 틀렸습니다")
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route("/find_id/", methods=['GET', 'POST'])
def find_id(): 
    found_id = None
    if request.method == 'POST':
        user_name = request.form['user_name']
        date_of_birth = request.form['date_of_birth']
        school = request.form['school']
        
        db = connect()
        cursor = db.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_name=%s AND date_of_birth=%s AND school=%s", (user_name, date_of_birth, school))
        user = cursor.fetchone()
        db.close()
        
        if user:
            found_id = user['user_id']
        else:
            flash("가입되신 회원정보가 없습니다")
            return redirect(url_for('find_id'))
    
    return render_template('find_id.html', found_id=found_id)


@app.route("/find_pw/", methods=['GET', 'POST'])
def find_pw(): 
    found_pw = None
    if request.method == 'POST':
        user_name = request.form['user_name']
        date_of_birth = request.form['date_of_birth']
        school = request.form['school']
        user_id = request.form['user_id']
        
        db = connect()
        cursor = db.cursor()
        cursor.execute("SELECT user_pw FROM users WHERE user_name=%s AND date_of_birth=%s AND school=%s AND user_id=%s", (user_name, date_of_birth, school, user_id))
        user = cursor.fetchone()
        db.close()
        
        if user:
            found_pw = user['user_pw']
        else:
            flash("가입되신 회원정보가 없습니다")
            return redirect(url_for('find_pw'))
    
    return render_template('find_pw.html', found_pw=found_pw)


@app.route("/join/", methods=['GET', 'POST'])
def join(): 
    if request.method == 'POST':
        user_name = request.form['user_name']
        date_of_birth = request.form['date_of_birth']
        school = request.form['school']
        user_id = request.form['user_id']
        user_pw = request.form['user_pw']
        hashed_pw = generate_password_hash(user_pw)
        user_pw_re = request.form['user_pw_re']
        if user_pw != user_pw_re:
            return "비밀번호가 일치하지 않습니다"
        
        db = connect()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (user_name, date_of_birth, school, user_id, user_pw) VALUES (%s, %s, %s, %s, %s)", (user_name, date_of_birth, school, user_id, hashed_pw))
        db.commit()
        db.close()
        
        return redirect(url_for('login'))
    
    return render_template('join.html')


@app.route("/home/")
def home(): 
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    search = request.args.get('search', '')
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id))
    user = cursor.fetchone()
    
    if search:
        cursor.execute("SELECT posts.*, users.profile_image FROM posts JOIN users ON posts.user_id = users.user_id WHERE title LIKE %s OR user_name LIKE %s ORDER BY num DESC", ('%' + search + '%', search))
    else:
        cursor.execute("SELECT posts.*, users.profile_image FROM posts JOIN users ON posts.user_id = users.user_id ORDER BY num DESC")
    posts = cursor.fetchall()
    db.close()
    
    return render_template('home.html', posts=posts, search=search, user=user)


@app.route("/read/<int:num>")
def read(num):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE num = %s", (num,))
    post = cursor.fetchone()
    db.close()
    
    if post['post_pw']:
        return redirect(url_for('verify', num=num))
    
    return render_template('read.html', post=post)


@app.route("/write/", methods=['GET', 'POST'])
def write():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        post_pw = request.form['post_pw']
        file = request.files.get('file')
        
        if post_pw:
            hashed_post_pw = generate_password_hash(post_pw)
        else:
            hashed_post_pw = None
        
        file_name = None
        if file and file.filename != '':
            file_name = secure_filename(file.filename)
            file.save(os.path.join('uploads', file_name))
        
        db = connect()
        cursor = db.cursor()
        cursor.execute("INSERT INTO posts (title, content, user_id, user_name, file_name, post_pw) VALUES (%s, %s, %s, %s, %s, %s)", (title, content, user_id, user_name, file_name, hashed_post_pw))
        db.commit()
        db.close()
        return redirect(url_for('home'))
    
    return render_template('write.html')


@app.route("/mypage/")
def mypage():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE user_id = %s ORDER BY num DESC", (user_id,))
    posts = cursor.fetchall()
    db.close()
    
    return render_template('mypage.html', posts=posts)
    
    
@app.route("/delete/<int:num>", methods=['POST'])
def delete(num):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM posts WHERE num = %s", (num,))
    post = cursor.fetchone()
    
    if post and post['user_id'] == user_id:
        cursor.execute("DELETE FROM posts WHERE num = %s", (num,))
        db.commit()
    
    db.close()
    return redirect(url_for('mypage'))


@app.route("/update/<int:num>", methods=['GET', 'POST'])
def update(num):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM posts WHERE num = %s", (num,))
    post = cursor.fetchone()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute("UPDATE posts SET title=%s, content=%s WHERE num=%s", (title, content, num))
        db.commit()
        db.close()
        return redirect(url_for('mypage'))
    
    db.close()
    return render_template('update.html', post=post)
        
        
@app.route("/verify/<int:num>", methods=['GET', 'POST'])
def verify(num):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        post_pw = request.form['post_pw']
    
        db = connect()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM posts WHERE num = %s", (num,))
        post = cursor.fetchone()
        db.close()
    
        if post and check_password_hash(post['post_pw'], post_pw):
            return render_template('read.html', post=post)
        else:
            flash("비밀번호가 틀렸습니다")
            return redirect(url_for('verify', num=num))
    
    return render_template('verify.html', num=num)


@app.route("/uploads/<file_name>")
def download(file_name):
    return send_from_directory('uploads', file_name, as_attachment=True)


@app.route("/profile/", methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    db = connect()
    cursor = db.cursor()
    
    if request.method == 'POST':
        user_name = request.form['user_name']
        date_of_birth = request.form['date_of_birth']
        school = request.form['school']
        profile_image = request.files.get('profile_image')
        
        image_file = None
        if profile_image and profile_image.filename:
            image_file = secure_filename(profile_image.filename)
            profile_image.save(os.path.join(app.config['upload_image'], image_file))
            cursor.execute("UPDATE users SET user_name=%s, date_of_birth=%s, school=%s, profile_image=%s WHERE user_id=%s", (user_name, date_of_birth, school, image_file, user_id))
        else:
            cursor.execute("UPDATE users SET user_name=%s, date_of_birth=%s, school=%s WHERE user_id=%s", (user_name, date_of_birth, school, user_id))
        
        db.commit()
        return redirect(url_for('profile'))
    
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    db.close()
    
    return render_template('profile.html', user=user)


@app.route("/view/<user_id>")
def view(user_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    db.close()
    
    if not user:
        flash("사용자가 존재하지 않습니다")
        return redirect(url_for('home'))
    
    return render_template("view.html", user=user)
    

if __name__ == '__main__':
    app.run(port="5002", debug=True)
