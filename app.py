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

@app.route('/logout')
def logout_user():
    session.pop('username')
    flash('Succesfully logged out', 'info')
    return redirect('/login')

@app.route('/users/<username>', methods=['GET', 'POST'])
def show_user(username):
    if 'username' not in session:
        flash('Please login', 'danger')
        return redirect('/login')
    user = User.query.filter_by(username=username).first_or_404()
    feedback = Feedback.query.filter_by(username=username)
    return render_template('user.html', user=user, feedback=feedback)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    if 'username' not in session:
        flash('Please login', 'danger')
        return redirect('/login')

    user = User.query.filter_by(username=username).first_or_404()

    if user.username != session['username']:
        flash('You are not authorized to delete this account', 'danger')
        return redirect(f'/users/{user.username}')

    Feedback.query.filter_by(username=username).delete()

    db.session.delete(user)
    db.session.commit()

    session.clear()
    flash('Your account has been deleted', 'danger')
    return redirect('/')

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

@app.route('/feedback/<feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    if 'username' not in session:
        flash('Please login', 'danger')
        return redirect('/login')
    feedback = Feedback.query.get_or_404(feedback_id)
    form = FeedbackForm()
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        flash('Feedback updated!', 'success')
        return redirect(f'/users/{feedback.username}')
    else:
        form.title.data = feedback.title
        form.content.data = feedback.content
        return render_template('edit_feedback.html', form=form, feedback=feedback)

@app.route('/feedback/<feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    if 'username' not in session:
        flash('Please login', 'danger')
        return redirect('/login')

    feedback = Feedback.query.filter_by(id=feedback_id).first_or_404()

    if feedback.username != session['username']:
        flash('You are not authorized to delete this account', 'danger')
        return redirect(f'/users/{session["username"]}')

    db.session.delete(feedback)
    db.session.commit()

    flash('Your feedback has been deleted', 'danger')
    return redirect(f'/users/{session["username"]}')

    

