from flask import Flask, render_template, redirect
from data import db_session
from data.users import User
from data.sounds import Sound

from forms.login import LoginForm
from forms.register import RegisterForm
from forms.upload_sound import UploadSoundForm

from flask_login import LoginManager, login_user, \
    current_user, login_required, \
    logout_user

from werkzeug.utils import secure_filename

import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'need_to_change_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)
login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/soundStorage.db")
db_sess = db_session.create_session()


@login_manager.user_loader
def load_user(user_id):
    return db_sess.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    if current_user.is_authenticated:
        return redirect('/')
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            age=form.age.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/')
def index():
    sounds = db_sess.query(Sound).all()
    return render_template('index.html', title='Sound Storage', sounds=sounds)


@app.route('/upload_sound', methods=['GET', 'POST'])
@login_required
def upload_sound():
    form = UploadSoundForm()

    if form.validate_on_submit():
        # получаем файл
        file = form.file.data
        # получаем айди последней записи, чтобы дать имя новой
        last_id = db_sess.query(Sound).order_by(Sound.id.desc()).first().id
        filename = secure_filename(file.filename)
        # создаем название файла с новым именем и оригинальным разширением
        filename = str(last_id + 1) + '.' + filename.split('.')[-1]

        sound = Sound()
        # собираем данные с формы
        sound.name = form.name.data
        sound.description = form.description.data
        sound.filename = filename

        # сохраняем файл и добавляем запись в бд
        file.save(os.path.join('static/sounds/', filename))
        db_sess.add(sound)
        db_sess.commit()

        # возвращаем на главную страницу
        return redirect('/')
    return render_template('upload_sound.html', title='Загрузка файла', form=form)


if __name__ == '__main__':
    app.run()
