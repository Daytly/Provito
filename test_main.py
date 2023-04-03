import os
import sys

import werkzeug.utils
from flask import Flask, render_template, redirect, session, make_response, request, abort, jsonify, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import Api
from forms.user import RegisterForm, LoginForm
from data.news import News
from data.users import User
from data import db_session, news_api, news_resources
from forms.NewsForm import NewsForm
from forms.SearchForm import SearchForm

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    # для списка объектов
    api = Api(app)
    api.add_resource(news_resources.NewsListResource, '/api/v2/news')
    # для одного объекта
    api.add_resource(news_resources.NewsResource, '/api/v2/news/<int:news_id>')
    app.run()


@app.route("/", methods=['GET', 'POST'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        return redirect(f'/search/{form.label.data}')
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private!=True))
    else:
        news = db_sess.query(News).filter(News.is_private!=True)
    return render_template("index.html", news=news, url_for=url_for, form=form, search='')


@app.route("/search/<string:searchWord>", methods=['GET', 'POST'])
def search(searchWord):
    form = SearchForm()
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private!=True))
    else:
        news = db_sess.query(News).filter(News.is_private!=True)
    if request.method == 'GET':
        print(f'Поиск: {searchWord}')
        return render_template('index.html', form=form, url_for=url_for, search=searchWord, news=news)
    if form.validate_on_submit():
        print(f'Поиск: {form.label.data}')
        return render_template('index.html', form=form, url_for=url_for,  search=form.label.data, news=news)
    return render_template('index.html', form=form, url_for=url_for,  search='', news=news)


@app.route("/confirmation")
def confirmation(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    db_sess.delete(news)
    db_sess.commit()


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
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


@app.route('/news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        file = form.photo.data
        if file:
            filename = werkzeug.utils.secure_filename(file.filename)
            path = f'static/users_data/{current_user.email}/files/{filename}'
            file.save(path)
            news.file = f'users_data/{current_user.email}/files/{filename}'
        else:
            news.file = 'img/img.png'
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/chat/<int:id>', methods=['GET', 'POST'])
@login_required
def WrIte_MeSSage(id):
    return jsonify(['wellcome'])

@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
            form.photo.data = news.file
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            file = form.photo.data
            if file:
                filename = werkzeug.utils.secure_filename(file.filename)
                path = f'static/users_data/{current_user.email}/files/{filename}'
                file.save(path)
                news.file = f'users_data/{current_user.email}/files/{filename}'
            else:
                news.file = 'img/img.png'
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
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
        user = db_sess.query(User).filter(User.id == current_user.id,).first()
        if user:
            form.email.data = user.email
            form.name.data = user.name
            form.about.data = user.about
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id,).first()
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        user1 = db_sess.query(User).filter(User.email == form.email.data).first()
        if user1.id != current_user.id:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        if user:
            user.email = form.email.data
            user.set_password(form.password.data)
            user.name = form.name.data
            user.about = form.about.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('register.html',
                           title='Редактирование профиля',
                           form=form)


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
    except FileExistsError:
        pass


if __name__ == '__main__':
    main()
