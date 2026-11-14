from datetime import datetime, timedelta
import json
import os
import re
from email.utils import parsedate_to_datetime

try:
    from gnews import GNews
    google_news = GNews(language='pt', country='BR', period='1d', max_results=12)
except Exception as e:
    print(f"Aviso ao inicializar GNews: {e}")
    google_news = None

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
    "Mandado de prisão Polícia Amazonas",
    "Operação policial Amazonas",
    "Pirataria fluvial Amazonas",
    "Investigação política Amazonas",
    "Polícia Civil Amazonas",
    "Polícia Militar Amazonas",
    "Operações Polícia Federal Amazonas",
    "Órgãos Federais Amazonas"
]

CATEGORIA_FRONTEIRAS = "Fronteiras, narcotráfico e guerrilhas nos países limítrofes do Amazonas"

# Buscas ocultas direcionadas para alimentar a categoria de fronteiras e países limítrofes
BUSCAS_FRONTEIRAS = [
    "narcotráfico fronteira Colômbia Peru Venezuela Amazonas",
    "guerrilha FARC ELN fronteira Brasil Amazonas",
    "tríplice fronteira Tabatinga Colômbia Peru tráfico",
    "fronteira Venezuela Amazonas crime guerrilha garimpo",
    "Sendero Luminoso Tren de Aragua fronteira Brasil"
]

# Buscas ocultas para reforçar atenção ao CM7 sem criar aba própria
BUSCAS_OCULTAS_CM7 = [
    "site:cm7brasil.com polícia",
    "site:cm7brasil.com operação",
    "site:cm7brasil.com prisão",
    "site:cm7brasil.com amazonas"
]

# Portais prioritários (recebem busca dedicada + prioridade na ordenação)
DOMINIOS_PRIORITARIOS = [
    "cm7brasil.com",
    "g1.globo.com",
    "uol.com.br",
    "r7.com",
    "metropoles.com",
    "cnnbrasil.com.br"
]

NOMES_FONTES_PRIORITARIAS = [
    "cm7", "g1", "uol", "r7", "metrópoles", "metropoles", "cnn"
]

FONTES_NACIONAIS_PRIORITARIAS = [
    {"nome": "G1", "termo": "site:g1.globo.com política OR polícia OR economia OR justiça"},
    {"nome": "UOL", "termo": "site:uol.com.br política OR polícia OR economia OR justiça"},
    {"nome": "R7", "termo": "site:r7.com política OR polícia OR economia OR justiça"},
    {"nome": "Metrópoles", "termo": "site:metropoles.com política OR polícia OR economia OR justiça"},
    {"nome": "CNN Brasil", "termo": "site:cnnbrasil.com.br política OR polícia OR economia OR justiça"}
]

# Buscas nacionais abertas para não ignorar outros portais relevantes (Folha, Estadão, Poder360, Agência Brasil, etc.)
BUSCAS_NACIONAIS_ABERTAS = [
    "Polícia Federal operação Brasil",
    "STF Supremo Justiça decisão Brasil",
    "Política Governo Congresso Brasil",
    "Economia Banco Central Receita Federal Brasil"
]

MUNICIPIOS_AM = [
    "alvarães", "amaturá", "anamã", "anori", "apuí", "atalaia do norte", "autazes",
    "barcelos", "barreirinha", "benjamin constant", "beruri", "boa vista do ramos",
    "boca do acre", "borba", "caapiranga", "canutama", "carauari", "careiro",
    "careiro da várzea", "coari", "codajás", "eirunepé", "envira", "fonte boa",
    "guajará", "humaitá", "ipixuna", "iranduba", "itacoatiara", "itamarati",
    "itapiranga", "japurá", "juruá", "jutaí", "lábrea", "manacapuru", "manaquiri",
    "manaú", "manaus", "manicoré", "maraã", "maués", "nhamundá", "nova olinda do norte",
    "novo airão", "novo aripuanã", "parintins", "pauini", "presidente figueiredo",
    "rio preto da eva", "santa isabel do rio negro", "santo antônio do içá",
    "são gabriel da cachoeira", "são paulo de olivença", "são sebastião do uatumã",
    "silves", "tabatinga", "tapauá", "tefé", "tonantins", "uarini", "urucará",
    "urucurituba", "amazonas", "alto solimões", "rio negro", "rio solimões"
]

