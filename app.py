import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import sqlite3
import api_steam as steam_api

# Configuração do aplicativo
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-do-avaliador-de-jogos'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)

# Configuração do Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Definição das models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reviews = db.relationship('Review', backref='author', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(50), nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route('/')
def index():
    search = request.args.get('search', '')
    games = steam_api.search_games(search) if search else steam_api.get_popular_games()
    return render_template('index.html', games=games, search=search)

@app.route('/game/<appid>')
def game_details(appid):
    game = steam_api.get_game_details(appid)
    reviews = Review.query.filter_by(game_id=appid).order_by(Review.date_posted.desc()).all()
    return render_template('game.html', game=game, reviews=reviews)

@app.route('/review/<appid>', methods=['GET', 'POST'])
@login_required
def review_game(appid):
    game = steam_api.get_game_details(appid)
    if request.method == 'POST':
        content = request.form.get('content')
        rating = int(request.form.get('rating'))
        
        if not content or rating < 1 or rating > 5:
            flash('Por favor, forneça uma análise e uma classificação válida (1-5)', 'danger')
        else:
            review = Review(
                game_id=appid,
                game_name=game['name'],
                content=content,
                rating=rating,
                user_id=current_user.id
            )
            db.session.add(review)
            db.session.commit()
            flash('Sua análise foi publicada com sucesso!', 'success')
            return redirect(url_for('game_details', appid=appid))
    
    return render_template('review.html', game=game)

@app.route('/forum')
def forum():
    reviews = Review.query.order_by(Review.date_posted.desc()).all()
    return render_template('forum.html', reviews=reviews)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não coincidem', 'danger')
            return render_template('auth/register.html')
        
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if user_exists:
            flash('Nome de usuário já existe', 'danger')
        elif email_exists:
            flash('Email já cadastrado', 'danger')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Conta criada com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login falhou. Verifique seu nome de usuário e senha', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 