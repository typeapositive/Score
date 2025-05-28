import requests
import os
import json
import time
import re
from markupsafe import Markup


STEAM_API_KEY = 'SUA_CHAVE_API_AQUI'

def get_all_steam_games():
    """
    Vamos buscar todos os jogos disponíveis na Steam!
    
    Esta função se conecta à API oficial da Steam e traz a lista completa
    de jogos - são milhares deles! O retorno é uma lista onde cada jogo
    tem um ID (appid) e nome.
    """
    try:
        #lista gigante de jogos da Steam
        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            apps = data.get('applist', {}).get('apps', [])
            
            #api filtra coisa que não é jogo, então é bom filtrar
            return apps
        else:
            print(f"Eita, tivemos um problema com a API da Steam! Código: {response.status_code}")
            return _get_sample_games()
    except Exception as e:
        print(f"Nossa, algo deu errado ao buscar os jogos da Steam: {str(e)}")
        #backup de jogos famosos
        return _get_sample_games()

def _get_sample_games():
    """
    Nossa lista de emergência com jogos populares!
    
    Quando a API da Steam não responde, usamos esta lista para
    garantir que o aplicativo continue funcionando.
    """
    return [
        {"appid": 570, "name": "Dota 2"},
        {"appid": 730, "name": "Counter-Strike 2"},
        {"appid": 440, "name": "Team Fortress 2"},
        {"appid": 230410, "name": "Warframe"},
        {"appid": 271590, "name": "Grand Theft Auto V"},
        {"appid": 252490, "name": "Rust"},
        {"appid": 578080, "name": "PUBG: BATTLEGROUNDS"},
        {"appid": 1174180, "name": "Red Dead Redemption 2"},
        {"appid": 359550, "name": "Rainbow Six Siege"},
        {"appid": 1091500, "name": "Cyberpunk 2077"}
    ]