PAISES_LIMITROFES_E_FRONTEIRA = [
    "colômbia", "colombia", "peru", "venezuela", "tríplice fronteira", "fronteira",
    "letícia", "leticia", "santa rosa", "iquitos", "loreto", "putumayo", "vaupés",
    "guainía", "tabatinga", "benjamin constant", "atalaia do norte",
    "são gabriel da cachoeira", "santo antônio do içá", "japurá", "javari",
    "alto solimões", "alto rio negro", "cabeça do cachorro"
]

OUTROS_ESTADOS_CAPITAIS = [
    "salvador", "bahia", "mato grosso", "cuiabá", "mato grosso do sul", "campo grande",
    "rio de janeiro", "são paulo", "minas gerais", "belo horizonte", "paraná", "curitiba",
    "santa catarina", "florianópolis", "rio grande do sul", "porto alegre", "pernambuco",
    "recife", "ceará", "fortaleza", "pará", "belém", "santarém", "acre", "rio branco",
    "rondônia", "porto velho", "roraima", "boa vista", "amapá", "macapá", "tocantins",
    "palmas", "goiás", "goiânia", "maranhão", "são luís", "piauí", "teresina",
    "paraíba", "joão pessoa", "rio grande do norte", "natal", "alagoas", "maceió",
    "sergipe", "aracaju", "espírito santo", "vitória"
]

# Núcleo obrigatório para abas do Amazonas
CERNE_REGIONAL = [
    "polícia", "policial", "delegado", "delegada", "pf", "prf", "federal", "civil",
    "militar", "operação", "investigação", "investigado", "prisão", "preso", "presa",
    "apreensão", "apreendido", "droga", "drogas", "entorpecente", "cocaína", "maconha",
    "skunk", "tráfico", "traficante", "facção", "comando vermelho", "pcc", "crime",
    "criminoso", "homicídio", "assassinato", "tiroteio", "baleado", "assalto", "roubo",
    "sequestro", "golpe", "estelionato", "fraude", "corrupção", "desvio", "garimpo",
    "ouro", "desmatamento", "queimada", "ambiental", "ibama", "icmbio", "funai",
    "indígena", "pirataria", "fluvial", "embarcação", "fronteira", "justiça",
    "ministério público", "mpf", "mpam", "tjam", "tre-am", "juiz", "desembargador",
    "governo", "prefeitura", "prefeito", "governador", "deputado", "senador", "vereador",
    "aleam", "tce", "tcu", "cgu", "corregedoria", "segurança", "ssp", "danielle mady"
]

# Núcleo específico para fronteiras, narcotráfico e guerrilhas nos países limítrofes
CERNE_FRONTEIRA = CERNE_REGIONAL + [
    "guerrilha", "guerrilheiro", "guerrilheiros", "farc", "eln", "sendero luminoso",
    "tren de aragua", "dissidentes", "cartel", "narcotráfico", "narcotraficante",
    "narco", "contrabando", "descaminho", "exército", "forças armadas", "soberania",
    "migração", "refugiados", "paramilitar", "armamento", "fuzil", "munição"
]

# Núcleo obrigatório para a aba nacional (impede fofocas, lifestyle e matérias aleatórias)
CERNE_NACIONAL = CERNE_REGIONAL + [
    "stf", "supremo", "stj", "tse", "congresso", "senado", "câmara dos deputados",
    "planalto", "presidente", "ministro", "ministério", "economia", "inflação",
    "selic", "juros", "dólar", "pib", "receita federal", "banco central", "orçamento",
    "imposto", "tributária", "reforma", "eleição", "eleições", "eleitoral", "inss",
    "sus", "saúde pública", "infraestrutura", "energia", "petrobras", "amazônia",
    "diplomacia", "onu"
]

