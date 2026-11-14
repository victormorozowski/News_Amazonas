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

# Categorias dedicadas e mutuamente exclusivas da Polícia Federal
CAT_PF_AMAZONAS = "Polícia Federal - Amazonas"
CAT_PF_BRASIL = "Polícia Federal - Brasil"
CATEGORIA_FRONTEIRAS = "Fronteiras, narcotráfico e guerrilhas nos países limítrofes do Amazonas"

BUSCAS_PF_AMAZONAS = [
    "Polícia Federal Amazonas",
    "Superintendência Polícia Federal Amazonas",
    "Superintendente da Polícia Federal no Amazonas Danielle Mady",
    "Operações Polícia Federal Amazonas",
    "Polícia Federal Manaus"
]

BUSCAS_PF_BRASIL = [
    "Polícia Federal operação",
    "Polícia Federal investigação",
    "Polícia Federal prisão",
    "Polícia Federal STF",
    "Polícia Federal apreensão"
]

# Demais temas regionais do Amazonas
TEMAS_BUSCA_AM = [
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
    "Órgãos Federais Amazonas"
]

# Buscas ocultas direcionadas para fronteiras e países limítrofes
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
    "site:cm7brasil.com polícia federal",
    "site:cm7brasil.com operação",
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

# Buscas nacionais abertas para não ignorar outros portais relevantes
BUSCAS_NACIONAIS_ABERTAS = [
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
    "urucurituba", "amazonas", "alto solimões", "rio negro", "rio solimões",
    "vale do javari"
]

OUTROS_ESTADOS_CAPITAIS = [
    "salvador", "bahia", "mato grosso", "cuiabá", "mato grosso do sul", "campo grande",
    "rio de janeiro", "são paulo", "minas gerais", "belo horizonte", "paraná", "curitiba",
    "santa catarina", "florianópolis", "rio grande do sul", "porto alegre", "pernambuco",
    "recife", "ceará", "fortaleza", "pará", "belém", "santarém", "acre", "rio branco",
    "rondônia", "porto velho", "roraima", "boa vista", "amapá", "macapá", "tocantins",
    "palmas", "goiás", "goiânia", "maranhão", "são luís", "piauí", "teresina",
    "paraíba", "joão pessoa", "rio grande do norte", "natal", "alagoas", "maceió",
    "sergipe", "aracaju", "espírito santo", "vitória", "brasília", "distrito federal"
]

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

CERNE_FRONTEIRA = CERNE_REGIONAL + [
    "guerrilha", "guerrilheiro", "guerrilheiros", "farc", "eln", "sendero luminoso",
    "tren de aragua", "dissidentes", "cartel", "narcotráfico", "narcotraficante",
    "narco", "contrabando", "descaminho", "exército", "forças armadas", "soberania",
    "migração", "refugiados", "paramilitar", "armamento", "fuzil", "munição"
]

CERNE_NACIONAL = CERNE_REGIONAL + [
    "stf", "supremo", "stj", "tse", "congresso", "senado", "câmara dos deputados",
    "planalto", "presidente", "ministro", "ministério", "economia", "inflação",
    "selic", "juros", "dólar", "pib", "receita federal", "banco central", "orçamento",
    "imposto", "tributária", "reforma", "eleição", "eleições", "eleitoral", "inss",
    "sus", "saúde pública", "infraestrutura", "energia", "petrobras", "amazônia",
    "diplomacia", "onu"
]

PAISES_LIMITROFES_E_FRONTEIRA = [
    "colômbia", "colombia", "peru", "venezuela", "tríplice fronteira", "fronteira",
    "letícia", "leticia", "santa rosa", "iquitos", "loreto", "putumayo", "vaupés",
    "guainía", "tabatinga", "benjamin constant", "atalaia do norte",
    "são gabriel da cachoeira", "santo antônio do içá", "japurá", "javari",
    "alto solimões", "alto rio negro", "cabeça do cachorro"
]

URLS_BLOQUEADAS = [
    "/esporte", "/esportes", "/futebol", "/ge/", "/lance", "/famosos", "/celebridades",
    "/gshow", "/splash", "/entretenimento", "/tv-e-famosos", "/novelas", "/cinema",
    "/musica", "/horoscopo", "/vida-e-estilo", "/delas", "/leo-dias", "/cultura",
    "/receitas", "/turismo", "/moda", "/beleza", "/autos", "/games"
]

