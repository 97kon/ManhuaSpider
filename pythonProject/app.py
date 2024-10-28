from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于会话管理
bcrypt = Bcrypt(app)  # 用于密码加密

# 连接数据库
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="123456",
    database="manhuaDB"
)
cursor = db.cursor()

# 用户注册接口
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # 插入用户到数据库
        sql = "INSERT INTO user (user_name, pwd) VALUES (%s, %s)"
        cursor.execute(sql, (username, hashed_password))
        db.commit()

        return redirect(url_for('login'))
    return render_template('register.html')

# 用户登录接口
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 查询用户
        sql = "SELECT * FROM user WHERE user_name = %s"
        cursor.execute(sql, (username,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[2], password):  # 校验密码
            session['username'] = user[1]  # 在session中存储用户名
            return redirect(url_for('gallery'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

# 查看漫画接口
@app.route('/gallery')
def gallery():
    if 'username' in session:
        sql = "SELECT comic_name, chapter_name, image_name FROM comic_images"
        cursor.execute(sql)
        comics = cursor.fetchall()
        return render_template('gallery.html', comics=comics)
    else:
        return redirect(url_for('login'))

# 漫画图片API，前端通过这个API来加载漫画图片
@app.route('/api/comics')
def get_comics():
    sql = "SELECT comic_name, chapter_name, image_name FROM comic_images"
    cursor.execute(sql)
    comics = cursor.fetchall()
    return jsonify(comics)

# 退出登录
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