# Bloqueio absoluto de URLs de entretenimento/esporte
URLS_BLOQUEADAS = [
    "/esporte", "/esportes", "/futebol", "/ge/", "/lance", "/famosos", "/celebridades",
    "/gshow", "/splash", "/entretenimento", "/tv-e-famosos", "/novelas", "/cinema",
    "/musica", "/horoscopo", "/vida-e-estilo", "/delas", "/leo-dias", "/cultura",
    "/receitas", "/turismo", "/moda", "/beleza", "/autos", "/games"
]

# Bloqueio absoluto de palavras de esportes, fofocas, celebridades e ruídos locais
TERMOS_RUIDO = [
    # Ruídos locais
    "vestibular", "biblioteca", "escola municipal", "ensino fundamental",
    "educação inclusiva", "formatura", "teatro", "exposição cultural",
    "campeonato municipal", "festa de", "concurso público municipal",
    "matrícula escolar", "merenda escolar", "atração musical", "programação cultural",
    # Esportes (futebol, clubes, olimpíadas, lutas, transmissões)
    "futebol", "brasileirão", "libertadores", "sul-americana", "copa do brasil",
    "champions league", "premier league", "la liga", "bundesliga", "série a", "série b",
    "série c", "série d", "paulistão", "carioca", "gaúcho", "mineiro", "flamengo",
    "corinthians", "palmeiras", "são paulo fc", "santos fc", "vasco", "botafogo",
    "fluminense", "cruzeiro", "atlético-mg", "grêmio", "internacional", "bahia",
    "fortaleza", "athletico", "manaus fc", "amazonas fc", "princesa do solimões",
    "seleção brasileira", "neymar", "vini jr", "vinicius junior", "messi",
    "cristiano ronaldo", "ancelotti", "dorival", "abel ferreira", "tite", "gabigol",
    "esporte", "esportes", "placar", "goleada", "empate", "escalação", "desfalque",
    "zagueiro", "atacante", "goleiro", "árbitro", "pênalti", "impedimento",
    "cartão vermelho", "campeonato", "torneio", "rodada", "rebaixamento",
    "copa do mundo", "olimpíadas", "paralimpíadas", "medalha", "medalhista", "pódio",
    "ginástica", "trave", "vôlei", "basquete", "nba", "nfl", "tênis", "fórmula 1",
    "gp de", "ufc", "mma", "boxe", "surfe", "skate", "natação", "atletismo",
    "onde assistir", "onde vai passar", "assistir ao vivo", "transmissão ao vivo",
    "barcelona", "real madrid",
    # Fofocas, celebridades, TV e entretenimento
    "fofoca", "fofocas", "celebridade", "celebridades", "famoso", "famosos",
    "famosa", "famosas", "influenciador", "influenciadora", "influencer", "gshow",
    "splash", "leo dias", "fábia oliveira", "fabia oliveira", "sonia abrão",
    "bbb", "big brother", "a fazenda", "reality show", "paredão", "novela",
    "capítulo de", "resumo da novela", "globoplay", "netflix", "prime video",
    "disney+", "bilheteria", "oscar", "grammy", "sertanejo", "pagode", "turnê",
    "rock in rio", "lollapalooza", "virgínia", "virginia fonseca", "zé felipe",
    "anitta", "ludmilla", "luísa sonza", "bruna biancardi", "bruna marquezine",
    "gusttavo lima", "luan santana", "maiara", "maraisa", "simone mendes",
    "ana castela", "jojo todynho", "davi brito", "juliette", "sabrina sato",
    "eliana", "xuxa", "luciano huck", "rodrigo faro", "patrícia poeta",
    "ana maria braga", "mais você", "namoro de", "término de", "separação de",
    "divórcio de", "traição de", "casamento de", "gravidez de", "biquíni",
    "ensaio fotográfico", "viralizou na web", "horóscopo", "signos", "astrologia",
    "receita de", "culinária"
]


def eh_ruido_absoluto(titulo, resumo, link):
    texto = f"{titulo} {resumo}".lower()
    link_lower = link.lower()

    if any(slug in link_lower for slug in URLS_BLOQUEADAS):
        return True

    if any(ruido in texto for ruido in TERMOS_RUIDO):
        return True

    # Bloqueia confrontos esportivos no padrão "Time A x Time B"
    if re.search(r'\b[a-záéíóúâêôãõç]+\s+x\s+[a-záéíóúâêôãõç]+\b', titulo.lower()):
        return True

    return False


