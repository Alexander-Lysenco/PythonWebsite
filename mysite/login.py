@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    user = request.form['username']
    passwd = request.form['password']

    conn = sqlite3.connect('site.db')
    c = conn.cursor()
    #msgs = c.execute('''SELECT username, text, strftime('%d.%m.%Y %H:%M:%S', time) FROM messages ORDER BY id ASC LIMIT 50;''').fetchall()

    user_id = c.execute('SELECT username FROM users WHERE idx_users=:id', {'id': user}).fetchone()  # Вытащить из базы
    salt = c.execute('SELECT salt FROM users WHERE idx_users=:id', {'id': user}).fetchone()     # Вытащить из базы
    real_hash = c.execute('SELECT password FROM users WHERE idx_users=:id', {'id': user}).fetchone() # Вытащить из базы

    password_hash = hash(salt, passwd)

    if password_hash != real_hash:
        return redirect(url_for('login'))

    session_key = uuid4()
    # Добавить в базу вместе с user_id

    response = make_response(redirect('/'))
    response.set_cookie('session_key', session_key)

    return response
    #return render_template('login.html')

def get_userid(request):
    try:
        session_key = request.cookies['session_key']
    except KeyError:
        return None

    # По ключу из базы вытаскиваем user_id
def get_username(user_id):
    pass

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'GET':
        return render_template('registration.html')

    conn = sqlite3.connect('site.db')
    c = conn.cursor()
    username = request.form['username']
    password = request.form['password']
    confirm  = request.form['confirm']

    if password != confirm:
        return redirect(url_for('registration'))

    salt = sha512(str(uuid4()))
    password_hash = hash(salt, password)

    try:
        c.execute('INSERT INTO users(username, password, salt) VALUES(?, ?, ?)', username, password_hash, salt)
    except sqlite3.Error as e:
        return render_template('registration.html', error = e.args[0])
    # Записать в базу username, salt, password
    # Если ошибка - редирект
    conn.commit()
    return redirect('/')

#def hash(salt, password):
#    return sha512((salt + password).encode('utf-8'))
