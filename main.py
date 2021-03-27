from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from data.sounds import Sound
from data.comments import Comment

from forms.login import LoginForm
from forms.register import RegisterForm
from forms.comment import CommentForm
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
def register():
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
                                   message="Эта почта уже зарегестрирована")
        if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")

        user = User(
            nickname=form.nickname.data,
            profile_description=form.profile_description.data,
            email=form.email.data,
        )

        file = form.file.data
        # если пришел файл, то ставим аватарку. если нет, до дефолтную картинку
        if file:
            last_id = db_sess.query(User).order_by(User.id.desc()).first()
            if not last_id:
                last_id = 0
            else:
                last_id = last_id.id
            filename = secure_filename(file.filename)
            # создаем название файла с новым именем и оригинальным разширением
            filename = str(last_id + 1) + '.' + filename.split('.')[-1]
            user.image = filename
            file.save(os.path.join('static', 'images/', filename))
        else:
            user.image = 'default-profile-picture.jpg'

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
    data = []
    for sound in sounds:
        data.append([sound, db_sess.query(User).get(sound.author_id)])
    return render_template('index.html', title='Sound Storage', data=data)


@app.route('/sound/<int:sound_id>', methods=["GET", "POST"])
def detail(sound_id):
    form = CommentForm()
    sound = db_sess.query(Sound).get(sound_id)
    comments = db_sess.query(Comment).filter(Comment.sound_id == sound_id)
    if request.method == 'POST':
        print(form.validate_on_submit(), form.content)
        if form.validate_on_submit():
            if current_user.is_authenticated:
                comment = Comment(
                    content=form.content.data,
                    sound_id=sound_id,
                    user_id=current_user.id
                )
            else:
                comment = Comment(
                    content=form.content.data,
                    sound_id=sound_id,
                    user_id=None
                )
            db_sess.add(comment)
            db_sess.commit()
            return redirect('/sound/{}'.format(sound_id))
    return render_template('detail.html', sound=sound, comments=comments, form=form)


@app.route('/upload_sound', methods=['GET', 'POST'])
@login_required
def upload_sound():
    form = UploadSoundForm()

    if form.validate_on_submit():
        # получаем файл
        file = form.file.data
        # получаем айди последней записи, чтобы дать имя новой
        last_id = db_sess.query(Sound).order_by(Sound.id.desc()).first()
        if not last_id:
            last_id = 1
        else:
            last_id = last_id.id
        filename = secure_filename(file.filename)
        # создаем название файла с новым именем и оригинальным разширением
        filename = str(last_id + 1) + '.' + filename.split('.')[-1]

        sound = Sound(
            name=form.name.data,
            description=form.description.data,
            filename=filename,
            user=current_user)

        # сохраняем файл и добавляем запись в бд
        file.save(os.path.join('static/sounds/', filename))
        db_sess.add(sound)
        db_sess.commit()

        # возвращаем на главную страницу
        return redirect('/')
    return render_template('upload_sound.html', title='Загрузка файла', form=form)


if __name__ == '__main__':
    app.run()
