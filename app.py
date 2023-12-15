from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import SignUpForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///auth_exercise"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
# db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home_page():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = SignUpForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username/email taken, please pick another')
            return render_template('/register.html', form=form)
        session['username'] = new_user.username
        flash('Welcome! You successfully created your account!', 'success')
        return redirect(f'/users/{new_user.username}')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        if user:
            flash(f'Welcome back, {user.username}!', 'info')
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password']

    return render_template('login.html', form=form)

@app.route('/users/<username>', methods=['GET', 'POST'])
def show_user(username):
    if 'username' not in session:
        flash('Please login', 'danger')
        return redirect('/login')
    user = User.query.filter_by(username=username).first_or_404()
    feedback = Feedback.query.filter_by(username=username)
    return render_template('user.html', user=user, feedback=feedback)

@app.route('/logout')
def logout_user():
    session.pop('username')
    flash('Succesfully logged out', 'info')
    return redirect('/login')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    if 'username' not in session:
        flash('Please login', 'danger')
        return redirect('/login')
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title, content=content, username=session['username'])
        db.session.add(new_feedback)
        db.session.commit()
        flash('New feedback added!', 'success')
        return redirect(f'/users/{username}')
    return render_template('feedback_form.html', form=form)

# POST /users/<username>/delete : Remove the user from the database and make sure to also delete all of their feedback. Clear any user information in the session and redirect to /. Make sure that only the user who is logged in can successfully delete their account.

# **GET */feedback/<feedback-id>/update :*** Display a form to edit feedback — [**](https://curric.springboard.com/software-engineering-career-track/default/exercises/flask-feedback/index.html#id1)Make sure that only the user who has written that feedback can see this form **

# **POST */feedback/<feedback-id>/update :*** Update a specific piece of feedback and redirect to /users/<username> — **Make sure that only the user who has written that feedback can update it.**

# **POST */feedback/<feedback-id>/delete :*** Delete a specific piece of feedback and redirect to /users/<username> — **Make sure that only the user who has written that feedback can delete it.**
    

