"""
Avaliador de Jogos da Steam

Aplicação Flask que permite aos usuários visualizar e avaliar jogos da Steam,
bem como interagir por meio de um fórum de avaliações.
"""

import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import sqlite3
import api_steam as steam_api
from werkzeug.utils import secure_filename
from pytz import UTC
from urllib.parse import urlparse

# Configuração do aplicativo
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-do-avaliador-de-jogos'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do diretório de uploads usando caminho absoluto
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Garante que o diretório de uploads existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        print(f"Diretório de uploads criado em: {app.config['UPLOAD_FOLDER']}")
    except Exception as e:
        print(f"Erro ao criar diretório de uploads: {str(e)}")

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)

# Configuração do Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Definição das models
class User(db.Model, UserMixin):
    """
    Modelo de usuário do sistema.
    Contém informações de autenticação e relacionamento com avaliações.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    avatar_url = db.Column(db.String(200), default='static/uploads/default.png')
    bio = db.Column(db.Text)
    favorite_games = db.Column(db.String(500))  # Armazenará IDs dos jogos favoritos separados por vírgula
    reviews = db.relationship('Review', backref='author', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    communities = db.relationship('CommunityMember', backref='user', lazy=True)
    review_responses = db.relationship('ReviewResponse', backref='author', lazy=True)

    def set_password(self, password):
        """Gera o hash da senha e armazena no objeto."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)

class Review(db.Model):
    """
    Modelo de avaliação de jogos.
    Relaciona-se a um jogo específico e a um usuário autor.
    """
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(50), nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    responses = db.relationship('ReviewResponse', backref='review', lazy=True)
    votes = db.relationship('ReviewVote', backref='review', lazy=True)

