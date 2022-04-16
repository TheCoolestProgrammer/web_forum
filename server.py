from flask import Flask, render_template, request

from data import db_session
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired
from flask import redirect
from posting import create_post, create_folders
from draw_post_tree import get_format_posts, delete_data
import os
from flask_login import LoginManager, login_user, logout_user, login_required
from data.posts import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'in_fact_we_are_not_powerless_but_weak-willed__will_will_make_any_choice_right'

app.config['RECAPTCHA_PRIVATE_KEY']='6LdPC3QfAAAAABpgXUnvcK227dFlvuSV6PTEu1Xi'
app.config['RECAPTCHA_PUBLIC_KEY']='6LdPC3QfAAAAAEHbsUF52N5sb8ez2R6PwaILBH7_'

boards = [["разное", "/abu", "/b", "/media", "/r", "/soc"],
          ["тематика", "/au", "/bi", "/biz", "/bo", "/cc"],
          ["творчество", "/de", "/di", "/diy", "/mus", "/p", "/pa"],
          ["политикка", "/hry", "/news", "/po"]]

hidden_posts = dict()
buttons = dict()

filepath = "static/images/uploads/"

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

class bless_form(FlaskForm):
    submit = SubmitField('благославить пост')

class LoginForm(FlaskForm):
    nickname = StringField('ваш никнэйм', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    nickname = StringField('ваш никнэйм', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class Answer_Form(FlaskForm):
    # title = StringField('введите заголовок', validators=[DataRequired()])
    # messenge = StringField('введите ваше сообщение', validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField('запостить')


class Answer_button(FlaskForm):

    submit = SubmitField('ответить')


class Close_button(FlaskForm):
    submit2 = SubmitField('скрыть/открыть ответы')


@app.route("/")
def index():
    # create_folders(boards,filepath)
    return render_template("home.html", boards=boards)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.nickname == form.nickname.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User()
        user.nickname=form.nickname.data
        user.set_password(form.password.data)
        user.verifyed=False
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('registration.html', title='Регистрация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.nickname == form.nickname.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route("/messenge_to/<section>/<int:reply_to_id>", methods=['GET', 'POST'])
def create_messenge(section, reply_to_id):
    form = Answer_Form()

    if form.validate_on_submit():

        # messenge = form.messenge._value()
        messenge = request.form["messenge"]
        title = request.form["title"]
        file = request.files["file_upload"]
        id = len(get_format_posts(section, buttons))
        if file:
            filename = f"{filepath}{section}/picture{id}.{file.filename.split('.')[1]}"
            file.save(filename)
        else:
            filename = ""
            print("aboba")
        # title = form.title._value()

        create_post(section, title, messenge, reply_to_id, hidden_posts, filename)

        # format_posts=get_format_posts(section,buttons)
        # hide_posts(id,id,format_posts)
        return redirect(f'/{section}')
    return render_template("messenge_form.html", form=form, to_id=reply_to_id)


def hide_posts(beggin_beggin_id, begin_id, posts):
    for i in posts:
        if i[1].reply_to_id == begin_id:
            hidden_posts[beggin_beggin_id].append(i[1].id)
            hide_posts(beggin_beggin_id, i[1].id, posts)
    pass


def show_posts(begin_id):
    del (hidden_posts[begin_id])


@app.route("/<db_section>", methods=['GET', 'POST'])
def index2(db_section):
    global buttons,counter

    # if not len(hidden_posts):
    if db_section == 'None':
        # print("flask is stupid shit for dumbasses")
        return ""

    delete_data()
    bless = bless_form()
    if bless.validate_on_submit():
        try:
            index = int(request.form["index2"])
            name = request.form["name"]

            from data import posts
            Posts = getattr(posts, db_section)
            db_sess = db_session.create_session()
            for i in db_sess.query(Posts).filter(Posts.id == index):
                post = i
            if post.blessing != None:
                post.blessing = post.blessing + name
            else:
                post.blessing = name + " "
            db_sess.commit()

        except:
            pass

    format_posts = get_format_posts(db_section, buttons)[::-1]

    i = 0
    post_pos = 0
    zero_pos=[]
    # сортировка постов, чтобы ответы были под постами
    # сначала заголовки
    while i<len(format_posts):
        if format_posts[i][1].reply_to_id == 0:
            if i!=post_pos:
                format_posts.insert(post_pos, format_posts[i])
                del (format_posts[i + 1])
            post_pos=i+1

        i+=1
    # теперь сами посты
    for i in range(len(format_posts)):
        if format_posts[i][1].reply_to_id == 0:
            zero_pos.append(i)
    zero_pos.append(len(format_posts)-1)
    for i in range(len(zero_pos)-1):
        print(format_posts[zero_pos[i]+1:zero_pos[i+1]][::-1])
        format_posts[zero_pos[i]+1:zero_pos[i+1]] =format_posts[zero_pos[i]+1:zero_pos[i+1]][::-1]

    form2 = Close_button()



    if form2.validate_on_submit():
        try:
            index = int(request.form["index"])
            if format_posts[index][1].id not in hidden_posts.keys():
                hidden_posts[format_posts[index][1].id] = []
                format_posts[index] = (format_posts[index][0], format_posts[index][1], 2)
                # hidden_posts.append(format_posts[index][1].id)
                buttons[format_posts[index][1].id] = 2
                hide_posts(format_posts[index][1].id, format_posts[index][1].id, format_posts)
            else:
                format_posts[index] = (format_posts[index][0], format_posts[index][1], 1)
                buttons[format_posts[index][1].id] = 1
                show_posts(format_posts[index][1].id)
        except:
            pass
    return render_template("main.html", format_posts=format_posts, section=db_section, form2=form2,
                           hidden_posts=hidden_posts, bless=bless)

    # print(type(format_posts[index][1]))
    # этот ретерн можно не писать
    # return redirect(f'/messenge_to/{db_section}/{id}')
    # print(format_posts)


def main():
    db_session.global_init("db/borda.db")
    # for self
    #app.run(port=8080, host='127.0.0.1')
    # for internet
    #
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()

