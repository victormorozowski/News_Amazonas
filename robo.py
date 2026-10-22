from datetime import datetime, timedelta
import json
import os
from email.utils import parsedate_to_datetime

try:
    from gnews import GNews
    google_news = GNews(language='pt', country='BR', period='1d', max_results=8)
except Exception as e:
    print(f"Aviso ao inicializar GNews: {e}")
    google_news = None

# Lista de temas unificada e limpa (sem duplicações visuais)
TEMAS_BUSCA = [
    "Polícia Federal Amazonas",
    "Superintendência Polícia Federal Amazonas",
    "Superintendente da Polícia Federal no Amazonas Danielle Mady",
    "Tráfico de drogas Amazonas",
    "Apreensão de drogas Amazonas",
    "Segurança Pública Amazonas",
    "Desmatamento Amazonas",
    "Queimadas Amazonas",
    "Garimpo ilegal Amazonas",
    "Extração de ouro Amazonas",
    "Prisão Amazonas",
    "Pirataria fluvial Amazonas",
    "Política Amazonas",
    "Polícia Civil Amazonas",
    "Polícia Militar Amazonas",
    "Operações Polícia Federal Amazonas",
    "Órgãos Federais Amazonas",
]

# Lista completa de municípios e termos geográficos do Amazonas
MUNICIPIOS_AM = [
    "alvarães", "amaturá", "anamã", "anori", "apuí", "atalaia do norte", "autazes", 
    "barcelos", "barreirinha", "benjamin constant", "beruri", "boa vista do ramos", 
    "boca do acre", "borba", "caapiranga", "canutama", "carauari", "careiro", 
    "careiro da várzea", "coari", "codajás", "eirunepé", "envira", "fonte boa", 
    "guajará", "humaitá", "ipixuna", "iranduba", "itacoatiara", "itamarati", 
    "itapiranga", "japurá", "juruá", "jutaí", "lábrea", "manacapuru", "manaquiri", 
    "manaus", "manicoré", "maraã", "maués", "nhamundá", "nova olinda do norte", 
    "novo airão", "novo aripuanã", "parintins", "pauini", "presidente figueiredo", 
    "rio preto da eva", "santa isabel do rio negro", "santo antônio do içá", 
    "são gabriel da cachoeira", "são paulo de olivença", "são sebastião do uatumã", 
    "silves", "tabatinga", "tapauá", "tefé", "tonantins", "uarini", "urucará", 
    "urucurituba", "amazonas", "am", "alto solimões", "rio negro", "rio solimões"
]

# Palavras-chave obrigatórias do cerne operacional/institucional (a notícia deve conter pelo menos uma)
CERNE_TEMATICO = [
    "polícia", "policial", "delegado", "delegada", "pf", "prf", "federal", "civil", 
    "militar", "operação", "investigação", "investigado", "prisão", "preso", 
    "apreensão", "apreendido", "droga", "drogas", "tráfico", "crime", "criminoso", 
    "garimpo", "ouro", "desmatamento", "queimada", "ambiental", "meio ambiente", 
    "pirataria", "fluvial", "justiça", "ministério", "governo", "deputado", 
    "senador", "vereador", "prefeito", "política", "político", "corregedoria", 
    "supremo", "tribunal", "juiz"
]

# Termos de ruído absoluto que devem ser eliminados (notícias irrelevantes de fora)
TERMOS_RUIDO = [
    "vestibular", "biblioteca", "escola municipal", "ensino fundamental", 
    "educação inclusiva", "formatura", "teatro", "exposição cultural", 
    "campeonato municipal", "festa de", "campeonato de futebol"
]

def validar_relevancia_noticia(titulo, resumo, link):
    texto = f"{titulo} {resumo}".lower()
    
    # 1. Se contiver termos clássicos de ruído irrelevante, rejeita direto
    for ruido in TERMOS_RUIDO:
        if ruido in texto:
            return False

    # 2. Exceção direta se citar a Superintendente por nome ou cargo
    termos_superintendente = [
        "danielle mady", "danielle de meneses", "delegada danielle", 
        "superintendente danielle", "danielle meneses"
    ]
    if any(termo in texto for termo in termos_superintendente):
        return True

    # 3. O texto DEVE obrigatoriamente mencionar o Amazonas ou algum município
    tem_vinculo_am = any(mun in texto for mun in MUNICIPIOS_AM)
    if not tem_vinculo_am:
        return False

    # 4. O texto DEVE obrigatoriamente tocar no cerne temático (segurança, polícia, meio ambiente, política, operações)
    tem_cerne = any(cerne in texto for cerne in CERNE_TEMATICO)
    
    return tem_cerne