class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    game_id = db.Column(db.String(50), nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    game_img = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    posts = db.relationship('Post', backref='community', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('CommunityMember', backref='community', lazy=True, cascade='all, delete-orphan')
    invitations = db.relationship('CommunityInvitation', backref='community', lazy=True, cascade='all, delete-orphan')

class CommunityMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(200))
    media_type = db.Column(db.String(10))  # 'image' ou 'video'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class CommunityInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected

class ReviewResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # friend_request, community_invite, review_response, post_response
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    reference_id = db.Column(db.Integer)  # ID do item relacionado (review, post, etc)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReviewVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'like' ou 'dislike'
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id', name='_user_review_uc'),)

class ReviewResponseVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    response_id = db.Column(db.Integer, db.ForeignKey('review_response.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'like' ou 'dislike'
    __table_args__ = (db.UniqueConstraint('user_id', 'response_id', name='_user_response_uc'),)

@login_manager.user_loader
def load_user(user_id):
    """
    Callback para carregar o usuário atual com base no ID armazenado na sessão.
    """
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """
    Página inicial da aplicação.
    Mostra os jogos populares ou resultados de uma pesquisa.
    """
    search = request.args.get('search', '')
    games = steam_api.search_games(search) if search else steam_api.get_popular_games()
    return render_template('index.html', games=games, search=search)

@app.route('/game/<appid>')
def game_details(appid):
    """
    Página de detalhes de um jogo específico.
    Exibe informações do jogo e avaliações dos usuários.
    """
    game = steam_api.get_game_details(appid)
    
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'recent') # Adiciona suporte para ordenação

    query = Review.query.filter_by(game_id=appid)

    # Aplica a ordenação
    if sort_by == 'popular':
        query = query.order_by(Review.likes.desc(), Review.date_posted.desc())
    else: # 'recent' (padrão)
        query = query.order_by(Review.date_posted.desc())

    reviews = query.paginate(page=page, per_page=10) # Pagina as avaliações

    community = Community.query.filter_by(game_id=appid).first()
    return render_template('game.html', game=game, reviews=reviews, community=community, sort_by=sort_by) # Passa sort_by também

@app.route('/review/<appid>', methods=['GET', 'POST'])
@login_required
def review_game(appid):
    """
    Permite ao usuário logado escrever uma nova avaliação para um jogo.
    """
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
    """
    Página do fórum que lista todas as avaliações publicadas.
    """
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'recent') # Padrão: mais recentes
    filter_by = request.args.get('filter') # Novo parâmetro de filtro

    query = Review.query

    # Aplica o filtro por amigos, se solicitado e usuário autenticado
    if filter_by == 'friends' and current_user.is_authenticated:
        # Busca os IDs dos amigos do usuário logado
        friendships = Friendship.query.filter(
            ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)) &
            (Friendship.status == 'accepted')
        ).all()

        friend_ids = []
        for friendship in friendships:
            if friendship.user_id == current_user.id:
                friend_ids.append(friendship.friend_id)
            else:
                friend_ids.append(friendship.user_id)

        # Inclui o próprio usuário nas avaliações de amigos (opcional, mas comum em timelines)
        # friend_ids.append(current_user.id)

        # Filtra as avaliações pelos IDs dos amigos
        if friend_ids:
            query = query.filter(Review.user_id.in_(friend_ids))
        else:
            # Se não houver amigos, retorna uma lista vazia de avaliações
            # reviews = Review.query.filter(Review.user_id == None).paginate(page=page, per_page=10) # Query que retorna vazio
            # Uma alternativa mais limpa é retornar uma paginação vazia se não houver amigos.
            reviews = Review.query.filter(Review.id == None).paginate(page=page, per_page=10) # Garante query vazia

            # Adiciona as imagens dos jogos às avaliações (para a lista vazia, não fará nada)
            for review in reviews.items:
                game = steam_api.get_game_details(review.game_id)
                if game:
                    review.game_img = game.get('img_url', '')
            print(f"DEBUG: Tipo de reviews antes de renderizar forum.html (filtro amigos, sem amigos): {type(reviews)}") # Log de depuração
            return render_template('forum.html', reviews=reviews, sort_by=sort_by, filter_by=filter_by, steam_api=steam_api)

    # Aplica a ordenação
    if sort_by == 'popular':
        query = query.order_by(Review.likes.desc(), Review.date_posted.desc())
    else: # 'recent'
        query = query.order_by(Review.date_posted.desc())

    reviews = query.paginate(page=page, per_page=10)
    
    # Adiciona as imagens dos jogos e o status do voto do usuário às avaliações
    for review in reviews.items:
        game = steam_api.get_game_details(review.game_id)
        if game:
            review.game_img = game.get('img_url', '')
        
        # Busca o voto do usuário logado para esta review
        user_vote = None
        if current_user.is_authenticated:
            vote = ReviewVote.query.filter_by(user_id=current_user.id, review_id=review.id).first()
            if vote:
                user_vote = vote.type # 'like' ou 'dislike'
        review.user_vote = user_vote # Adiciona o status do voto ao objeto review

    # --- Busca de dados para o Hall da Fama ---
    # Usuário com mais avaliações
    user_most_reviews_data = db.session.query(User, db.func.count(Review.id).label('review_count'))\
        .join(Review)\
        .group_by(User)\
        .order_by(db.desc('review_count'))\
        .first()
    user_most_reviews = user_most_reviews_data[0] if user_most_reviews_data else None
    user_most_reviews_count = user_most_reviews_data[1] if user_most_reviews_data else 0

    # Comunidade com mais membros
    community_most_members_data = db.session.query(Community, db.func.count(CommunityMember.id).label('member_count'))\
        .outerjoin(CommunityMember)\
        .group_by(Community)\
        .order_by(db.desc('member_count'))\
        .first()
    community_most_members = community_most_members_data[0] if community_most_members_data else None
    community_most_members_count = community_most_members_data[1] if community_most_members_data else 0

    # Comunidade mais ativa (com mais posts)
    community_most_active_data = db.session.query(Community, db.func.count(Post.id).label('post_count'))\
        .outerjoin(Post)\
        .group_by(Community)\
        .order_by(db.desc('post_count'))\
        .first()
    community_most_active = community_most_active_data[0] if community_most_active_data else None
    community_most_active_count = community_most_active_data[1] if community_most_active_data else 0

    # Jogo com mais avaliações
    game_most_reviews_data = db.session.query(Review.game_id, Review.game_name, db.func.count(Review.id).label('review_count'))\
        .group_by(Review.game_id, Review.game_name)\
        .order_by(db.desc('review_count'))\
        .first()
    game_most_reviews_game_id = game_most_reviews_data[0] if game_most_reviews_data else None
    game_most_reviews_name = game_most_reviews_data[1] if game_most_reviews_data else None
    game_most_reviews_count = game_most_reviews_data[2] if game_most_reviews_data else 0
    # --- Fim da busca de dados para o Hall da Fama ---

    print(f"DEBUG: Tipo de reviews antes de renderizar forum.html: {type(reviews)}") # Log de depuração
    
    return render_template('forum.html', reviews=reviews, sort_by=sort_by, filter_by=filter_by, steam_api=steam_api,
                           user_most_reviews=user_most_reviews,
                           user_most_reviews_count=user_most_reviews_count,
                           community_most_members=community_most_members,
                           community_most_members_count=community_most_members_count,
                           community_most_active=community_most_active,
                           community_most_active_count=community_most_active_count,
                           game_most_reviews_game_id=game_most_reviews_game_id,
                           game_most_reviews_name=game_most_reviews_name,
                           game_most_reviews_count=game_most_reviews_count)

@app.route('/communities')
def communities():
    search = request.args.get('search', '')
    game_id = request.args.get('game_id')
    sort_by = request.args.get('sort', 'popular') # Padrão: mais populares

    query = db.session.query(Community, db.func.count(CommunityMember.id).label('members_count')) \
        .outerjoin(CommunityMember) \
        .group_by(Community)

    if search:
        query = query.filter(Community.game_name.ilike(f'%{search}%'))
    elif game_id:
        query = query.filter(Community.game_id == game_id)

    # Aplica a ordenação com base no parâmetro sort_by
    if sort_by == 'recent':
        query = query.order_by(db.desc(Community.created_at))
    else: # 'popular' (padrão)
        query = query.order_by(db.desc('members_count'))

    communities_with_counts = query.all()

    # Extrai apenas os objetos Community e adiciona a contagem como atributo
    communities = []
    for community, member_count in communities_with_counts:
        community.member_count = member_count
        
        # Verifica se o usuário logado é membro desta comunidade
        is_member = False
        if current_user.is_authenticated:
            is_member = CommunityMember.query.filter_by(
                user_id=current_user.id,
                community_id=community.id
            ).first() is not None
        community.is_member = is_member # Adiciona a informação ao objeto community

        communities.append(community)

    # Adiciona logs de depuração para verificar a ordenação e status de membro
    print(f"DEBUG: Comunidades ordenadas por {sort_by} com status de membro:")
    for comm in communities:
        print(f" - {comm.name} (Membros: {getattr(comm, 'member_count', 'N/A')}, Criada: {comm.created_at}, Membro: {getattr(comm, 'is_member', 'N/A')})")

    return render_template('communities.html', 
                           communities=communities,
                           search=search,
                           selected_game_id=game_id,
                           sort_by=sort_by) # Passa sort_by para o template

