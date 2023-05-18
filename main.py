from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from sqlalchemy.exc import NoResultFound

##### This is for testing purposes only. Should use environment variable instead.
SECRET_KEY = 'top_secret'

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap(app)

###### Connect to DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

###### Configure DB tables


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Tasks', backref='user')

    def find_user_by_email(self, user_email):
        with app.app_context():
            # Had to catch a NoResultFound exception in order to flash the message in main.py
            # sqlalchemy kept returning a exc.NoResultFound error, regardless of where the IF statement was located
            try:
                user = db.session.execute(db.select(User).filter_by(email=user_email)).scalar_one()
                return user
            except NoResultFound:
                return "Email not found"


class Tasks(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#### Uncomment this if there is no database in the instance folder.
# with app.app_context():
#     db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=["GET"])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('logged_in', user_email=current_user.email))
    return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User().find_user_by_email(email)
        if user == "Email not found":
            flash("This email doesn't exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('logged_in', user_email=current_user.email))
    return render_template('login.html', logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(email=request.form['email']).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        hash_salted_password = generate_password_hash(
            request.form['password'],
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form['email'],
            password=hash_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('logged_in', user_email=current_user.email))
    return render_template('register.html')


@app.route('/<user_email>', methods=["GET", "POST"])
def logged_in(user_email):
    if current_user.is_authenticated:
        all_tasks = Tasks.query.filter_by(user_id=current_user.id).all()
        tasks_active = Tasks.query.filter(Tasks.status, Tasks.user_id == current_user.id).all()
        tasks_completed = Tasks.query.filter(Tasks.status==False, Tasks.user_id == current_user.id).all()
        return render_template('logged.html', user_email=current_user.email, active_tasks=tasks_active,
                               completed_tasks=tasks_completed, all_tasks=all_tasks)
    else:
        return render_template('index.html')


@app.route('/new_task', methods=["GET", "POST"])
def new_task():
    if current_user.is_authenticated:
        if request.method == "POST":
            task = request.form['task']
            if task == "":
                flash("Please add a task!")
                return redirect(url_for('logged_in', user_email=current_user.email))
            else:
                new_tsk = Tasks(
                task=task,
                status=True,
                user_id=current_user.id,
                )
                db.session.add(new_tsk)
                db.session.commit()
                return redirect(url_for('logged_in', user_email=current_user.email))
    else:
        return redirect(url_for('home'))


@app.route('/check_task/<id>/', methods=["GET", "POST"])
def check_task(id):
    task_to_check = Tasks.query.filter_by(id=id, user_id=current_user.id).first()
    if task_to_check.status:
        task_to_check.status = False
    else:
        task_to_check.status = True
    db.session.commit()
    redirect(url_for('logged_in', user_email=current_user.email))
    return jsonify({'message': 'Task status updated'})


@app.route('/delete/<id>/', methods=["GET", "POST"])
def delete_task(id):
    task_to_delete = Tasks.query.filter_by(id=id, user_id=current_user.id).first()
    if task_to_delete:
        Tasks.query.filter_by(id=id, user_id=current_user.id).delete()
        db.session.commit()
        return redirect(url_for('logged_in', user_email=current_user.email))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