TERMOS_RUIDO = [
    "vestibular", "biblioteca", "escola municipal", "ensino fundamental",
    "educação inclusiva", "formatura", "teatro", "exposição cultural",
    "campeonato municipal", "festa de", "concurso público municipal",
    "matrícula escolar", "merenda escolar", "atração musical", "programação cultural",
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


def limpar_titulo_sem_fonte(titulo):
    """Remove o sufixo ' - Nome do Portal' adicionado pelo Google News para não falsificar filtro geográfico."""
    if not titulo:
        return ""
    partes = titulo.rsplit(" - ", 1)
    if len(partes) == 2 and len(partes[1]) <= 45:
        return partes[0].strip()
    return titulo.strip()


def eh_ruido_absoluto(titulo, resumo, link):
    texto = f"{titulo} {resumo}".lower()
    link_lower = link.lower()

    if any(slug in link_lower for slug in URLS_BLOQUEADAS):
        return True

    if any(ruido in texto for ruido in TERMOS_RUIDO):
        return True

    titulo_limpo = limpar_titulo_sem_fonte(titulo).lower()
    if re.search(r'\b[a-záéíóúâêôãõç]+\s+x\s+[a-záéíóúâêôãõç]+\b', titulo_limpo):
        return True

    return False


def tem_mencao_pf(texto):
    texto_low = texto.lower()
    termos_pf = [
        "polícia federal", "policia federal",
        "superintendência regional da polícia federal",
        "superintendente da polícia federal",
        "danielle mady", "delegado federal", "delegada federal",
        "agentes federais", "inquérito da pf", "operação da pf",
        "ação da pf", "prisão pela pf", "investigação da pf",
        "indiciados pela pf", "indiciado pela pf", "pf deflagra",
        "pf prende", "pf apreende", "pf investiga", "pf mira", "pf faz"
    ]
    if any(t in texto_low for t in termos_pf):
        return True
    if re.search(r'\bpf\b', texto_low):
        return True
    return False


def tem_vinculo_amazonas(titulo, resumo):
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto_analise = f"{titulo_limpo} {resumo}".lower()
    return any(re.search(rf'\b{re.escape(mun)}\b', texto_analise) for mun in MUNICIPIOS_AM)


def validar_pf_amazonas(titulo, resumo, link):
    """Aceita APENAS atuação da Polícia Federal dentro do Amazonas."""
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}"

    if not tem_mencao_pf(texto):
        return False

    return tem_vinculo_amazonas(titulo, resumo)


def validar_pf_brasil(titulo, resumo, link):
    """Aceita APENAS atuação da Polícia Federal no restante do Brasil (exclui Amazonas)."""
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}"
    texto_low = texto.lower()

    if not tem_mencao_pf(texto):
        return False

    # Exclusão estrita: se envolver o Amazonas, vai apenas para 'Polícia Federal - Amazonas'
    if tem_vinculo_amazonas(titulo, resumo):
        return False

    # Exclui polícias federais estrangeiras sem relação com o Brasil
    estrangeiras = ["polícia federal argentina", "polícia federal da argentina", "polícia federal mexicana", "polícia federal do méxico"]
    if any(est in texto_low for est in estrangeiras):
        return False

    return True


