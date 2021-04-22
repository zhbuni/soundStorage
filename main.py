import datetime
import os
from math import ceil

from flask import Flask, render_template, redirect, request, send_file, abort
from flask_jwt_extended import JWTManager
from flask_login import LoginManager, login_user, \
    current_user, login_required, \
    logout_user
from flask_restful import abort, Api
from werkzeug.urls import url_encode
from werkzeug.utils import secure_filename

from data import db_session
from data.comments import Comment

from data.resources.auth import RegisterResource, LoginResource
from data.resources.id_resources import IdsResource
from data.resources.sound_resources import SoundsDownloadResource, SoundsResource, SoundsPostResource
from data.resources.user_resources import UserResource
from data.resources.comment_resources import CommentsListResource, CommentResource
from forms.update_sound_form import UpdateSoundForm

from data.sounds import Sound
from data.tags import Tag
from data.users import User
from forms.comment import CommentForm
from forms.login import LoginForm
from forms.register import RegisterForm
from forms.search import SearchForm
from forms.update_profile_info import UpdateProfileInfoForm
from forms.upload_sound import UploadSoundForm
from data.functions import generate_random_string



app = Flask(__name__)
app.config['SECRET_KEY'] = generate_random_string(15)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)
# jwt ломает нормальную функциональность flask, из за чего он не возвращает ошибку в результате запроса.
# это строка его чинит
app.config['PROPAGATE_EXCEPTIONS'] = True

jwt = JWTManager(app)

# сколько звуков находится на одной странице
SOUNDS_ON_PAGE = 5

api = Api(app)
api.add_resource(IdsResource, '/api/id')
api.add_resource(RegisterResource, '/api/auth/register')
api.add_resource(LoginResource, '/api/auth/login')
api.add_resource(SoundsDownloadResource, '/api/sounds/<string:sound_id>/download')
api.add_resource(SoundsPostResource, '/api/sounds/')
api.add_resource(SoundsResource, '/api/sounds/<string:sound_id>')
api.add_resource(UserResource, '/api/user/<int:user_id>')
api.add_resource(CommentsListResource, '/api/comments')
api.add_resource(CommentResource, '/api/comments/<int:comment_id>')

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/soundStorage.db")
db_sess = db_session.create_session()


# позволяет заменить аргументы из юрл. используется в ссылках на страницы в шаблоне
@app.template_global()
def modify_query(**new_values):
    args = request.args.copy()

    for key, value in new_values.items():
        args[key] = value

    return '{}?{}'.format(request.path, url_encode(args))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def not_found_error(error):
    return render_template('403.html'), 401


@app.errorhandler(401)
def not_found_error(error):
    return render_template('401.html'), 401


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
            filename = secure_filename(file.filename)
            # создаем название файла с новым именем и оригинальным разширением
            filename = generate_random_string(9) + '.' + filename.split('.')[-1]
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


@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    # сперва новые
    sounds = db_sess.query(Sound).order_by(Sound.datetime.desc())

    # получаем фильтр по названию из юрл и фильтруем
    title = request.args.get('title')
    if title:
        sounds = sounds.filter(Sound.name.like('%{}%'.format(title)))

    # всего страниц
    all_pages = ceil(len(sounds.all()) / SOUNDS_ON_PAGE)

    # берем страницу из юрл. если ее нет, значит мы на первой. если страница невалидна, возвращаем 404
    page = request.args.get('page')
    if not page:
        page = '1'
    if page.isdigit() and int(page) > 0:
        sounds = sounds.offset((int(page) - 1) * SOUNDS_ON_PAGE).limit(SOUNDS_ON_PAGE)
    else:
        abort(404)

    # если мы нажали на кнопку поиска, то обрабатываем редирект
    if request.method == 'POST' and form.validate_on_submit():
        if form.select.data == 'title':
            return redirect(f'/?title={form.searchStr.data}')

        elif form.select.data == 'tag':
            sounds = db_sess.query(Sound).join(Tag,
                                               Sound.tags).filter(
                Tag.name.like('%{}%'.format(form.searchStr.data))).all()

    return render_template('index.html', title='Sound Storage', sounds=sounds, form=form, all_pages=all_pages,
                           current_page=int(page))


@app.route('/sound/<int:sound_id>', methods=["GET", "POST"])
@login_required
def detail(sound_id):
    form = CommentForm()
    sound = db_sess.query(Sound).get(sound_id)
    comments = db_sess.query(Comment).filter(Comment.sound_id == sound_id)
    if request.method == 'POST':
        if form.validate_on_submit():
            if current_user.is_authenticated:
                comment = Comment(
                    content=form.content.data,
                    sound_id=sound_id,
                    user_id=current_user.id
                )
            else:
                return redirect('/register')
            db_sess.add(comment)
            db_sess.commit()
            return redirect('/sound/{}'.format(sound_id))
    return render_template('detail.html', sound=sound, comments=comments, form=form, title=sound.name)


