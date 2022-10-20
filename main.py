from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import desc
from __init__ import db
from models import User, History

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    user = db.session.query(User).filter(User.id==current_user.id).one()
    weight = user.weight
    height = user.height
    ave_energia = user.ave_energia

    return render_template('profile.html', height=height, weight=weight, ave_energia=ave_energia)


@main.route('/profile', methods=["POST"])
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

        return redirect(url_for('main.profile'))



#ホーム画面
@main.route('/home')
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

@main.route('/home', methods=["POST"])
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

        return redirect(url_for('main.home'))


@main.route('/history')
def history():
    topics = db.session.query(History).filter(History.users_id==current_user.id).all()
    total_ene = db.session.query(User).filter(User.id==current_user.id).first().total_energia
    return render_template('history.html', topics=topics, total_ene=total_ene)