def get_popular_games(limit=20):
    """
    Descubra quais são os jogos mais bombados da Steam!
    
    Esta função traz os jogos mais populares do momento.
    Você pode definir quantos jogos quer ver com o parâmetro 'limit'.
    """
    try:
        #pegar os mais jogados
        
        popular_appids = [570, 730, 440, 230410, 271590, 252490, 578080, 1174180, 359550, 1091500, 
                         238960, 582010, 292030, 1245620, 1817070, 1172470, 1599340, 400, 550, 218620]
        
        games = []
        for appid in popular_appids[:limit]:
            #mais detalhes sobre cada jogo
            details = get_game_details(str(appid))
            if details and 'name' in details:
                games.append({
                    "appid": str(appid),
                    "name": details['name'],
                    "img_url": details.get('img_url', f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg")
                })
        
        if len(games) < limit:
            print(f"Hmm, conseguimos apenas {len(games)} jogos... vamos completar a lista!")
            sample_games = [
                {"appid": "570", "name": "Dota 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/570/header.jpg"},
                {"appid": "730", "name": "Counter-Strike 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg"},
                {"appid": "440", "name": "Team Fortress 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/440/header.jpg"},
                {"appid": "230410", "name": "Warframe", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/230410/header.jpg"},
                {"appid": "271590", "name": "Grand Theft Auto V", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/271590/header.jpg"},
                {"appid": "252490", "name": "Rust", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/252490/header.jpg"},
                {"appid": "578080", "name": "PUBG: BATTLEGROUNDS", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/578080/header.jpg"},
                {"appid": "1174180", "name": "Red Dead Redemption 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg"},
                {"appid": "359550", "name": "Rainbow Six Siege", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/359550/header.jpg"},
                {"appid": "1091500", "name": "Cyberpunk 2077", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg"}
            ]
            missing_count = limit - len(games)
            games.extend(sample_games[:missing_count])
        
        return games
    except Exception as e:
        print(f"Ops! Tivemos um problema ao buscar os jogos populares: {str(e)}")
        #lista de jogos famosos
        sample_games = [
            {"appid": "570", "name": "Dota 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/570/header.jpg"},
            {"appid": "730", "name": "Counter-Strike 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg"},
            {"appid": "440", "name": "Team Fortress 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/440/header.jpg"},
            {"appid": "230410", "name": "Warframe", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/230410/header.jpg"},
            {"appid": "271590", "name": "Grand Theft Auto V", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/271590/header.jpg"},
            {"appid": "252490", "name": "Rust", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/252490/header.jpg"},
            {"appid": "578080", "name": "PUBG: BATTLEGROUNDS", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/578080/header.jpg"},
            {"appid": "1174180", "name": "Red Dead Redemption 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg"},
            {"appid": "359550", "name": "Rainbow Six Siege", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/359550/header.jpg"},
            {"appid": "1091500", "name": "Cyberpunk 2077", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg"}
        ]
        return sample_games[:limit]

def search_games(query, limit=10):
    """
    Procurando por algum jogo específico? É só me falar!
    
    Digite o nome (ou parte dele) do jogo que você procura,
    e vamos encontrar até 'limit' jogos que correspondam.
    """
    if not query or len(query.strip()) < 2:
        #se a busca estiver vazia, mostra os mais populares
        return get_popular_games(limit)
    
    try:
        #buscar todos os jogos e filtrar aqui mesmo
        all_games = get_all_steam_games()
        
        #encontrar jogos que combinam com a busca
        filtered_games = []
        
        for game in all_games:
            game_name_lower = game['name'].lower()
            query_lower = query.lower()
            # Verifica se o nome do jogo começa com a query ou contém a query
            if game_name_lower.startswith(query_lower) or query_lower in game_name_lower:
                #montar um objeto com as infos necessárias
                appid = str(game['appid'])
                filtered_games.append({
                    "appid": appid,
                    "name": game['name'],
                    "img_url": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"
                })
                
                if len(filtered_games) >= limit:
                    break
        
        #tentar com dados de backup se nao encontrar nada
        if not filtered_games:
            print("Hmm, não encontramos nenhum jogo com esse nome, vamos verificar nossa lista local!")
            #usar lista local de jogos populares
            all_games = [
                {"appid": "570", "name": "Dota 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/570/header.jpg"},
                {"appid": "730", "name": "Counter-Strike 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg"},
                {"appid": "440", "name": "Team Fortress 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/440/header.jpg"},
                {"appid": "230410", "name": "Warframe", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/230410/header.jpg"},
                {"appid": "271590", "name": "Grand Theft Auto V", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/271590/header.jpg"},
                {"appid": "252490", "name": "Rust", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/252490/header.jpg"},
                {"appid": "578080", "name": "PUBG: BATTLEGROUNDS", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/578080/header.jpg"},
                {"appid": "1174180", "name": "Red Dead Redemption 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg"},
                {"appid": "359550", "name": "Rainbow Six Siege", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/359550/header.jpg"},
                {"appid": "1091500", "name": "Cyberpunk 2077", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg"},
                {"appid": "238960", "name": "Path of Exile", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/238960/header.jpg"},
                {"appid": "582010", "name": "Monster Hunter: World", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/582010/header.jpg"},
                {"appid": "292030", "name": "The Witcher 3: Wild Hunt", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/292030/header.jpg"},
                {"appid": "1245620", "name": "Elden Ring", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg"},
                {"appid": "1817070", "name": "Baldur's Gate 3", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1817070/header.jpg"}
            ]
            
            filtered_games = [game for game in all_games if query in game['name'].lower()]
        
        return filtered_games[:limit]
    except Exception as e:
        print(f"Puxa, tivemos um problema na busca: {str(e)}")
        #lista de emergência
        all_games = [
            {"appid": "570", "name": "Dota 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/570/header.jpg"},
            {"appid": "730", "name": "Counter-Strike 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg"},
            {"appid": "440", "name": "Team Fortress 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/440/header.jpg"},
            {"appid": "230410", "name": "Warframe", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/230410/header.jpg"},
            {"appid": "271590", "name": "Grand Theft Auto V", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/271590/header.jpg"},
            {"appid": "252490", "name": "Rust", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/252490/header.jpg"},
            {"appid": "578080", "name": "PUBG: BATTLEGROUNDS", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/578080/header.jpg"},
            {"appid": "1174180", "name": "Red Dead Redemption 2", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg"},
            {"appid": "359550", "name": "Rainbow Six Siege", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/359550/header.jpg"},
            {"appid": "1091500", "name": "Cyberpunk 2077", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg"},
            {"appid": "238960", "name": "Path of Exile", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/238960/header.jpg"},
            {"appid": "582010", "name": "Monster Hunter: World", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/582010/header.jpg"},
            {"appid": "292030", "name": "The Witcher 3: Wild Hunt", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/292030/header.jpg"},
            {"appid": "1245620", "name": "Elden Ring", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg"},
            {"appid": "1817070", "name": "Baldur's Gate 3", "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1817070/header.jpg"}
        ]
        
        filtered_games = [game for game in all_games if query in game['name'].lower()]
        return filtered_games[:limit]

def _clean_html_description(description):
    """
    Limpa e formata a descrição HTML do jogo para exibição segura.
    
    A API da Steam geralmente retorna descrições com HTML pesado.
    Esta função limpa ou ajusta esse conteúdo para exibição segura.
    """
    if not description:
        return "Descrição não disponível"
    
    #remover tags de script que podem ser perigosas
    description = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', description)
    
    # Converter pra markup do flask para renderizar HTML seguro
    return Markup(description)

def get_game_details(appid):
    """
    Vamos descobrir tudo sobre um jogo específico!
    
    Forneça o ID do jogo (appid) e retornaremos todas as informações
    disponíveis como nome, descrição, desenvolvedor, preço e muito mais.
    """
    try:
        #perguntar diretamente pra a loja da Steam sobre este jogo
        #adicionando parâmetro pra solicitar a API em português (pt-BR)
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=brazilian"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            #verificar se a API deu uma resposta completa
            if data and appid in data and data[appid]['success']:
                game_data = data[appid]['data']
                
                #obter a descrição e limpar o HTML
                description = game_data.get('detailed_description', game_data.get('about_the_game', 'Descrição não disponível'))
                cleaned_description = _clean_html_description(description)
                
                #organizar as informações do jogo de forma clara
                return {
                    "appid": appid,
                    "name": game_data.get('name', 'Nome não disponível'),
                    "description": cleaned_description,
                    "img_url": game_data.get('header_image', f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"),
                    "developer": ", ".join(game_data.get('developers', ['Desconhecido'])),
                    "publisher": ", ".join(game_data.get('publishers', ['Desconhecido'])),
                    "release_date": game_data.get('release_date', {}).get('date', 'Data desconhecida'),
                    "genres": [genre.get('description', '') for genre in game_data.get('genres', [])],
                    "price": _format_price(game_data.get('price_overview', {}))
                }
        print(f"A API da Steam não retornou dados válidos para o jogo {appid}. Usando dados de backup.")
        return _get_sample_game_details(appid)
    
    except Exception as e:
        print(f"Eita! Erro ao buscar detalhes do jogo {appid}: {str(e)}")
        return _get_sample_game_details(appid)

def _format_price(price_data):
    """
    Vamos deixar o preço do jogo bonito e legível!
    
    Esta função pega os dados de preço da API e os formata
    de um jeito fácil de entender para o usuário.
    """
    if not price_data:
        return "Preço não disponível"
    
    if price_data.get('final_formatted', '') == '':
        return "Gratuito para Jogar"
    
    #devolve o preço formatado certinho
    return price_data.get('final_formatted', 'Preço não disponível')

def _get_sample_game_details(appid):
    """
    Nossa enciclopédia de emergência com detalhes dos jogos mais populares!
    
    Quando a API não nos dá as informações, recorremos a esta coleção
    de detalhes pré-definidos para os jogos mais conhecidos.
    """
    #biblioteca de informações sobre os jogos mais famosos
    sample_games = {
        "570": {
            "appid": "570",
            "name": "Dota 2",
            "description": Markup("Jogo MOBA gratuito da Valve. Cada dia, milhões de jogadores ao redor do mundo batalham como um dos mais de cem heróis do Dota. Com atualizações regulares que garantem evolução constante de gameplay, recursos e heróis, o Dota 2 realmente ganhou vida própria."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/570/header.jpg",
            "developer": "Valve",
            "publisher": "Valve",
            "release_date": "9 Jul, 2013",
            "genres": ["MOBA", "Free to Play", "Strategy"],
            "price": "Gratuito para Jogar"
        },
        "730": {
            "appid": "730",
            "name": "Counter-Strike 2",
            "description": Markup("Counter-Strike 2 é a evolução do icônico FPS competitivo da Valve. Com gráficos melhorados e jogabilidade refinada, mantém a essência do CS:GO enquanto oferece uma experiência mais moderna e dinâmica. Desfrute de visuais aprimorados, física mais realista e mecânicas de jogo otimizadas nesta renovação do lendário shooter tático."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg",
            "developer": "Valve",
            "publisher": "Valve",
            "release_date": "26 Set, 2023",
            "genres": ["FPS", "Shooter", "Competitive"],
            "price": "Gratuito para Jogar"
        },
        "440": {
            "appid": "440",
            "name": "Team Fortress 2",
            "description": Markup("FPS de classes gratuito da Valve com um estilo visual cartunesco e humorístico. Escolha entre nove classes distintas, cada uma com suas próprias armas e personalidades marcantes, e participe de diversos modos de jogo em ambientes coloridos e caóticos. Um dos jogos de tiro em equipe mais divertidos e acessíveis disponíveis."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/440/header.jpg",
            "developer": "Valve",
            "publisher": "Valve",
            "release_date": "10 Out, 2007",
            "genres": ["FPS", "Hero Shooter", "Cartoon"],
            "price": "Gratuito para Jogar"
        },
        "230410": {
            "appid": "230410",
            "name": "Warframe",
            "description": Markup("Jogo de ação e RPG gratuito onde você controla guerreiros conhecidos como Tenno, comandando poderosas armaduras biomecânicas chamadas Warframes. Explore um universo de ficção científica em constante expansão, com dezenas de Warframes para colecionar, armas para personalizar, e uma história rica e envolvente que continua crescendo com atualizações regulares."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/230410/header.jpg",
            "developer": "Digital Extremes",
            "publisher": "Digital Extremes",
            "release_date": "25 Mar, 2013",
            "genres": ["Action", "RPG", "Free to Play"],
            "price": "Gratuito para Jogar"
        },
        "271590": {
            "appid": "271590",
            "name": "Grand Theft Auto V",
            "description": Markup("Jogo de mundo aberto da Rockstar Games que permite explorar a imensa e vibrante cidade de Los Santos e o condado de Blaine. Siga a história interligada de três criminosos distintos na campanha single-player ou mergulhe no Grand Theft Auto Online, onde você pode construir seu próprio império criminoso junto com milhões de outros jogadores em um mundo compartilhado em constante evolução."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/271590/header.jpg",
            "developer": "Rockstar North",
            "publisher": "Rockstar Games",
            "release_date": "14 Abr, 2015",
            "genres": ["Open World", "Action", "Adventure"],
            "price": "R$ 99,99"
        },
        "1817070": {
            "appid": "1817070",
            "name": "Marvel's Spider-Man Remastered",
            "description": Markup("Desenvolvido pela Insomniac Games em colaboração com a Marvel, Marvel's Spider-Man Remastered traz um Peter Parker experiente combatendo o crime e icônicos vilões em Nova York, enquanto tenta equilibrar sua caótica vida pessoal. Balancie-se pelos arranha-céus, combata vilões com um sistema de combate dinâmico e explore uma Nova York vibrante e detalhada nesta aventura de super-herói definitiva."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1817070/header.jpg",
            "developer": "Insomniac Games, Nixxes Software",
            "publisher": "PlayStation PC LLC",
            "release_date": "12 Ago, 2022",
            "genres": ["Ação", "Aventura", "Super-herói"],
            "price": "R$ 249,90"
        },
        "1245620": {
            "appid": "1245620", 
            "name": "Elden Ring",
            "description": Markup("Um novo RPG de ação e fantasia desenvolvido pela FromSoftware, Inc. e pela BANDAI NAMCO Entertainment Inc. A vasta experiência nascida de uma série de jogos de Dark Souls, Bloodborne e Sekiro: Shadows Die Twice. Elden Ring é a maior aventura da FromSoftware até hoje e está repleta de elementos que você pode desfrutar nesse imenso mundo interligado."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg",
            "developer": "FromSoftware",
            "publisher": "Bandai Namco",
            "release_date": "25 Fev, 2022",
            "genres": ["Souls-like", "RPG", "Mundo Aberto"],
            "price": "R$ 299,90"
        },
        "292030": {
            "appid": "292030",
            "name": "The Witcher 3: Wild Hunt",
            "description": Markup("The Witcher 3: Wild Hunt é um RPG de mundo aberto ambientado em um universo de fantasia visualmente deslumbrante, cheio de escolhas significativas e consequências impactantes. Em The Witcher, você joga como Geralt de Rívia, um caçador de monstros profissional encarregado de encontrar uma criança da profecia em um vasto mundo aberto, rico em cidades mercantis, ilhas piratas, passagens perigosas por montanhas e cavernas esquecidas."),
            "img_url": "https://cdn.cloudflare.steamstatic.com/steam/apps/292030/header.jpg",
            "developer": "CD PROJEKT RED",
            "publisher": "CD PROJEKT RED",
            "release_date": "18 Mai, 2015",
            "genres": ["RPG", "Mundo Aberto", "Fantasia"],
            "price": "R$ 79,99"
        }
    }
    
    #se não encontrar o jogo na biblioteca, cria uma resposta padrão
    return sample_games.get(appid, {
        "appid": appid,
        "name": "Jogo não encontrado",
        "description": Markup("Detalhes indisponíveis para este jogo."),
        "img_url": f"https://via.placeholder.com/460x215/2a475e/c7d5e0?text=Jogo+n%C3%A3o+encontrado",
        "developer": "Desconhecido",
        "publisher": "Desconhecido",
        "release_date": "Desconhecido",
        "genres": [],
        "price": "Desconhecido"
    }) 