@app.route('/community/<int:community_id>/members')
def community_members(community_id):
    community = Community.query.get_or_404(community_id)
    members = db.session.query(User).join(CommunityMember).filter(CommunityMember.community_id == community_id).all()
    
    # Para cada membro, verificar se já são amigos do usuário logado
    if current_user.is_authenticated:
        for member in members:
            if member.id != current_user.id:
                friendship = Friendship.query.filter(
                    ((Friendship.user_id == current_user.id) & (Friendship.friend_id == member.id)) |
                    ((Friendship.user_id == member.id) & (Friendship.friend_id == current_user.id))
                ).first()
                member.is_friend = friendship and friendship.status == 'accepted'
                member.friendship_pending = friendship and friendship.status == 'pending'
            else:
                member.is_friend = False
                member.friendship_pending = False
    else:
         for member in members:
             member.is_friend = False
             member.friendship_pending = False


    return render_template('community_members.html', community=community, members=members)

@app.route('/community/<int:community_id>')
def community_details(community_id):
    community = Community.query.get_or_404(community_id)
    
    # Conta o número de membros da comunidade
    member_count = db.session.query(CommunityMember).filter_by(community_id=community_id).count()

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'recent') # Padrão: mais recentes
    
    query = Post.query.filter_by(community_id=community_id)
    
    if sort_by == 'popular':
        query = query.order_by(Post.likes.desc(), Post.created_at.desc())
    else: # 'recent'
        query = query.order_by(Post.created_at.desc())
        
    posts = query.paginate(page=page, per_page=10) # Paginação

    is_member = False
    if current_user.is_authenticated:
        is_member = CommunityMember.query.filter_by(
            user_id=current_user.id,
            community_id=community_id
        ).first() is not None
        
    return render_template('community_details.html', 
                           community=community, 
                           posts=posts, 
                           is_member=is_member,
                           member_count=member_count, # Passa a contagem de membros para o template
                           sort_by=sort_by)

@app.route('/community/<int:community_id>/join', methods=['POST'])
@login_required
def join_community(community_id):
    if not CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first():
        member = CommunityMember(user_id=current_user.id, community_id=community_id)
        db.session.add(member)
        db.session.commit()
        flash('Você agora é membro desta comunidade!', 'success')
    return redirect(url_for('community_details', community_id=community_id))

@app.route('/community/<int:community_id>/delete', methods=['POST'])
@login_required
def delete_community(community_id):
    community = Community.query.get_or_404(community_id)

    # Verifica se o usuário logado é o criador da comunidade
    if community.creator_id != current_user.id:
        flash('Você não tem permissão para apagar esta comunidade.', 'danger')
        return redirect(url_for('community_details', community_id=community.id))

    try:
        db.session.delete(community)
        db.session.commit()
        flash('Comunidade apagada com sucesso!', 'success')
        return redirect(url_for('communities')) # Redireciona para a página geral de comunidades
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao apagar a comunidade: {e}', 'danger')
        return redirect(url_for('community_details', community_id=community.id))

@app.route('/community/<int:community_id>/leave', methods=['POST'])
@login_required
def leave_community(community_id):
    # Verifica se o usuário não é o criador antes de permitir sair
    community = Community.query.get_or_404(community_id)
    if community.creator_id == current_user.id:
        flash('O criador não pode sair da própria comunidade. Considere apagá-la.', 'warning')
        return redirect(url_for('community_details', community_id=community_id))

    member = CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first()

    if member:
        try:
            db.session.delete(member)
            db.session.commit()
            flash('Você saiu da comunidade.', 'info')
            return redirect(url_for('community_details', community_id=community_id)) # Redireciona de volta para a página da comunidade
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao sair da comunidade: {e}', 'danger')
            return redirect(url_for('community_details', community_id=community_id))
    else:
        flash('Você não é membro desta comunidade.', 'warning')
        return redirect(url_for('community_details', community_id=community_id))

