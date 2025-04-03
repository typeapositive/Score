# Avaliador de Jogos da Steam

Um aplicativo web em Python com Flask que permite aos usuários visualizar, buscar e avaliar jogos da Steam, além de compartilhar suas opiniões com outros usuários através de um fórum.

## Funcionalidades

- **Autenticação de Usuários**: Sistema completo de registro e login
- **Exploração de Jogos**: Busca e visualização de jogos populares da Steam
- **Avaliações**: Os usuários podem escrever avaliações e atribuir classificação por estrelas
- **Fórum de Avaliações**: Um espaço público para visualizar todas as avaliações dos usuários
- **Interface Responsiva**: Design agradável e responsivo inspirado na estética da Steam

## Tecnologias Utilizadas

### Backend
- **Python 3.10**: Linguagem de programação principal
- **Flask 2.0.1**: Framework web leve e flexível para desenvolvimento rápido de aplicações
- **Werkzeug 2.0.1**: Biblioteca de utilitários WSGI para Python, usado pelo Flask

### Banco de Dados
- **SQLite**: Banco de dados relacional embutido, ideal para aplicações de pequeno a médio porte
- **SQLAlchemy 1.4.23**: ORM (Object Relational Mapper) que facilita a interação com o banco de dados
- **Flask-SQLAlchemy 2.5.1**: Extensão do Flask que adiciona suporte para SQLAlchemy

### Autenticação e Segurança
- **Flask-Login 0.5.0**: Gerenciamento de sessões de usuário e autenticação
- **Werkzeug Security**: Utilizado para hash de senhas (generate_password_hash e check_password_hash)
- **Flask-WTF 0.15.1**: Integração do WTForms com Flask para validação de formulários

### Frontend
- **HTML5**: Estruturação do conteúdo das páginas
- **CSS3**: Estilização das páginas
- **Bootstrap 5**: Framework de design responsivo para criar interfaces consistentes
- **FontAwesome**: Biblioteca de ícones vetoriais
- **Jinja2 3.1.6**: Motor de templates usado pelo Flask para renderizar páginas HTML dinâmicas

### Integrações e APIs
- **Requests 2.26.0**: Biblioteca para fazer requisições HTTP
- **API Steam (simulada)**: Interface programática para acessar dados de jogos da Steam
- **Python-dotenv 0.19.1**: Carregamento de variáveis de ambiente a partir de um arquivo .env

### Ferramentas de Desenvolvimento
- **Pylance/Pyright**: Servidor de linguagem Python para análise estática de código
- **Visual Studio Code**: IDE utilizada para o desenvolvimento

## Configuração e Execução

### Pré-requisitos

- Python 3.7+ (recomendado Python 3.10)
- pip (gerenciador de pacotes Python)

### Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/avaliador-steam.git
cd avaliador-steam
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. (Opcional) Configure sua chave de API da Steam:
Crie um arquivo `.env` na raiz do projeto e adicione:
```
STEAM_API_KEY=sua_chave_api_aqui
```

4. Execute a aplicação:
```
python app.py
```

5. Acesse a aplicação em seu navegador:
```
http://localhost:5000
```

## Estrutura do Projeto

### Arquivos Principais
- `app.py`: Arquivo principal da aplicação Flask (rotas, configurações, modelos de dados)
- `api_steam.py`: Módulo para interação com a API da Steam (consulta e processamento de dados de jogos)
- `requirements.txt`: Lista de dependências do projeto
- `site.db`: Banco de dados SQLite (criado automaticamente)

### Diretórios
- `templates/`: Arquivos HTML das páginas
  - `base.html`: Template base com estrutura comum (navbar, footer, etc.)
  - `index.html`: Página inicial com listagem de jogos
  - `game.html`: Página de detalhes de um jogo específico
  - `review.html`: Formulário para criação de avaliações
  - `forum.html`: Página do fórum com todas as avaliações
  - `auth/`: Templates relacionados à autenticação
    - `login.html`: Página de login
    - `register.html`: Página de registro de novos usuários

### Modelos de Dados
- **User**: Representa os usuários do sistema, com autenticação via Flask-Login
  - Atributos: id, username, email, password_hash
  - Relacionamentos: reviews (lista de avaliações feitas pelo usuário)

- **Review**: Representa as avaliações de jogos
  - Atributos: id, game_id, game_name, content, rating, date_posted, user_id
  - Relacionamentos: author (usuário que fez a avaliação)

## Como as Tecnologias São Utilizadas

### Flask
- Gerencia as rotas da aplicação web
- Renderiza templates com dados dinâmicos
- Manipula formulários e requisições HTTP
- Interage com o banco de dados através do SQLAlchemy

### SQLAlchemy
- Define modelos de dados como classes Python
- Cria e gerencia o esquema do banco de dados
- Permite consultas eficientes sem SQL direto
- Gerencia relacionamentos entre tabelas (ex: usuário -> avaliações)

### Flask-Login
- Gerencia sessões de usuário seguras
- Controla acesso a páginas restritas
- Armazena o usuário atual na sessão
- Permite decoradores como @login_required para proteção de rotas

### Jinja2 Templates
- Renderiza HTML dinâmico com dados do servidor
- Permite herança de templates (base.html serve como layout principal)
- Suporta expressões condicionais (if/else) e loops (for) no HTML

### API da Steam (Simulada)
- Busca informações sobre jogos na plataforma
- Permite pesquisa de jogos por nome
- Fornece detalhes como imagens, descrições e classificações de jogos

## Implementação da API da Steam

Atualmente, o projeto utiliza dados simulados em vez de requisições reais à API da Steam. Para implementar a API real:

1. Obtenha uma chave de API da Steam em: https://steamcommunity.com/dev/apikey
2. Modifique o módulo `api_steam.py` para usar os endpoints reais, como:
   - `https://api.steampowered.com/ISteamApps/GetAppList/v0002/`
   - `https://store.steampowered.com/api/appdetails?appids={app_id}`

## Fluxo de Funcionamento

1. Usuários se registram e fazem login na plataforma
2. Na página inicial, podem ver jogos populares ou pesquisar por jogos específicos
3. Ao clicar em um jogo, veem detalhes e avaliações existentes
4. Usuários logados podem adicionar suas próprias avaliações
5. O fórum mostra todas as avaliações recentes de todos os jogos

## Contribuindo

Sinta-se à vontade para contribuir com o projeto através de issues ou pull requests.

## Configuração do Ambiente de Desenvolvimento

O projeto utiliza arquivos de configuração especiais para o VS Code e Pylance:
- `.vscode/settings.json`: Configurações do VS Code para Python
- `pyrightconfig.json`: Configurações do Pylance para análise de código

## Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes. 