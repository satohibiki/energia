from flask import Flask, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from email.policy import default
from sqlalchemy import desc
from datetime import datetime, date


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://satoki:password@localhost:8080/mydatabase'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    height = db.Column(db.Integer, default=170)
    weight = db.Column(db.Integer, default=60)
    total_energia = db.Column(db.Integer, default=0)
    ave_energia = db.Column(db.Integer, default=0)
    last_up_date = db.Column(db.DateTime)
    histories = db.relationship('History', backref='user', lazy=True)
    last_up_date = db.Column(db.DateTime)

class History(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    users_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    energia = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect('/login') # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect('/home')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('このメールアドレスはすでに登録されています')
        return redirect('/signup')

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect('/login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    user = db.session.query(User).filter(User.id==current_user.id).one()
    weight = user.weight
    height = user.height
    ave_energia = user.ave_energia

    return render_template('profile.html', height=height, weight=weight, ave_energia=ave_energia)


@app.route('/profile', methods=["POST"])
def set_profile():
     if request.method == 'POST':
        form_new_weight = request.form.get('weight', type=int)
        form_new_height = request.form.get('height', type=int)
        form_interval = request.form.get('interval', type=int)
        form_goal_weight =request.form.get('goal_weight', type=int)

        user = db.session.query(User).filter(User.id==current_user.id).first()
        if(form_new_height != None and form_new_weight != None):
        #身長，体重更新
            user.height = form_new_height
            user.weight = form_new_weight
        if(form_goal_weight !=None and form_interval != None):
            #目標エネルギア設定
            weight = user.weight

            total_energia = (weight - form_goal_weight) * 7000
            ave_energia = total_energia / (form_interval * 30)

            user.ave_energia = int(ave_energia)

        db.session.commit()

        return redirect('/profile')



#ホーム画面
@app.route('/home')
@login_required
def home():
    users = User.query.order_by(desc(User.total_energia)).limit(10)
    user = db.session.query(User).filter(User.id==current_user.id).first()
    user_his = db.session.query(History).filter(History.users_id==current_user.id and History.date == date.today()).all()
    today_ene = 0

    if user_his != None:
        for his_topic in user_his:
            today_ene += his_topic.energia
    if user.ave_energia != None:
        remain_ene = user.ave_energia - today_ene
    else:
        remain_ene = 0

    if remain_ene <=0:
        msg="おめでとう！"
    else:
        msg="今日の残りエネルギア" + str(remain_ene)

    remain_time = int( remain_ene / (3 * user.weight * 1.05) * 60 )

    return render_template('home.html', users=users, msg=msg, remain_time=remain_time)

@app.route('/home', methods=["POST"])
def addEnergia():
    if request.method == 'POST':
        #フォームから受け取る
        form_mets = request.form.get('mets', type=int)
        form_time = request.form.get('time', type=int) / 60

        user = db.session.query(User).filter(User.id==current_user.id).one()

        form_energia = int(form_mets * form_time * user.weight * 1.05)

        #履歴追加
        history = History(
            users_id = current_user.id,
            energia = form_energia,
            date = datetime.today()
        )
        db.session.add(history)

        #total, 最終更新日時更新
        user = db.session.query(User).filter(User.id==current_user.id).first()
        user.total_energia += form_energia
        user.last_up_date = datetime.today()
        db.session.commit()

        return redirect('/home')


@app.route('/history')
def history():
    topics = db.session.query(History).filter(History.users_id==current_user.id).all()
    total_ene = db.session.query(User).filter(User.id==current_user.id).first().total_energia
    return render_template('history.html', topics=topics, total_ene=total_ene)

if __name__ == '__main__' :
    app.run()