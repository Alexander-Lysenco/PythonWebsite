from flask import Flask, render_template, request, jsonify, escape, redirect
from datetime import datetime
from werkzeug import secure_filename
import sqlite3, math, os, random, string, re
import uuid
import hashlib

# http://flask.pocoo.org/docs/0.10
# http://ru.wikibooks.org/wiki/Flask
app = Flask(__name__)
app.debug = True

@app.errorhandler(404)
def page_not_found(error):
    return redirect('http://proteys.info/404', code=302)

@app.route('/')
@app.route('/index')
def index():
    L = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    t = datetime.now()
    t = t.strftime("%A, %d. %B %Y %H:%M:%S")
    return render_template('index.html', current_time=t, days=L)

@app.route('/sqr', methods=['GET', 'POST'])
def sqr_num():
    title="Квадрат числа"
    if request.method == 'GET':
        return render_template('sqr.html')
    else:
        try:
            x = int(request.form['number'])
        except ValueError:
            return render_template('sqr.html', error="Опаньки! Ошибочка вышла!", title=title)
        x_2 = x ** 2
        return render_template('sqr.html', result=x_2, input=x, title=title)

@app.route('/sqr2', methods=['GET', 'POST'])
def sqr_equation():
    title="Квадратное уравнение"
    if request.method == 'GET':
        return render_template('sqr.html', title=title)
    else:
        try:
            a = int(request.form['a'])
            b = int(request.form['b'])
            c = int(request.form['c'])
            if(a == 0):
                raise ValueError
        except ValueError:
            return render_template('sqr.html', errorcode="Данные должны быть числами, \"a\" должно быть больше нуля!", title=title)
        D = b ** 2 - 4 * a * c
        if(D < 0):
            x1 = str(-b / (2 * a)) +"-"+ str(math.sqrt(abs(D)) / (2 * a))+"i"
            x2 = str(-b / (2 * a)) +"+"+ str(math.sqrt(abs(D)) / (2 * a))+"i"
            return render_template('sqr.html', a=a, b=b, c=c, diskriminant=D, x1=x1, x2=x2, title=title)
        x1 = (-b - math.sqrt(D)) / 2 * a
        x2 = (-b + math.sqrt(D)) / 2 * a
        return render_template('sqr.html', a=a, b=b, c=c, diskriminant=D, x1=x1, x2=x2, title=title)

@app.route('/chat')
def chat():
    title="Наш чат"
    return render_template('chat.html', title=title)

@app.route('/api/messages/list')
def api_messages_list():
    conn = sqlite3.connect('site.db')
    #conn.row_factory = sqlite3.Row
    c = conn.cursor()
    msgs = c.execute('''SELECT username, text, strftime('%d.%m.%Y %H:%M:%S', time) FROM messages ORDER BY id ASC LIMIT 50;''').fetchall()
    msgs = [[escape(x), escape(y), z] for x,y,z in msgs]
    return jsonify(messages=msgs)

@app.route('/api/messages/add', methods=['POST'])
def api_messages_add():
    message = request.get_json()
    conn = sqlite3.connect('site.db')
    c = conn.cursor()
    c.execute('''INSERT INTO messages(text, username, time) VALUES(?, ?, datetime('now'));''', (message['text'], message['user']))
    #c.execute('''INSERT INTO messages(username, text, time) VALUES (message['user'], message['text'], ?)''', datetime.now())
    conn.commit()
    return 'OK'

@app.route('/about')
def about():
    title="Кто мы"
    return render_template('about.html', title=title)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    title="Информация о нас"
    error="Доступ к таблице ограничен администратором"
    if request.method == 'GET':
        return render_template('contact.html', error=error, title=title)
    else:
        try:
            x = int(request.form['pass'])
            if(x == 88005553535):
                return render_template('contact.html', access=1, title=title)
        except ValueError:
            return render_template('contact.html', error="Опаньки! Ошибочка вышла!")
        return render_template('contact.html', error="Пароль не подходит, доступ к данным скрыт.")