def validar_noticia_regional(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()

    if not any(cerne in texto for cerne in CERNE_REGIONAL):
        return False

    tem_am = tem_vinculo_amazonas(titulo, resumo)
    cita_outro_estado = any(re.search(rf'\b{re.escape(est)}\b', texto) for est in OUTROS_ESTADOS_CAPITAIS)

    if cita_outro_estado and not tem_am:
        return False

    return True


def validar_noticia_fronteira(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()

    tem_fronteira_ou_pais = any(loc in texto for loc in PAISES_LIMITROFES_E_FRONTEIRA)
    if not tem_fronteira_ou_pais:
        return False

    return any(cerne in texto for cerne in CERNE_FRONTEIRA)


def validar_noticia_nacional(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False

    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()
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
    def chave_ordenacao(noticia):
        dt = converter_data_para_ordenacao(noticia.get('data_original'))
        bloco_tempo = int(dt.timestamp() // (6 * 3600)) if dt != datetime.min else 0
        prioridade = 1 if eh_fonte_prioritaria(noticia) else 0
        return (bloco_tempo, prioridade, dt)

    lista_noticias.sort(key=chave_ordenacao, reverse=True)
    return lista_noticias


def normalizar_titulo_dedup(titulo):
    base = limpar_titulo_sem_fonte(titulo).lower()
    return re.sub(r'[^a-z0-9]', '', base)[:60]


def buscar_noticias():
    if not google_news:
        return

    dados_existentes = {}
    if os.path.exists('noticias_atualizadas.json'):
        try:
            with open('noticias_atualizadas.json', 'r', encoding='utf-8') as f:
                dados_existentes = json.load(f)
        except Exception:
            pass

    # Migra notícias antigas de PF para as novas categorias separadas e remove abas obsoletas
    abas_pf_antigas = [
        "Polícia Federal Amazonas",
        "Superintendência Polícia Federal Amazonas",
        "Superintendente da Polícia Federal no Amazonas Danielle Mady",
        "Operações Polícia Federal Amazonas"
    ]
    antigas_pf = []
    for aba_antiga in abas_pf_antigas:
        itens = dados_existentes.pop(aba_antiga, [])
        if isinstance(itens, list):
            antigas_pf.extend(itens)

    dados_existentes.pop("site:cm7brasil.com polícia", None)
    dados_existentes.pop("site:cm7brasil.com amazonas", None)

    if not isinstance(dados_existentes.get(CAT_PF_AMAZONAS), list):
        dados_existentes[CAT_PF_AMAZONAS] = []
    if not isinstance(dados_existentes.get(CAT_PF_BRASIL), list):
        dados_existentes[CAT_PF_BRASIL] = []

    for item in antigas_pf:
        t, r, l = item.get('titulo', ''), item.get('resumo', ''), item.get('link', '')
        if validar_pf_amazonas(t, r, l):
            dados_existentes[CAT_PF_AMAZONAS].append(item)
        elif validar_pf_brasil(t, r, l):
            dados_existentes[CAT_PF_BRASIL].append(item)

    # Controle de duplicidade por categoria (permite que a mesma notícia esteja em PF-Brasil e Principais Notícias do Brasil, mas NUNCA em PF-AM e PF-BR juntas)
    links_pf_global = set()
    titulos_pf_global = set()

    for cat_pf, validador in [(CAT_PF_AMAZONAS, validar_pf_amazonas), (CAT_PF_BRASIL, validar_pf_brasil)]:
        limpas = []
        for n in dados_existentes.get(cat_pf, []):
            l, t, r = n.get('link', ''), n.get('titulo', ''), n.get('resumo', '')
            chave_t = normalizar_titulo_dedup(t)
            if validador(t, r, l) and l not in links_pf_global and chave_t not in titulos_pf_global:
                links_pf_global.add(l)
                titulos_pf_global.add(chave_t)
                limpas.append(n)
        dados_existentes[cat_pf] = limpas

    relatorio_geral = {}

    # 1. Polícia Federal - Amazonas (Estritamente Amazonas)
    noticias_pf_am = list(dados_existentes[CAT_PF_AMAZONAS])
    for termo_pf_am in BUSCAS_PF_AMAZONAS:
        try:
            artigos = google_news.get_news(termo_pf_am)
            if artigos:
                for artigo in artigos:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Atuação da Polícia Federal no Amazonas."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_pf_global or chave_tit in titulos_pf_global:
                        continue
                    if not validar_pf_amazonas(titulo, resumo, link):
                        continue

                    links_pf_global.add(link)
                    titulos_pf_global.add(chave_tit)
                    noticias_pf_am.append({
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Fonte'),
                        'link': link
                    })
        except Exception:
            pass

    relatorio_geral[CAT_PF_AMAZONAS] = ordenar_com_prioridade(noticias_pf_am) if noticias_pf_am else "Sem atualizações relevantes da PF no Amazonas nas últimas 24h."

    # 2. Polícia Federal - Brasil (Estritamente fora do Amazonas)
    noticias_pf_br = list(dados_existentes[CAT_PF_BRASIL])
    for termo_pf_br in BUSCAS_PF_BRASIL:
        try:
            artigos = google_news.get_news(termo_pf_br)
            if artigos:
                for artigo in artigos:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Atuação nacional da Polícia Federal."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_pf_global or chave_tit in titulos_pf_global:
                        continue
                    if not validar_pf_brasil(titulo, resumo, link):
                        continue

                    links_pf_global.add(link)
                    titulos_pf_global.add(chave_tit)
                    noticias_pf_br.append({
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Fonte'),
                        'link': link
                    })
        except Exception:
            pass

    relatorio_geral[CAT_PF_BRASIL] = ordenar_com_prioridade(noticias_pf_br) if noticias_pf_br else "Sem atualizações relevantes da PF no restante do país nas últimas 24h."

    # 3. Fronteiras, narcotráfico e guerrilhas nos países limítrofes do Amazonas
    links_fronteira = set()
    titulos_fronteira = set()
    noticias_fronteira = []
    if isinstance(dados_existentes.get(CATEGORIA_FRONTEIRAS), list):
        for n in dados_existentes[CATEGORIA_FRONTEIRAS]:
            l, t, r = n.get('link', ''), n.get('titulo', ''), n.get('resumo', '')
            chave_t = normalizar_titulo_dedup(t)
            if validar_noticia_fronteira(t, r, l) and l not in links_fronteira and chave_t not in titulos_fronteira:
                links_fronteira.add(l)
                titulos_fronteira.add(chave_t)
                noticias_fronteira.append(n)

    for termo_fronteira in BUSCAS_FRONTEIRAS:
        try:
            artigos_front = google_news.get_news(termo_fronteira)
            if artigos_front:
                for artigo in artigos_front:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Monitoramento de fronteira e países limítrofes."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_fronteira or chave_tit in titulos_fronteira:
                        continue
                    if not validar_noticia_fronteira(titulo, resumo, link):
                        continue

                    links_fronteira.add(link)
                    titulos_fronteira.add(chave_tit)
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

    relatorio_geral[CATEGORIA_FRONTEIRAS] = ordenar_com_prioridade(noticias_fronteira) if noticias_fronteira else "Sem atualizações relevantes nas últimas 24h."

    # 4. Demais Temas Regionais do Amazonas
    links_regionais = set(links_pf_global)
    titulos_regionais = set(titulos_pf_global)

    for tema in TEMAS_BUSCA_AM:
        noticias_tema = []
        if isinstance(dados_existentes.get(tema), list):
            for n in dados_existentes[tema]:
                l, t, r = n.get('link', ''), n.get('titulo', ''), n.get('resumo', '')
                chave_t = normalizar_titulo_dedup(t)
                if validar_noticia_regional(t, r, l) and l not in links_regionais and chave_t not in titulos_regionais:
                    links_regionais.add(l)
                    titulos_regionais.add(chave_t)
                    noticias_tema.append(n)

        try:
            artigos = google_news.get_news(tema)
            if artigos:
                for artigo in artigos:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or f"Notícia referente a {tema}."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_regionais or chave_tit in titulos_regionais:
                        continue
                    if not validar_noticia_regional(titulo, resumo, link):
                        continue

                    links_regionais.add(link)
                    titulos_regionais.add(chave_tit)
                    noticias_tema.append({
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Fonte'),
                        'link': link
                    })
        except Exception:
            pass

        relatorio_geral[tema] = ordenar_com_prioridade(noticias_tema) if noticias_tema else "Sem atualizações relevantes nas últimas 24h."

    # 5. Varredura Oculta e Prioritária no CM7 (roteada com precisão para a aba correta)
    for busca_cm7 in BUSCAS_OCULTAS_CM7:
        try:
            artigos_cm7 = google_news.get_news(busca_cm7)
            if artigos_cm7:
                for artigo in artigos_cm7:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Notícia CM7."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    noticia_obj = {
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'CM7 Brasil'),
                        'link': link
                    }

                    # Roteamento estrito de PF (Amazonas vs Brasil)
                    if validar_pf_amazonas(titulo, resumo, link):
                        if link not in links_pf_global and chave_tit not in titulos_pf_global:
                            links_pf_global.add(link)
                            titulos_pf_global.add(chave_tit)
                            if not isinstance(relatorio_geral.get(CAT_PF_AMAZONAS), list):
                                relatorio_geral[CAT_PF_AMAZONAS] = []
                            relatorio_geral[CAT_PF_AMAZONAS].append(noticia_obj)
                            relatorio_geral[CAT_PF_AMAZONAS] = ordenar_com_prioridade(relatorio_geral[CAT_PF_AMAZONAS])
                        continue

                    if validar_pf_brasil(titulo, resumo, link):
                        if link not in links_pf_global and chave_tit not in titulos_pf_global:
                            links_pf_global.add(link)
                            titulos_pf_global.add(chave_tit)
                            if not isinstance(relatorio_geral.get(CAT_PF_BRASIL), list):
                                relatorio_geral[CAT_PF_BRASIL] = []
                            relatorio_geral[CAT_PF_BRASIL].append(noticia_obj)
                            relatorio_geral[CAT_PF_BRASIL] = ordenar_com_prioridade(relatorio_geral[CAT_PF_BRASIL])
                        continue

                    if link in links_regionais or chave_tit in titulos_regionais:
                        continue
                    if not validar_noticia_regional(titulo, resumo, link):
                        continue

                    links_regionais.add(link)
                    titulos_regionais.add(chave_tit)
                    texto_comb = f"{limpar_titulo_sem_fonte(titulo)} {resumo}".lower()
                    aba_destino = "Tráfico de drogas Amazonas" if any(p in texto_comb for p in ["droga", "entorpecente", "cocaína", "maconha", "skunk", "tráfico"]) else "Segurança Pública Amazonas"

                    if not isinstance(relatorio_geral.get(aba_destino), list):
                        relatorio_geral[aba_destino] = []
                    relatorio_geral[aba_destino].append(noticia_obj)
                    relatorio_geral[aba_destino] = ordenar_com_prioridade(relatorio_geral[aba_destino])
        except Exception:
            pass

    # 6. Varredura Nacional: Portais Prioritários + Buscas Abertas
    links_nacionais = set()
    titulos_nacionais = set()
    noticias_brasil = []

    if isinstance(dados_existentes.get("Principais Notícias do Brasil"), list):
        for n in dados_existentes["Principais Notícias do Brasil"]:
            l, t, r = n.get('link', ''), n.get('titulo', ''), n.get('resumo', '')
            chave_t = normalizar_titulo_dedup(t)
            if validar_noticia_nacional(t, r, l) and l not in links_nacionais and chave_t not in titulos_nacionais:
                links_nacionais.add(l)
                titulos_nacionais.add(chave_t)
                noticias_brasil.append(n)

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

                    if not validar_noticia_nacional(titulo, resumo, link):
                        continue

                    noticia_obj = {
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Portal'),
                        'link': link
                    }

                    # Roteia notícias da PF capturadas nos portais nacionais para a aba PF correta (sem misturar)
                    if validar_pf_amazonas(titulo, resumo, link):
                        if link not in links_pf_global and chave_tit not in titulos_pf_global:
                            links_pf_global.add(link)
                            titulos_pf_global.add(chave_tit)
                            if not isinstance(relatorio_geral.get(CAT_PF_AMAZONAS), list):
                                relatorio_geral[CAT_PF_AMAZONAS] = []
                            relatorio_geral[CAT_PF_AMAZONAS].append(noticia_obj)
                            relatorio_geral[CAT_PF_AMAZONAS] = ordenar_com_prioridade(relatorio_geral[CAT_PF_AMAZONAS])
                    elif validar_pf_brasil(titulo, resumo, link):
                        if link not in links_pf_global and chave_tit not in titulos_pf_global:
                            links_pf_global.add(link)
                            titulos_pf_global.add(chave_tit)
                            if not isinstance(relatorio_geral.get(CAT_PF_BRASIL), list):
                                relatorio_geral[CAT_PF_BRASIL] = []
                            relatorio_geral[CAT_PF_BRASIL].append(noticia_obj)
                            relatorio_geral[CAT_PF_BRASIL] = ordenar_com_prioridade(relatorio_geral[CAT_PF_BRASIL])

                    # Duplica para Fronteiras se citar países limítrofes com narcotráfico/guerrilha
                    if validar_noticia_fronteira(titulo, resumo, link):
                        if link not in links_fronteira and chave_tit not in titulos_fronteira:
                            links_fronteira.add(link)
                            titulos_fronteira.add(chave_tit)
                            if not isinstance(relatorio_geral.get(CATEGORIA_FRONTEIRAS), list):
                                relatorio_geral[CATEGORIA_FRONTEIRAS] = []
                            relatorio_geral[CATEGORIA_FRONTEIRAS].append(noticia_obj)
                            relatorio_geral[CATEGORIA_FRONTEIRAS] = ordenar_com_prioridade(relatorio_geral[CATEGORIA_FRONTEIRAS])

                    # Duplica para Segurança Pública Amazonas se citar Manaus/AM
                    if tem_vinculo_amazonas(titulo, resumo) and validar_noticia_regional(titulo, resumo, link):
                        if link not in links_regionais and chave_tit not in titulos_regionais:
                            links_regionais.add(link)
                            titulos_regionais.add(chave_tit)
                            if not isinstance(relatorio_geral.get("Segurança Pública Amazonas"), list):
                                relatorio_geral["Segurança Pública Amazonas"] = []
                            relatorio_geral["Segurança Pública Amazonas"].append(noticia_obj)
                            relatorio_geral["Segurança Pública Amazonas"] = ordenar_com_prioridade(relatorio_geral["Segurança Pública Amazonas"])

                    if link not in links_nacionais and chave_tit not in titulos_nacionais:
                        links_nacionais.add(link)
                        titulos_nacionais.add(chave_tit)
                        noticias_brasil.append(noticia_obj)
                        contador += 1
        except Exception:
            pass

    relatorio_geral["Principais Notícias do Brasil"] = ordenar_com_prioridade(noticias_brasil) if noticias_brasil else "Sem atualizações válidas."

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