def validar_noticia_regional(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    texto = f"{titulo} {resumo}".lower()

    # Precisa ter obrigatoriamente palavra-chave do núcleo temático (inclusive CM7!)
    if not any(cerne in texto for cerne in CERNE_REGIONAL):
        return False

    tem_am = any(mun in texto for mun in MUNICIPIOS_AM)

    # Evita notícias de outros estados republicadas por portais locais (ex: "em Salvador", "em Mato Grosso")
    cita_outro_estado = any(est in texto for est in OUTROS_ESTADOS_CAPITAIS)
    if cita_outro_estado and not tem_am:
        return False

    return True


def validar_noticia_fronteira(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    texto = f"{titulo} {resumo}".lower()

    # Precisa citar país limítrofe (Colômbia, Peru, Venezuela) ou região de fronteira do AM
    tem_fronteira_ou_pais = any(loc in texto for loc in PAISES_LIMITROFES_E_FRONTEIRA)
    if not tem_fronteira_ou_pais:
        return False

    # Precisa estar dentro do escopo de segurança, narcotráfico ou guerrilhas
    return any(cerne in texto for cerne in CERNE_FRONTEIRA)


def validar_noticia_nacional(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    texto = f"{titulo} {resumo}".lower()

    # Exige relevância pública/nacional (bloqueia fofocas novas e matérias irrelevantes)
    return any(cerne in texto for cerne in CERNE_NACIONAL)


def eh_fonte_prioritaria(noticia_obj):
    link = noticia_obj.get('link', '').lower()
    fonte = noticia_obj.get('fonte', '').lower()
    if any(dom in link for dom in DOMINIOS_PRIORITARIOS):
        return True
    if any(nome in fonte for nome in NOMES_FONTES_PRIORITARIAS):
        return True
    return False


def formatar_data_brasil(data_str):
    if not data_str:
        return "Data não informada"
    str_val = str(data_str).strip()
    try:
        dt_utc = parsedate_to_datetime(str_val)
        if dt_utc:
            return (dt_utc - timedelta(hours=4)).strftime('%d/%m/%Y às %H:%M (GMT-4 Manaus)')
    except Exception:
        pass
    return str_val


def converter_data_para_ordenacao(data_str):
    if not data_str:
        return datetime.min
    try:
        dt_utc = parsedate_to_datetime(str(data_str).strip())
        if dt_utc:
            return dt_utc.replace(tzinfo=None)
    except Exception:
        pass
    return datetime.min


def ordenar_com_prioridade(lista_noticias):
    """
    Ordena mantendo notícias mais recentes primeiro (agrupadas por bloco de 6 horas),
    mas dando prioridade no topo dentro do mesmo bloco aos portais preferenciais
    (CM7, G1, UOL, R7, Metrópoles, CNN) sem excluir outros portais.
    """
    def chave_ordenacao(noticia):
        dt = converter_data_para_ordenacao(noticia.get('data_original'))
        bloco_tempo = int(dt.timestamp() // (6 * 3600)) if dt != datetime.min else 0
        prioridade = 1 if eh_fonte_prioritaria(noticia) else 0
        return (bloco_tempo, prioridade, dt)

    lista_noticias.sort(key=chave_ordenacao, reverse=True)
    return lista_noticias


def normalizar_titulo_dedup(titulo):
    base = titulo.split(" - ")[0].lower().strip()
    return re.sub(r'[^a-z0-9]', '', base)[:60]


def buscar_noticias():
    if not google_news:
        return

    dados_existentes = {}
    if os.path.exists('noticias_atualizadas.json'):
        try:
            with open('noticias_atualizadas.json', 'r', encoding='utf-8') as f:
                dados_existentes = json.load(f)
                dados_existentes.pop("site:cm7brasil.com polícia", None)
                dados_existentes.pop("site:cm7brasil.com amazonas", None)
        except Exception:
            pass

    links_processados = set()
    titulos_processados = set()

    # Revalida dados existentes para purgar qualquer ruído antigo que tenha sobrado
    for tema, noticias in list(dados_existentes.items()):
        if isinstance(noticias, list):
            limpas = []
            for n in noticias:
                link = n.get('link', '')
                titulo = n.get('titulo', '')
                resumo = n.get('resumo', '')
                if tema == "Principais Notícias do Brasil":
                    valido = validar_noticia_nacional(titulo, resumo, link)
                elif tema == CATEGORIA_FRONTEIRAS:
                    valido = validar_noticia_fronteira(titulo, resumo, link)
                else:
                    valido = validar_noticia_regional(titulo, resumo, link)

                if valido and link not in links_processados:
                    links_processados.add(link)
                    titulos_processados.add(normalizar_titulo_dedup(titulo))
                    limpas.append(n)
            dados_existentes[tema] = limpas

    relatorio_geral = {}

    # 1. Varredura dos Temas Regionais (aberta a TODOS os sites do Amazonas e do Brasil)
    for tema in TEMAS_BUSCA:
        try:
            artigos = google_news.get_news(tema)
            noticias_tema = list(dados_existentes.get(tema, [])) if isinstance(dados_existentes.get(tema), list) else []
            if artigos:
                for artigo in artigos:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or f"Notícia referente a {tema}."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_processados or chave_tit in titulos_processados:
                        continue
                    if not validar_noticia_regional(titulo, resumo, link):
                        continue

                    links_processados.add(link)
                    titulos_processados.add(chave_tit)
                    noticias_tema.append({
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Fonte'),
                        'link': link
                    })
            if noticias_tema:
                relatorio_geral[tema] = ordenar_com_prioridade(noticias_tema)
            else:
                relatorio_geral[tema] = "Sem atualizações relevantes nas últimas 24h."
        except Exception:
            relatorio_geral[tema] = dados_existentes.get(tema, "Sem atualizações.")

    # 2. Varredura dedicada para Fronteiras, Narcotráfico e Guerrilhas nos Países Limítrofes
    noticias_fronteira = list(dados_existentes.get(CATEGORIA_FRONTEIRAS, [])) if isinstance(dados_existentes.get(CATEGORIA_FRONTEIRAS), list) else []
    for termo_fronteira in BUSCAS_FRONTEIRAS:
        try:
            artigos_front = google_news.get_news(termo_fronteira)
            if artigos_front:
                for artigo in artigos_front:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Monitoramento de fronteira e países limítrofes."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_processados or chave_tit in titulos_processados:
                        continue
                    if not validar_noticia_fronteira(titulo, resumo, link):
                        continue

                    links_processados.add(link)
                    titulos_processados.add(chave_tit)
                    noticias_fronteira.append({
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Fonte'),
                        'link': link
                    })
        except Exception:
            pass

    if noticias_fronteira:
        relatorio_geral[CATEGORIA_FRONTEIRAS] = ordenar_com_prioridade(noticias_fronteira)
    else:
        relatorio_geral[CATEGORIA_FRONTEIRAS] = "Sem atualizações relevantes nas últimas 24h."

    # 3. Varredura Oculta e Prioritária no CM7 (injetada nas abas operacionais)
    for busca_cm7 in BUSCAS_OCULTAS_CM7:
        try:
            artigos_cm7 = google_news.get_news(busca_cm7)
            if artigos_cm7:
                for artigo in artigos_cm7:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Notícia CM7."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_processados or chave_tit in titulos_processados:
                        continue
                    if not (validar_noticia_regional(titulo, resumo, link) or validar_noticia_fronteira(titulo, resumo, link)):
                        continue

                    links_processados.add(link)
                    titulos_processados.add(chave_tit)
                    noticia_obj = {
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'CM7 Brasil'),
                        'link': link
                    }

                    texto_comb = f"{titulo} {resumo}".lower()
                    if validar_noticia_fronteira(titulo, resumo, link) and any(p in texto_comb for p in ["colômbia", "colombia", "peru", "venezuela", "guerrilha", "farc", "eln", "tríplice fronteira"]):
                        aba_destino = CATEGORIA_FRONTEIRAS
                    elif any(p in texto_comb for p in ["droga", "entorpecente", "cocaína", "maconha", "skunk", "tráfico"]):
                        aba_destino = "Tráfico de drogas Amazonas"
                    elif any(p in texto_comb for p in ["polícia federal", "pf ", "danielle mady"]):
                        aba_destino = "Polícia Federal Amazonas"
                    else:
                        aba_destino = "Segurança Pública Amazonas"

                    if not isinstance(relatorio_geral.get(aba_destino), list):
                        relatorio_geral[aba_destino] = []
                    relatorio_geral[aba_destino].append(noticia_obj)
                    relatorio_geral[aba_destino] = ordenar_com_prioridade(relatorio_geral[aba_destino])
        except Exception:
            pass

    # 4. Varredura Nacional: Portais Prioritários + Buscas Abertas (todos os sites)
    noticias_brasil = list(dados_existentes.get("Principais Notícias do Brasil", [])) if isinstance(dados_existentes.get("Principais Notícias do Brasil"), list) else []

    consultas_nacionais = [f["termo"] for f in FONTES_NACIONAIS_PRIORITARIAS] + BUSCAS_NACIONAIS_ABERTAS
    for termo_nac in consultas_nacionais:
        try:
            artigos_portal = google_news.get_news(termo_nac)
            if artigos_portal:
                contador = 0
                for artigo in artigos_portal:
                    if contador >= 5:
                        break
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Destaque nacional."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_processados or chave_tit in titulos_processados:
                        continue
                    if not validar_noticia_nacional(titulo, resumo, link):
                        continue

                    links_processados.add(link)
                    titulos_processados.add(chave_tit)
                    noticia_obj = {
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Portal'),
                        'link': link
                    }

                    texto_analise = f"{titulo} {resumo}".lower()

                    # Duplica para a aba de fronteiras se envolver países limítrofes com narcotráfico/guerrilha
                    if validar_noticia_fronteira(titulo, resumo, link):
                        if not isinstance(relatorio_geral.get(CATEGORIA_FRONTEIRAS), list):
                            relatorio_geral[CATEGORIA_FRONTEIRAS] = []
                        if not any(n.get('link') == link for n in relatorio_geral[CATEGORIA_FRONTEIRAS]):
                            relatorio_geral[CATEGORIA_FRONTEIRAS].append(noticia_obj)
                            relatorio_geral[CATEGORIA_FRONTEIRAS] = ordenar_com_prioridade(relatorio_geral[CATEGORIA_FRONTEIRAS])

                    # Duplica para o Amazonas se citar Manaus ou municípios do AM
                    if any(mun in texto_analise for mun in MUNICIPIOS_AM):
                        if validar_noticia_regional(titulo, resumo, link):
                            aba_reg = "Polícia Federal Amazonas" if "polícia federal" in texto_analise else "Segurança Pública Amazonas"
                            if not isinstance(relatorio_geral.get(aba_reg), list):
                                relatorio_geral[aba_reg] = []
                            if not any(n.get('link') == link for n in relatorio_geral[aba_reg]):
                                relatorio_geral[aba_reg].append(noticia_obj)
                                relatorio_geral[aba_reg] = ordenar_com_prioridade(relatorio_geral[aba_reg])

                    noticias_brasil.append(noticia_obj)
                    contador += 1
        except Exception:
            pass

    if noticias_brasil:
        relatorio_geral["Principais Notícias do Brasil"] = ordenar_com_prioridade(noticias_brasil)
    else:
        relatorio_geral["Principais Notícias do Brasil"] = "Sem atualizações válidas."

    with open('noticias_atualizadas.json', 'w', encoding='utf-8') as f:
        json.dump(relatorio_geral, f, ensure_ascii=False, indent=4)

    historico = {}
    if os.path.exists('historico_geral.json'):
        try:
            with open('historico_geral.json', 'r', encoding='utf-8') as f:
                historico = json.load(f)
        except Exception:
            pass
    historico[datetime.now().strftime('%Y-%m-%d')] = relatorio_geral
    with open('historico_geral.json', 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    buscar_noticias()
