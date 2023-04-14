import datetime
import os
import werkzeug.utils
from flask import Flask, render_template, redirect, session, make_response, request, abort, jsonify, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from forms.user import RegisterForm, LoginForm
from data.advertisement import Advertisement
from data.users import User
from data.chats import Chat
from data import db_session, advertisement_api, advertisement_resources
from forms.AdvertisementForm import AdvertisementForm
from forms.SearchForm import SearchForm
from forms.ChatForm import ChatForm
from functions import check_password
from tinydb import TinyDB, Query
from livereload import Server

chats = TinyDB('chats_db.json')
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/blogs.db")
    app.register_blueprint(advertisement_api.blueprint)
    # для списка объектов
    api = Api(app)
    api.add_resource(advertisement_resources.AdvertisementListResource, '/api/v2/advertisement')
    # для одного объекта
    api.add_resource(advertisement_resources.AdvertisementResource, '/api/v2/advertisement/<int:advertisement_id>')
    # app.run()
    server = Server(app.wsgi_app)
    server.serve()


@app.route("/", methods=['GET', 'POST'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(f'/search/{form.label.data}')
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        advertisement = db_sess.query(Advertisement).filter(
            (Advertisement.user == current_user) | (Advertisement.is_private != True))
    else:
        advertisement = db_sess.query(Advertisement).filter(Advertisement.is_private != True)
    return render_template("index.html", advertisement=advertisement, url_for=url_for, form=form, search={'title': '',
                                                                                                          'author': ''})


@app.route("/search/<string:searchWord>", methods=['GET', 'POST'])
def search(searchWord):
    form = SearchForm()
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        advertisement = db_sess.query(Advertisement).filter(
            (Advertisement.user == current_user) | (Advertisement.is_private != True))
    else:
        advertisement = db_sess.query(Advertisement).filter(Advertisement.is_private != True)
    text = ''
    if request.method == 'GET':
        text = searchWord
    if form.validate_on_submit():
        print(f'Поиск: {form.label.data}')
        text = form.label.data
    if '%' in text:
        emailIndex = text.index('%') + 1
        emailEndIndex = text[emailIndex:].find(' ') + len(text[:emailIndex])
        if emailEndIndex < len(text[:emailIndex]):
            emailEndIndex = len(text)
        emailAuthor = text[emailIndex:emailEndIndex]
        search = {'title': (' '.join((text[:emailIndex - 1] + text[emailEndIndex:]).split()).lower()),
                  'author': emailAuthor}
    else:
        search = {'title': text.lower(), 'author': ''}
    print('Поиск: ', search)
    return render_template('index.html', form=form, url_for=url_for, search=search, advertisement=advertisement)


@app.route("/confirmation")
def confirmation(id):
    db_sess = db_session.create_session()
    advertisement = db_sess.query(Advertisement).filter(Advertisement.id == id,
                                                        Advertisement.user == current_user
                                                        ).first()
    db_sess.delete(advertisement)
    db_sess.commit()


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if request.method == 'POST':
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        try:
            check_password(form.password.data, form.password_again.data)
        except Exception as error:
            return render_template('register.html', title='Регистрация', form=form,
                                   message=error.__str__())
        user = User()
        file = form.photo.data
        user.name = form.name.data
        user.email = form.email.data
        user.about = form.about.data
        new_user(user)
        print(file)
        if file:
            filename = werkzeug.utils.secure_filename(file.filename)
            path = f'static/users_data/{user.email}/avatar/{filename}'
            file.save(path)
            user.avatar = f'users_data/{user.email}/avatar/{filename}'
        else:
            user.avatar = 'https://bootdey.com/img/Content/user_1.jpg'
        user.set_password(form.password.data)
        new_user(user)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/advertisement', methods=['GET', 'POST'])
@login_required
def add_advertisement():
    form = AdvertisementForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        advertisement = Advertisement()
        advertisement.title = form.title.data
        advertisement.content = form.content.data
        advertisement.is_private = form.is_private.data
        file = form.photo.data
        if file:
            filename = werkzeug.utils.secure_filename(file.filename)
            path = f'static/users_data/{current_user.email}/files/{filename}'
            file.save(path)
            advertisement.file = f'users_data/{current_user.email}/files/{filename}'
        else:
            advertisement.file = 'img/img.png'
        current_user.advertisement.append(advertisement)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('advertisement.html', title='Добавление новости',
                           form=form)


@app.route('/advertisement/<int:advertisement_id>', methods=['GET', 'POST'])
@login_required
def advertisement_page(advertisement_id):
    db_sess = db_session.create_session()
    advertisement = db_sess.query(Advertisement).filter(Advertisement.id == advertisement_id).first()
    if advertisement:
        return render_template('advertisement_page.html', advertisement=advertisement,
                               current_user=current_user,
                               url_for=url_for)
    else:
        return redirect('/')


@app.route('/chat/<int:_id>', methods=['GET', 'POST'])
@login_required
def WrIte_MeSSage(_id):
    form = ChatForm()
    sess = db_session.create_session()
    if _id != 0:
        res = sess.query(Chat).filter((Chat.user_id1 == min(current_user.id, _id)) &
                                      (Chat.user_id2 == max(current_user.id, _id))).first()
        if res:
            chat_id = res.id
        else:
            chat = Chat(user_id1=min(current_user.id, _id),
                        user_id2=max(current_user.id, _id))
            sess.add(chat)
            sess.commit()
            chat_id = chat.id
        other = sess.query(User).filter(User.id == _id).first()
        table = chats.table(str(chat_id))
    else:
        table = chats.table(str(0))
        other = None
    previous = [i.user_id1 if i.user_id1 != current_user.id else i.user_id2 for i
                in sess.query(Chat).filter((Chat.user_id1 == current_user.id) |
                                           (Chat.user_id2 == current_user.id)).all()]
    previous = [sess.query(User).filter(User.id == i).first() for i in previous]
    if request.method == 'POST':
        if form.message.data:
            table.insert({'id': current_user.id, 'text': form.message.data, 'time': datetime.datetime.now()})
        return redirect(f'/chat/{_id}')
    return render_template('chat_room.html', messages=table.all(), cur=current_user,
                           other=other, form=form, previous=previous, id=_id)


@app.route('/advertisement/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_advertisement(id):
    form = AdvertisementForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        advertisement = db_sess.query(Advertisement).filter(Advertisement.id == id,
                                                            Advertisement.user == current_user
                                                            ).first()
        if advertisement:
            form.title.data = advertisement.title
            form.content.data = advertisement.content
            form.is_private.data = advertisement.is_private
            form.photo.data = advertisement.file
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        advertisement = db_sess.query(Advertisement).filter(Advertisement.id == id,
                                                            Advertisement.user == current_user
                                                            ).first()
        if advertisement:
            advertisement.title = form.title.data
            advertisement.content = form.content.data
            advertisement.is_private = form.is_private.data
            file = form.photo.data
            if file:
                filename = werkzeug.utils.secure_filename(file.filename)
                path = f'static/users_data/{current_user.email}/files/{filename}'
                file.save(path)
                advertisement.file = f'users_data/{current_user.email}/files/{filename}'
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('advertisement.html',
                           title='Редактирование новости',
                           form=form)


@app.route('/advertisement_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def advertisement_delete(id):
    db_sess = db_session.create_session()
    advertisement = db_sess.query(Advertisement).filter(Advertisement.id == id,
                                                        Advertisement.user == current_user
                                                        ).first()
    if advertisement:
        db_sess.delete(advertisement)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/settings')
def settings():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    return render_template('settings.html', user=user)


@app.route('/settings/edit', methods=['GET', 'POST'])
def edit_user():
    form = RegisterForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id, ).first()
        if user:
            form.email.data = user.email
            form.name.data = user.name
            form.about.data = user.about
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id, ).first()
        user1 = db_sess.query(User).filter(User.email == form.email.data).first()
        if user1.id != current_user.id:
            return render_template('register.html', title='Редактирование', form=form,
                                   message="Такой пользователь уже есть")
        try:
            check_password(form.password.data, form.password_again.data)
        except Exception as error:
            return render_template('register.html', title='Регистрация', form=form,
                                   message=error.__str__())
        if user:
            user.email = form.email.data
            user.set_password(form.password.data)
            user.name = form.name.data
            user.about = form.about.data
            file = form.photo.data
            print(file)
            if file:
                filename = werkzeug.utils.secure_filename(file.filename)
                path = f'static/users_data/{user.email}/avatar/{filename}'
                file.save(path)
                user.avatar = f'users_data/{user.email}/avatar/{filename}'
            else:
                user.avatar = 'https://bootdey.com/img/Content/user_1.jpg'
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('register.html',
                           title='Редактирование профиля',
                           form=form)


@app.route('/settings/delete', methods=['GET', 'POST'])
def delete_user():
    db_sess = db_session.create_session()
    db_sess.delete(current_user)
    db_sess.commit()
    return redirect('/')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


def new_user(user):
    try:
        os.mkdir('static/users_data/' + user.email)
        os.mkdir('static/users_data/' + user.email + '/files')
        os.mkdir('static/users_data/' + user.email + '/avatar')
    except FileExistsError:
        pass


if __name__ == '__main__':
    main()