@app.route('/community/<int:community_id>/post', methods=['POST'])
@login_required
def create_post(community_id):
    # Verifica se o usuário é membro da comunidade
    if not CommunityMember.query.filter_by(user_id=current_user.id, community_id=community_id).first():
        flash('Você precisa ser membro da comunidade para postar.', 'danger')
        return redirect(url_for('community_details', community_id=community_id))

    content = request.form.get('content')
    media = request.files.get('media')
    
    media_url = None
    media_type = None

    if media and media.filename:
        print(f"Tentando fazer upload do arquivo: {media.filename}")
        # Verifica a extensão do arquivo
        filename = secure_filename(media.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
            media_type = 'image'
        elif file_ext in ['mp4', 'webm']:
            media_type = 'video'
        else:
            flash('Formato de arquivo não suportado. Use imagens (jpg, jpeg, png, gif) ou vídeos (mp4, webm).', 'danger')
            return redirect(url_for('community_details', community_id=community_id))
        
        # Gera um nome único para o arquivo
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        # Salva o arquivo
        try:
            media_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            print(f"Tentando salvar arquivo em: {media_path}")
            print(f"Diretório de upload existe? {os.path.exists(app.config['UPLOAD_FOLDER'])}")
            print(f"Permissões do diretório: {oct(os.stat(app.config['UPLOAD_FOLDER']).st_mode)[-3:]}")
            
            media.save(media_path)
            media_url = f'uploads/{unique_filename}'
            print(f"Arquivo salvo com sucesso em: {media_path}")
            print(f"URL da mídia: {media_url}")
        except Exception as e:
            print(f"Erro ao salvar arquivo: {str(e)}")
            print(f"Tipo do erro: {type(e)}")
            flash('Erro ao salvar o arquivo de mídia. Por favor, tente novamente.', 'danger')
            return redirect(url_for('community_details', community_id=community_id))

    elif not content:
        flash('O post não pode estar vazio.', 'danger')
        return redirect(url_for('community_details', community_id=community_id))

    # Cria o post
    try:
        post = Post(
            content=content,
            media_url=media_url,
            media_type=media_type,
            user_id=current_user.id,
            community_id=community_id
        )
        
        db.session.add(post)
        db.session.commit()
        flash('Postagem criada com sucesso!', 'success')
    except Exception as e:
        print(f"Erro ao criar post: {str(e)}")
        db.session.rollback()
        flash('Erro ao criar a postagem. Por favor, tente novamente.', 'danger')
        return redirect(url_for('community_details', community_id=community_id))

    return redirect(url_for('community_details', community_id=community_id))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    # Verifica se o usuário é membro da comunidade
    if not CommunityMember.query.filter_by(user_id=current_user.id, community_id=post.community_id).first():
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Você precisa ser membro da comunidade para comentar.'}), 403
        flash('Você precisa ser membro da comunidade para comentar.', 'danger')
        return redirect(url_for('community_details', community_id=post.community_id))
    content = request.form.get('comment') or (request.json and request.json.get('comment'))
    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id
    )
    db.session.add(comment)
    db.session.commit()
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Comentário adicionado com sucesso!'}), 200
    flash('Comentário adicionado com sucesso!', 'success')
    return redirect(url_for('community_details', community_id=post.community_id))

@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return redirect(url_for('community_details', community_id=post.community_id))

@app.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    # Verifica se o usuário logado é o autor da avaliação
    if review.user_id != current_user.id:
        flash('Você não tem permissão para apagar esta avaliação.', 'danger')
        return redirect(url_for('forum')) # ou para a página do jogo, dependendo de onde foi clicado

    db.session.delete(review)
    db.session.commit()
    flash('Avaliação apagada com sucesso.', 'success')
    return redirect(url_for('forum'))

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    community = Community.query.get_or_404(post.community_id)
    # Verifica se o usuário é o autor do post ou o criador da comunidade
    if post.user_id != current_user.id and community.creator_id != current_user.id:
        flash('Você não tem permissão para apagar esta postagem.', 'danger')
        return redirect(url_for('community_details', community_id=community.id))
    
    db.session.delete(post)
    db.session.commit()
    flash('Postagem apagada com sucesso!', 'success')
    return redirect(url_for('community_details', community_id=community.id))

@app.route('/response/<int:response_id>/delete', methods=['POST'])
@login_required
def delete_response(response_id):
    print(f"Tentativa de apagar resposta {response_id} pelo usuário {current_user.username}")
    response = ReviewResponse.query.get_or_404(response_id)
    # Verifica se o usuário logado é o autor da resposta
    if response.user_id != current_user.id:
        print(f"Usuário {current_user.username} não é o autor da resposta {response_id}.")
        flash('Você não tem permissão para apagar esta resposta.', 'danger')
        # Redireciona de volta para a página do jogo da avaliação associada
        review = Review.query.get(response.review_id)
        if review:
            print(f"Redirecionando para game_details {review.game_id} após falha de permissão.")
            return redirect(url_for('game_details', appid=review.game_id))
        else:
            print("Redirecionando para index após falha de permissão (review não encontrada).")
            # Fallback se a avaliação associada não for encontrada
            return redirect(url_for('index')) # Ou outra página apropriada

    db.session.delete(response)
    db.session.commit()
    print(f"Resposta {response_id} apagada com sucesso.")
    flash('Resposta apagada com sucesso!', 'success')
    # Redireciona de volta para a página do jogo da avaliação associada
    review = Review.query.get(response.review_id)
    if review:
        print(f"Redirecionando para game_details {review.game_id} após sucesso na exclusão.")
        return redirect(url_for('game_details', appid=review.game_id))
    else:
        print("Redirecionando para index após sucesso na exclusão (review não encontrada).")
        # Fallback se a avaliação associada não for encontrada
        return redirect(url_for('index')) # Ou outra página apropriada

@app.route('/api/search_games')
def api_search_games():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    games = steam_api.search_games(query)
    return jsonify(games)