@app.route('/linkshorter', methods=['GET', 'POST'])
def linkshorter():
    title="Сокращение ссылок"
    if request.method == 'GET':
        conn = sqlite3.connect('site.db')
        c = conn.cursor()
        urls = c.execute('''SELECT id, url, prefix, strftime('%d.%m.%Y %H:%M:%S', time) FROM linkshorter ORDER BY id DESC LIMIT 20;''').fetchall()
        return render_template('linkshorter.html', urls=urls, title=title)
    else:
        try:
            url = str(request.form['url'])
            result = re.match(r'(ht|f)tp\w*://\w+\.\w+', url)
            if(result==None):
                raise ValueError
        except ValueError:
            return render_template('linkshorter.html', error="Недопустимый формат URL")
        else:
            prefix = random_id()
            link = "http://linjay.pythonanywhere.com/go/"+prefix
            conn = sqlite3.connect('site.db')
            c = conn.cursor()
            c.execute('''INSERT INTO linkshorter (url, prefix, time) VALUES (?, ?, datetime('now'))''', (url, prefix))
            conn.commit()
            urls = c.execute('''SELECT id, url, prefix, strftime('%d.%m.%Y %H:%M:%S', time) FROM linkshorter ORDER BY id DESC LIMIT 20;''').fetchall()
            return render_template('linkshorter.html', link=link, urls=urls, title=title)

def random_id():
    rid = ''
    for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
    return rid

@app.route('/go/<prefix>')
def shortlink(prefix):
    conn = sqlite3.connect('site.db')
    c = conn.cursor()
    destination = c.execute('SELECT url FROM linkshorter WHERE prefix=:pr;', {'pr' : prefix} ).fetchone()
    return redirect(destination[0], code=302)

@app.route('/rm/<prefix>')
def removelink(prefix):
    conn = sqlite3.connect('site.db')
    c = conn.cursor()
    c.execute('DELETE FROM linkshorter WHERE prefix=:pr;', {'pr' : prefix} ).fetchone()
    conn.commit()
    return redirect('/linkshorter')

@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    title="Галерея"
    if request.method == 'GET':
        directory = 'mysite/static/img'
        files = os.listdir(directory)
        return render_template('gallery.html', fileslist = files,title=title)
    else:
        try:
            fs = request.files['image']
            fs.save('mysite/static/img/' + secure_filename(fs.filename))
        except OSError:
            return render_template('gallery.html')
    return redirect('/gallery')

@app.route('/gallery/remove/<filename>')
def remove(filename):
    os.remove('mysite/static/img/' + filename)
    return redirect('/gallery')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message="Неправильный логин или пароль"
    if request.method == 'GET':
        return render_template('login.html')
    else:
        try:
            login=request.form['login']
            password=request.form['password']
            if(login == "" or password == ""):
                raise ValueError
            else: pass
        except ValueError:
            message="Обнаружены пустые поля"
            return render_template('login.html', message=message)
        return render_template('login.html', message=message)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'GET':
        return render_template('registration.html')
    else:
        realname = request.form['realname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm  = request.form['confirm']
        if(realname == "" or username == "" or email == "" or password == "" or confirm == ""):
            return render_template('registration.html', message="Обнаружены пустые поля")
        if password != confirm:
            return render_template('registration.html', message="Пароли не совпадают")

        salt = hashlib.sha512(str(uuid.uuid4()))
        password_hash = hash(salt, password)
        #try:
        #    conn = sqlite3.connect('site.db')
        #    c = conn.cursor()
        #    c.execute('INSERT INTO users(username, password, salt) VALUES(?, ?, ?)', username, password_hash, salt)
        #    conn.commit()
        #except sqlite3.Error as e:
        #    return render_template('registration.html', error = e.args[0])
        return render_template('registration.html', message=[realname, username, email, password_hash])

@app.route('/captcha', methods=['GET', 'POST'])
def captcha():
    a = random.randrange(-99, 99)
    x = random.choice(['+', '-', '*', ':'])
    b = random.randrange(-99, 99)
    if request.method == 'GET':
        return render_template('captcha.html', aa=a, xx=x, bb=b)
    a = int(request.form['a'])
    x = request.form['x']
    b = int(request.form['b'])
    num=None
    try:
        num = int(request.form['number'])
    except ValueError:
        pass
    if(x=='+'): c = a + b
    if(x=='-'): c = a - b
    if(x=='*'): c = a * b
    if(x==':'): c = a / b
    if(c==num):
        return render_template('captcha.html', a=a, x=x, b=b, result=c)
    return redirect('/captcha')


#if __name__ == '__main__':
#    app.run()