def formatar_data_brasil(data_str):
    if not data_str:
        return "Data não informada"
    
    str_val = str(data_str).strip()
    
    try:
        dt_utc = parsedate_to_datetime(str_val)
        if dt_utc:
            dt_local = dt_utc - timedelta(hours=4)
            return dt_local.strftime('%d/%m/%Y às %H:%M (GMT-4 Manaus)')
    except:
        pass
    
    texto = str_val.lower()
    substituicoes = [
        ("hours ago", "horas atrás"), ("hour ago", "hora atrás"),
        ("hours", "horas"), ("hour", "hora"),
        ("minutes ago", "minutos atrás"), ("minute ago", "minuto atrás"),
        ("minutes", "minutos"), ("minute", "minuto"),
        ("days ago", "dias atrás"), ("day ago", "dia atrás"),
        ("days", "dias"), ("day", "dia"),
        ("weeks ago", "semanas atrás"), ("week ago", "semana atrás"),
        ("ago", "atrás"), ("yesterday", "ontem"), ("today", "hoje")
    ]
    
    for ing, pt in substituicoes:
        texto = texto.replace(ing, pt)
    
    return texto.strip().capitalize()

def converter_data_para_ordenacao(data_str):
    if not data_str:
        return datetime.min
    try:
        dt_utc = parsedate_to_datetime(str(data_str).strip())
        if dt_utc:
            return dt_utc
    except:
        pass
    return datetime.min

def buscar_noticias():
    data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')
    data_hoje = datetime.now().strftime('%Y-%m-%d')

    print(f"Iniciando varredura com triagem semântica - {data_execucao}\n" + "=" * 50)

    if not google_news:
        print("Erro crítico: GNews não foi carregado corretamente.")
        return

    dados_existentes_hoje = {}
    if os.path.exists('noticias_atualizadas.json'):
        try:
            with open('noticias_atualizadas.json', 'r', encoding='utf-8') as f:
                dados_existentes_hoje = json.load(f)
        except:
            dados_existentes_hoje = {}

    links_processados = set()
    for tema, noticias in dados_existentes_hoje.items():
        if isinstance(noticias, list):
            for n in noticias:
                if 'link' in n:
                    links_processados.add(n['link'])

    relatorio_geral = {}

    for tema in TEMAS_BUSCA:
        print(f"Pesquisando: {tema}...")
        try:
            artigos = google_news.get_news(tema)
            
            noticias_tema = []
            if tema in dados_existentes_hoje and isinstance(dados_existentes_hoje[tema], list):
                noticias_tema = list(dados_existentes_hoje[tema])

            if artigos:
                for artigo in artigos:
                    link = artigo.get('url', '#')
                    
                    if link in links_processados:
                        continue

                    titulo = artigo.get('title', 'Sem Título')
                    descricao = artigo.get('description', '')
                    resumo = descricao if descricao else f"Notícia referente a {tema}."

                    # Validação semântica e estrutural
                    if not validar_relevancia_noticia(titulo, resumo, link):
                        continue

                    links_processados.add(link)
                    fonte = artigo.get('publisher', {}).get('title', 'Fonte Desconhecida')
                    data_crua = artigo.get('published date', '')
                    data_pub = formatar_data_brasil(data_crua)

                    noticias_tema.append({
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': data_pub,
                        'data_original': str(data_crua),
                        'fonte': fonte,
                        'link': link
                    })

            if noticias_tema and isinstance(noticias_tema, list):
                noticias_tema.sort(key=lambda x: converter_data_para_ordenacao(x.get('data_original')), reverse=True)
                relatorio_geral[tema] = noticias_tema
            else:
                relatorio_geral[tema] = "Sem atualizações relevantes nas últimas 24h."

        except Exception as e:
            print(f"Erro ao buscar o tema \"{tema}\": {e}")
            if tema in dados_existentes_hoje:
                relatorio_geral[tema] = dados_existentes_hoje[tema]
            else:
                relatorio_geral[tema] = "Sem atualizações relevantes nas últimas 24h."

    with open('noticias_atualizadas.json', 'w', encoding='utf-8') as f:
        json.dump(relatorio_geral, f, ensure_ascii=False, indent=4)

    historico = {}
    if os.path.exists('historico_geral.json'):
        try:
            with open('historico_geral.json', 'r', encoding='utf-8') as f:
                historico = json.load(f)
        except:
            historico = {}

    historico[data_hoje] = relatorio_geral

    with open('historico_geral.json', 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

    print("\nVarredura concluída com sucesso!")

if __name__ == '__main__':
    buscar_noticias()