@app.route('/api/game_details/<appid>')
def api_game_details(appid):
    game = steam_api.get_game_details(appid)
    if game:
        return jsonify(game)
    return jsonify({'error': 'Jogo não encontrado'}), 404

def update_database():
    with app.app_context():
        # Adiciona a coluna avatar_url se ela não existir
        try:
            db.engine.execute('ALTER TABLE user ADD COLUMN avatar_url VARCHAR(200) DEFAULT "static/uploads/default.png"')
        except Exception as e:
            print(f"Erro ao adicionar coluna avatar_url: {e}")

        # Adiciona as colunas likes e dislikes à tabela review
        try:
            db.engine.execute('ALTER TABLE review ADD COLUMN likes INTEGER DEFAULT 0')
            db.engine.execute('ALTER TABLE review ADD COLUMN dislikes INTEGER DEFAULT 0')
        except Exception as e:
            print(f"Erro ao adicionar colunas likes/dislikes: {e}")

        # Adiciona a coluna name à tabela community
        try:
            db.engine.execute('ALTER TABLE community ADD COLUMN name VARCHAR(100)')
        except Exception as e:
            print(f"Erro ao adicionar coluna name: {e}")

        # Adiciona as colunas bio e favorite_games à tabela user
        try:
            db.engine.execute('ALTER TABLE user ADD COLUMN bio TEXT')
            db.engine.execute('ALTER TABLE user ADD COLUMN favorite_games VARCHAR(500)')
        except Exception as e:
            print(f"Erro ao adicionar colunas bio/favorite_games: {e}")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Página de registro de novos usuários.
    Valida entradas e cria contas no banco de dados.
    """
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
    """
    Página de login de usuários existentes.
    Autentica e redireciona para a página inicial.
    """
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
    """
    Encerra a sessão do usuário atual.
    """
    logout_user()
    flash('Você saiu da sua conta', 'info')
    return redirect(url_for('index'))

@app.route('/create_community', methods=['GET', 'POST'])
@login_required
def create_community():
    if request.method == 'POST':
        game_id = request.form.get('game_id')
        game_name = request.form.get('game_name')
        game_img = request.form.get('game_img')
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Remove a verificação de comunidade existente para permitir várias comunidades por jogo
        # existing_community = Community.query.filter_by(game_id=game_id).first()
        # if existing_community:
        #     flash('Já existe uma comunidade para este jogo.', 'warning')
        #     return redirect(url_for('community_details', community_id=existing_community.id))
        
        # Cria a nova comunidade
        community = Community(
            name=name,
            game_id=game_id,
            game_name=game_name,
            game_img=game_img,
            description=description,
            creator_id=current_user.id
        )
        
        # Adiciona a comunidade ao banco de dados primeiro
        db.session.add(community)
        db.session.flush()  # Isso gera o ID da comunidade sem fazer commit
        
        # Agora cria o membro com o ID da comunidade
        member = CommunityMember(
            user_id=current_user.id,
            community_id=community.id
        )
        db.session.add(member)
        
        # Faz o commit de todas as alterações
        db.session.commit()
        
        flash('Comunidade criada com sucesso!', 'success')
        return redirect(url_for('community_details', community_id=community.id))
    
    # Se for GET, pega os parâmetros da URL
    game_id = request.args.get('game_id')
    game_name = request.args.get('game_name')
    game_img = request.args.get('game_img')
    
    return render_template('create_community.html', game_id=game_id, game_name=game_name, game_img=game_img)

@app.route('/community/<int:community_id>/invite', methods=['POST'])
@login_required
def invite_to_community(community_id):
    community = Community.query.get_or_404(community_id)
    username = request.form.get('username')
    
    if not username:
        flash('Por favor, forneça um nome de usuário.', 'danger')
        return redirect(url_for('community_details', community_id=community_id))
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('community_details', community_id=community_id))
    
    if CommunityMember.query.filter_by(user_id=user.id, community_id=community_id).first():
        flash('Este usuário já é membro da comunidade.', 'warning')
        return redirect(url_for('community_details', community_id=community_id))
    
    if CommunityInvitation.query.filter_by(
        community_id=community_id,
        sender_id=current_user.id,
        receiver_id=user.id,
        status='pending'
    ).first():
        flash('Já existe um convite pendente para este usuário.', 'warning')
        return redirect(url_for('community_details', community_id=community_id))
    
    invitation = CommunityInvitation(
        community_id=community_id,
        sender_id=current_user.id,
        receiver_id=user.id
    )
    db.session.add(invitation)
    
    notification = Notification(
        user_id=user.id,
        type='community_invite',
        content=f'{current_user.username} te convidou para participar da comunidade {community.name}',
        reference_id=community_id
    )
    db.session.add(notification)
    
    db.session.commit()
    flash('Convite enviado com sucesso!', 'success')
    return redirect(url_for('community_details', community_id=community_id))

@app.route('/review/<int:review_id>/respond', methods=['POST'])
@login_required
def respond_to_review(review_id):
    review = Review.query.get_or_404(review_id)
    content = request.form.get('content')
    
    if not content:
        flash('Por favor, forneça uma resposta.', 'danger')
        return redirect(url_for('game_details', appid=review.game_id))
    
    response = ReviewResponse(
        content=content,
        user_id=current_user.id,
        review_id=review_id
    )
    db.session.add(response)
    
    notification = Notification(
        user_id=review.user_id,
        type='review_response',
        content=f'{current_user.username} respondeu à sua avaliação de {review.game_name}',
        reference_id=review_id
    )
    db.session.add(notification)
    
    db.session.commit()
    flash('Resposta publicada com sucesso!', 'success')
    return redirect(url_for('forum'))

@app.route('/review/<int:review_id>/like', methods=['POST'])
@login_required
def like_review(review_id):
    review = Review.query.get_or_404(review_id)
    user_id = current_user.id

    # Evita que o autor vote na própria review
    if review.user_id == user_id:
        return jsonify({'likes': review.likes, 'dislikes': review.dislikes, 'user_vote': None}), 400 # Retorna 400 Bad Request ou outro código apropriado

    existing_vote = ReviewVote.query.filter_by(user_id=user_id, review_id=review_id).first()

    if existing_vote:
        if existing_vote.type == 'like':
            # Usuário já deu like, remove o like
            db.session.delete(existing_vote)
            review.likes -= 1
            user_vote_status = None
        else:
            # Usuário deu dislike, muda para like
            existing_vote.type = 'like'
            review.dislikes -= 1
            review.likes += 1
            user_vote_status = 'like'
    else:
        # Usuário não votou, adiciona like
        new_vote = ReviewVote(user_id=user_id, review_id=review_id, type='like')
        db.session.add(new_vote)
        review.likes += 1
        user_vote_status = 'like'

    db.session.commit()
    return jsonify({'likes': review.likes, 'dislikes': review.dislikes, 'user_vote': user_vote_status})

@app.route('/review/<int:review_id>/dislike', methods=['POST'])
@login_required
def dislike_review(review_id):
    review = Review.query.get_or_404(review_id)
    user_id = current_user.id

    # Evita que o autor vote na própria review
    if review.user_id == user_id:
         return jsonify({'likes': review.likes, 'dislikes': review.dislikes, 'user_vote': None}), 400 # Retorna 400 Bad Request ou outro código apropriado

    existing_vote = ReviewVote.query.filter_by(user_id=user_id, review_id=review_id).first()

    if existing_vote:
        if existing_vote.type == 'dislike':
            # Usuário já deu dislike, remove o dislike
            db.session.delete(existing_vote)
            review.dislikes -= 1
            user_vote_status = None
        else:
            # Usuário deu like, muda para dislike
            existing_vote.type = 'dislike'
            review.likes -= 1
            review.dislikes += 1
            user_vote_status = 'dislike'
    else:
        # Usuário não votou, adiciona dislike
        new_vote = ReviewVote(user_id=user_id, review_id=review_id, type='dislike')
        db.session.add(new_vote)
        review.dislikes += 1
        user_vote_status = 'dislike'

    db.session.commit()
    return jsonify({'likes': review.likes, 'dislikes': review.dislikes, 'user_vote': user_vote_status})

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/friend_request/<username>', methods=['POST'])
@login_required
def send_friend_request(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    if user.id == current_user.id:
        flash('Você não pode enviar solicitação de amizade para si mesmo.', 'warning')
        return redirect(url_for('profile', username=username))
    
    existing_request = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user.id)) |
        ((Friendship.user_id == user.id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if existing_request:
        flash('Já existe uma solicitação de amizade pendente.', 'warning')
        return redirect(url_for('profile', username=username))
    
    friendship = Friendship(user_id=current_user.id, friend_id=user.id)
    db.session.add(friendship)
    
    notification = Notification(
        user_id=user.id,
        type='friend_request',
        content=f'{current_user.username} enviou uma solicitação de amizade',
        reference_id=current_user.id
    )
    db.session.add(notification)
    
    db.session.commit()
    flash('Solicitação de amizade enviada!', 'success')
    return redirect(url_for('profile', username=username))

@app.route('/response/<int:response_id>/like', methods=['POST'])
@login_required
def like_response(response_id):
    response = ReviewResponse.query.get_or_404(response_id)
    user_id = current_user.id

    # Evita que o autor vote na própria resposta
    if response.user_id == user_id:
        return jsonify({'likes': response.likes, 'dislikes': response.dislikes, 'user_vote': None}), 400 # Retorna 400 Bad Request ou outro código apropriado

    existing_vote = ReviewResponseVote.query.filter_by(user_id=user_id, response_id=response_id).first()

    if existing_vote:
        if existing_vote.type == 'like':
            # Usuário já deu like, remove o like
            db.session.delete(existing_vote)
            response.likes -= 1
            user_vote_status = None
        else:
            # Usuário deu dislike, muda para like
            existing_vote.type = 'like'
            response.dislikes -= 1
            response.likes += 1
            user_vote_status = 'like'
    else:
        # Usuário não votou, adiciona like
        new_vote = ReviewResponseVote(user_id=user_id, response_id=response_id, type='like')
        db.session.add(new_vote)
        response.likes += 1
        user_vote_status = 'like'

    db.session.commit()
    return jsonify({'likes': response.likes, 'dislikes': response.dislikes, 'user_vote': user_vote_status})

@app.route('/response/<int:response_id>/dislike', methods=['POST'])
@login_required
def dislike_response(response_id):
    response = ReviewResponse.query.get_or_404(response_id)
    user_id = current_user.id

    # Evita que o autor vote na própria resposta
    if response.user_id == user_id:
        return jsonify({'likes': response.likes, 'dislikes': response.dislikes, 'user_vote': None}), 400 # Retorna 400 Bad Request ou outro código apropriado

    existing_vote = ReviewResponseVote.query.filter_by(user_id=user_id, response_id=response_id).first()

    if existing_vote:
        if existing_vote.type == 'dislike':
            # Usuário já deu dislike, remove o dislike
            db.session.delete(existing_vote)
            response.dislikes -= 1
            user_vote_status = None
        else:
            # Usuário deu like, muda para dislike
            existing_vote.type = 'dislike'
            response.likes -= 1
            response.dislikes += 1
            user_vote_status = 'dislike'
    else:
        # Usuário não votou, adiciona dislike
        new_vote = ReviewResponseVote(user_id=user_id, response_id=response_id, type='dislike')
        db.session.add(new_vote)
        response.dislikes += 1
        user_vote_status = 'dislike'

    db.session.commit()
    return jsonify({'likes': response.likes, 'dislikes': response.dislikes, 'user_vote': user_vote_status})

@app.route('/friend_request/<int:notification_id>/accept', methods=['POST'])
@login_required
def accept_friend_request(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id or notification.type != 'friend_request':
        flash('Notificação inválida.', 'danger')
        return redirect(url_for('notifications'))
    
    friendship = Friendship.query.filter_by(
        user_id=notification.reference_id,
        friend_id=current_user.id
    ).first()
    
    if friendship:
        friendship.status = 'accepted'
        notification.is_read = True
        db.session.commit()
        flash('Solicitação de amizade aceita!', 'success')
    
    return redirect(url_for('notifications'))

@app.route('/friend_request/<int:notification_id>/reject', methods=['POST'])
@login_required
def reject_friend_request(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id or notification.type != 'friend_request':
        flash('Notificação inválida.', 'danger')
        return redirect(url_for('notifications'))
    
    friendship = Friendship.query.filter_by(
        user_id=notification.reference_id,
        friend_id=current_user.id
    ).first()
    
    if friendship:
        friendship.status = 'rejected'
        notification.is_read = True
        db.session.commit()
        flash('Solicitação de amizade rejeitada.', 'info')
    
    return redirect(url_for('notifications'))

@app.route('/community_invite/<int:notification_id>/accept', methods=['POST'])
@login_required
def accept_community_invite(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id or notification.type != 'community_invite':
        flash('Notificação inválida.', 'danger')
        return redirect(url_for('notifications'))
    
    invitation = CommunityInvitation.query.filter_by(
        community_id=notification.reference_id,
        receiver_id=current_user.id,
        status='pending'
    ).first()
    
    if invitation:
        invitation.status = 'accepted'
        member = CommunityMember(user_id=current_user.id, community_id=invitation.community_id)
        db.session.add(member)
        notification.is_read = True
        db.session.commit()
        flash('Convite para comunidade aceito!', 'success')
    
    return redirect(url_for('notifications'))

@app.route('/community_invite/<int:notification_id>/reject', methods=['POST'])
@login_required
def reject_community_invite(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id or notification.type != 'community_invite':
        flash('Notificação inválida.', 'danger')
        return redirect(url_for('notifications'))
    
    invitation = CommunityInvitation.query.filter_by(
        community_id=notification.reference_id,
        receiver_id=current_user.id,
        status='pending'
    ).first()
    
    if invitation:
        invitation.status = 'rejected'
        notification.is_read = True
        db.session.commit()
        flash('Convite para comunidade rejeitado.', 'info')
    
    return redirect(url_for('notifications'))

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.date_posted.desc()).all()
    communities = [member.community for member in user.communities]
    
    # Busca amigos
    friendships_query = Friendship.query.filter(
        ((Friendship.user_id == user.id) | (Friendship.friend_id == user.id)) &
        (Friendship.status == 'accepted')
    )
    
    # Busca a relação de amizade entre o usuário logado e o usuário do perfil
    friendship_status = 'not_friends'
    if current_user.is_authenticated and current_user.id != user.id:
        existing_friendship = Friendship.query.filter(
            ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user.id)) |
            ((Friendship.user_id == user.id) & (Friendship.friend_id == current_user.id))
        ).first()
        
        if existing_friendship:
            if existing_friendship.status == 'accepted':
                friendship_status = 'friends'
            elif existing_friendship.user_id == current_user.id and existing_friendship.status == 'pending':
                friendship_status = 'pending_sent'
            elif existing_friendship.friend_id == current_user.id and existing_friendship.status == 'pending':
                friendship_status = 'pending_received'


    friends = []
    for friendship in friendships_query.all():
        if friendship.status == 'accepted': # Considera apenas amizades aceitas para a lista de amigos
            if friendship.user_id == user.id:
                friend = User.query.get(friendship.friend_id)
            else:
                friend = User.query.get(friendship.user_id)
            friends.append(friend)


    return render_template('profile.html', 
                         user=user, 
                         reviews=reviews, 
                         communities=communities,
                         friends=friends,
                         steam_api=steam_api,
                         friendship_status=friendship_status)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.files.get('avatar'):
        avatar = request.files['avatar']
        if avatar:
            filename = secure_filename(avatar.filename)
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar.save(avatar_path)
            current_user.avatar_url = f'uploads/{filename}'
    
    current_user.bio = request.form.get('bio')
    current_user.favorite_games = request.form.get('favorite_games')
    
    db.session.commit()
    flash('Perfil atualizado com sucesso!', 'success')
    return redirect(url_for('profile', username=current_user.username))

@app.route('/profile/<username>/invite', methods=['POST'])
@login_required
def invite_to_community_from_profile(username):
    # Encontra o usuário cujo perfil está sendo visualizado
    user_to_invite = User.query.filter_by(username=username).first_or_404()

    # Pega o ID da comunidade do formulário
    community_id = request.form.get('community_id')
    if not community_id:
        flash('Comunidade não selecionada.', 'danger')
        return redirect(url_for('profile', username=username))

    community = Community.query.get_or_404(community_id)

    # Verifica se o usuário logado é membro da comunidade selecionada
    is_member_of_selected_community = CommunityMember.query.filter_by(
        user_id=current_user.id,
        community_id=community.id
    ).first()
    if not is_member_of_selected_community:
        flash('Você não é membro desta comunidade e não pode convidar.', 'danger')
        return redirect(url_for('profile', username=username))

    # Verifica se o usuário a ser convidado já é membro
    if CommunityMember.query.filter_by(user_id=user_to_invite.id, community_id=community.id).first():
        flash(f'{user_to_invite.username} já é membro desta comunidade.', 'warning')
        return redirect(url_for('profile', username=username))

    # Verifica se já existe um convite pendente
    existing_invitation = CommunityInvitation.query.filter_by(
        community_id=community.id,
        receiver_id=user_to_invite.id,
        status='pending'
    ).first()
    if existing_invitation:
        flash(f'Já existe um convite pendente para {user_to_invite.username} nesta comunidade.', 'warning')
        return redirect(url_for('profile', username=username))

    # Cria o convite
    invitation = CommunityInvitation(
        community_id=community.id,
        sender_id=current_user.id,
        receiver_id=user_to_invite.id
    )
    db.session.add(invitation)

    # Cria a notificação
    notification = Notification(
        user_id=user_to_invite.id,
        type='community_invite',
        content=f'{current_user.username} te convidou para participar da comunidade {community.name}',
        reference_id=community.id
    )
    db.session.add(notification)

    db.session.commit()
    flash('Convite enviado com sucesso!', 'success')
    return redirect(url_for('profile', username=username))

@app.route('/profile/<username>/friends')
def user_friends(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Busca amigos
    friendships_query = Friendship.query.filter(
        ((Friendship.user_id == user.id) | (Friendship.friend_id == user.id)) &
        (Friendship.status == 'accepted')
    )
    
    friends = []
    for friendship in friendships_query.all():
        if friendship.user_id == user.id:
            friend = User.query.get(friendship.friend_id)
        else:
            friend = User.query.get(friendship.user_id)
        friends.append(friend)
    
    return render_template('user_friends.html', user=user, friends=friends)

@app.route('/edit_community', methods=['POST'])
@login_required
def edit_community():
    community_id = request.form.get('community_id')
    name = request.form.get('name')
    description = request.form.get('description')
    
    community = Community.query.get_or_404(community_id)
    
    # Verifica se o usuário é o criador da comunidade
    if current_user.id != community.creator_id:
        flash('Você não tem permissão para editar esta comunidade.', 'error')
        return redirect(url_for('communities'))
    
    # Atualiza os dados da comunidade
    community.name = name
    community.description = description
    
    try:
        db.session.commit()
        flash('Comunidade atualizada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar a comunidade.', 'error')
    
    return redirect(url_for('community_details', community_id=community_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = Post.query.get_or_404(comment.post_id)
    if comment.user_id != current_user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Você não tem permissão para apagar este comentário.'}), 403
        flash('Você não tem permissão para apagar este comentário.', 'danger')
        if post.community_id:
            return redirect(url_for('community_details', community_id=post.community_id))
        else:
            return redirect(url_for('forum'))
    db.session.delete(comment)
    db.session.commit()
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Comentário apagado com sucesso!'}), 200
    flash('Comentário apagado com sucesso!', 'success')
    if post.community_id:
        return redirect(url_for('community_details', community_id=post.community_id))
    else:
        return redirect(url_for('forum'))

@app.route('/community/<int:community_id>/kick/<int:user_id>', methods=['POST'])
@login_required
def kick_member(community_id, user_id):
    community = Community.query.get_or_404(community_id)
    if current_user.id != community.creator_id:
        flash('Apenas o líder pode expulsar membros.', 'danger')
        return redirect(url_for('community_members', community_id=community_id))
    if user_id == community.creator_id:
        flash('O líder não pode se expulsar.', 'warning')
        return redirect(url_for('community_members', community_id=community_id))
    member = CommunityMember.query.filter_by(user_id=user_id, community_id=community_id).first()
    if not member:
        flash('Membro não encontrado.', 'danger')
        return redirect(url_for('community_members', community_id=community_id))
    db.session.delete(member)
    db.session.commit()
    flash('Membro expulso com sucesso!', 'success')
    return redirect(url_for('community_members', community_id=community_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        update_database()
    app.run(debug=True)