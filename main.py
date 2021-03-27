from flask import Flask, render_template, redirect, request, url_for
from data import db_session
from data.users import User
from data.sounds import Sound
from data.comments import Comment

from forms.login import LoginForm
from forms.register import RegisterForm
from forms.comment import CommentForm

from flask_login import LoginManager, login_user, \
    current_user, login_required, \
    logout_user

import datetime

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


if __name__ == '__main__':
    app.run()