@app.route('/upload_sound', methods=['GET', 'POST'])
@login_required
def upload_sound():
    form = UploadSoundForm()

    if form.validate_on_submit():
        # получаем файл
        file = form.file.data
        # получаем айди последней записи, чтобы дать имя новой
        filename = secure_filename(file.filename)
        # создаем название файла с новым именем и оригинальным разширением
        filename = generate_random_string(9) + '.' + filename.split('.')[-1]

        sound = Sound(
            name=form.name.data,
            description=form.description.data,
            filename=filename,
            user=current_user)

        sound.set_tags(form.tags.data, db_sess)

        # сохраняем файл и добавляем запись в бд
        open(os.path.join('static', 'sounds', filename), 'a').close()
        file.save(os.path.join('static', 'sounds', filename))
        db_sess.add(sound)
        db_sess.commit()

        # возвращаем на главную страницу
        return redirect('/')
    return render_template('upload_sound.html', title='Загрузка файла', form=form)


@app.route('/sound/<int:sound_id>/download')
@login_required
def download_sound(sound_id):
    sound = db_sess.query(Sound).get(sound_id)
    if not sound:
        abort(404)
    sound.downloads += 1
    db_sess.commit()
    return send_file(os.path.join(app.root_path, 'static', 'sounds', sound.filename), as_attachment=True)


@app.route('/sound/<int:sound_id>/delete')
@login_required
def delete_sound(sound_id):
    sound = db_sess.query(Sound).get(sound_id)
    if not sound:
        abort(404)
    if sound.author_id == current_user.id:
        os.remove(os.path.join('static', 'sounds', sound.filename))
        db_sess.delete(sound)
        db_sess.commit()
        return redirect('/user/{}'.format(current_user.id))
    abort(403)


@app.route('/sound/<int:sound_id>/update', methods=['POST', 'GET'])
@login_required
def update_sound(sound_id):
    sound = db_sess.query(Sound).get(sound_id)
    if not sound:
        abort(404)
    if sound.author_id != current_user.id:
        abort(403)
    form = UpdateSoundForm()

    if request.method == 'GET':
        form.name.data = sound.name
        form.tags.data = ', '.join([tag.name for tag in sound.tags])
        form.description.data = sound.description
    if form.validate_on_submit():
        sound.name = form.name.data
        sound.set_tags(form.tags.data, db_sess)
        sound.description = form.description.data

        db_sess.commit()
        return redirect('/')

    return render_template('update_sound.html', title='Изменение звука', form=form)


@app.route('/user/<int:user_id>')
def user_page(user_id):
    user = db_sess.query(User).get(user_id)
    if user:
        sounds = db_sess.query(Sound).filter(Sound.author_id == user.id).all()
        return render_template('user_page.html', user=user, sounds=sounds)
    else:
        abort(404)


@app.route('/update_profile_info', methods=['GET', 'POST'])
@login_required
def update_profile_info():
    form = UpdateProfileInfoForm()
    user = db_sess.query(User).get(current_user.id)

    # устанавливаем предустановленные значения текстовым полям
    if request.method == 'GET':
        form.nickname.data = user.nickname
        form.email.data = user.email
        form.profile_description.data = user.profile_description

    if form.validate_on_submit():
        if form.data['submit']:
            if form.email.data != user.email:
                if db_sess.query(User).filter(User.email == form.email.data).first():
                    return render_template('update_profile_info.html', title='Регистрация',
                                           form=form,
                                           message="Эта почта уже зарегестрирована")
            if form.nickname.data != user.nickname:
                if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
                    return render_template('update_profile_info.html', title='Регистрация',
                                           form=form,
                                           message="Такой пользователь уже есть")

            user.nickname = form.nickname.data
            user.email = form.email.data
            user.profile_description = form.profile_description.data

            # пароль изменять необязательно, но если он пришел, то они должны совпадать
            if form.password.data or form.password_again.data:
                if form.password.data != form.password_again.data:
                    return render_template('update_profile_info.html', title='Регистрация',
                                           form=form,
                                           message="Пароли не совпадают")
                user.set_password(form.password.data)

            file = form.file.data
            # если пришел файл, то меняем аватарку
            if file:
                filename = secure_filename(file.filename)
                # создаем название файла с новым именем и оригинальным разширением
                filename = generate_random_string(9) + '.' + filename.split('.')[-1]
                if user.image != 'default-profile-picture.jpg':
                    os.remove(os.path.join('static', 'images', user.image))

                user.image = filename
                file.save(os.path.join('static', 'images', filename))

            db_sess.commit()
            return redirect('/user/' + str(user.id))

        else:
            if user.image != 'default-profile-picture.jpg':
                os.remove(os.path.join('static', 'images', user.image))
                user.image = 'default-profile-picture.jpg'
                db_sess.commit()

    return render_template('update_profile_info.html', form=form)


@app.route('/api/')
def search():
    return render_template('api_docs.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
