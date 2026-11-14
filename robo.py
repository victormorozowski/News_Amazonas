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

# Categorias principais consolidadas
CAT_PF_AMAZONAS = "Polícia Federal - Amazonas"
CAT_PF_BRASIL = "Polícia Federal - Brasil"
CATEGORIA_FRONTEIRAS = "Fronteiras, narcotráfico e guerrilhas nos países limítrofes do Amazonas"
CAT_TRAFICO_AM = "Tráfico de Drogas - Amazonas"
CAT_SEGURANCA_ESTADUAL_AM = "Segurança Pública Estadual - Amazonas"
CAT_MEIO_AMBIENTE_AM = "Crimes contra o Meio Ambiente - Amazonas"
CAT_POLITICOS_AM = "Investigação Policial envolvendo Políticos - Amazonas"
CAT_NACIONAL = "Principais Notícias do Brasil"

# Categorias remanescentes ainda não fundidas
TEMAS_BUSCA_RESTANTES = [
    "Desmatamento Amazonas",
    "Mandado de prisão Polícia Amazonas",
    "Operação policial Amazonas",
    "Pirataria fluvial Amazonas",
    "Órgãos Federais Amazonas"
]

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

BUSCAS_FRONTEIRAS = [
    "narcotráfico fronteira Colômbia Peru Venezuela Amazonas",
    "guerrilha FARC ELN fronteira Brasil Amazonas",
    "tríplice fronteira Tabatinga Colômbia Peru tráfico",
    "fronteira Venezuela Amazonas crime guerrilha garimpo",
    "Sendero Luminoso Tren de Aragua fronteira Brasil"
]

BUSCAS_TRAFICO_AM = [
    "Tráfico de drogas Amazonas",
    "Apreensão de drogas Amazonas",
    "DENARC Polícia Civil Amazonas drogas",
    "Polícia Militar apreende drogas Manaus Amazonas",
    "apreensão skunk cocaína maconha rio Solimões Amazonas",
    "tráfico de entorpecentes Manaus Amazonas"
]

BUSCAS_SEGURANCA_ESTADUAL_AM = [
    "Segurança Pública Amazonas",
    "Polícia Civil Amazonas",
    "Polícia Militar Amazonas",
    "SSP-AM Manaus Amazonas",
    "ROCAM Força Tática Manaus Amazonas",
    "delegacia polícia Manaus Amazonas prisão",
    "homicídio crime Manaus Amazonas polícia"
]

BUSCAS_MEIO_AMBIENTE = [
    "Garimpo ilegal Amazonas",
    "Extração de ouro Amazonas",
    "Queimadas Amazonas",
    "Incêndio florestal Amazônia Região Norte",
    "Focos de queimadas floresta amazônica",
    "Crime ambiental IBAMA ICMBio Amazonas"
]

BUSCAS_POLITICOS_AM = [
    "Investigação política Amazonas",
    "Operação policial prefeito vereador deputado Amazonas",
    "Prisão prefeito vereador deputado secretário Amazonas",
    "Corrupção desvio verba investigação Manaus Amazonas",
    "MPAM MPF investigação político Amazonas"
]

BUSCAS_OCULTAS_CM7 = [
    "site:cm7brasil.com polícia",
    "site:cm7brasil.com polícia federal",
    "site:cm7brasil.com operação",
    "site:cm7brasil.com amazonas"
]

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

BUSCAS_NACIONAIS_ABERTAS = [
    "STF Supremo Justiça decisão Brasil",
    "Política Governo Congresso Brasil",
    "Economia Banco Central Receita Federal Brasil"
]

MUNICIPIOS_E_INDICADORES_AM = [
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
    "vale do javari", "pc-am", "pcam", "pmam", "pm-am", "ssp-am", "sspam",
    "aleam", "tjam", "mpam", "tce-am", "tre-am", "ipaam", "cbmam", "detran-am"
]

REGIAO_NORTE_E_PAN_AMAZONIA = MUNICIPIOS_E_INDICADORES_AM + [
    "amazônia", "amazonia", "floresta amazônica", "amazônico", "amazônica",
    "região norte", "acre", "rio branco", "amapá", "macapá", "pará", "belém",
    "santarém", "altamira", "itaituba", "rondônia", "porto velho", "roraima",
    "boa vista", "tocantins", "palmas", "bolívia", "peru", "colômbia", "colombia",
    "venezuela", "equador", "guiana", "suriname", "guiana francesa", "pan-amazônia"
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

TERMOS_TRAFICO = [
    "tráfico", "traficante", "traficantes", "narcotráfico", "droga", "drogas",
    "entorpecente", "entorpecentes", "cocaína", "maconha", "skunk", "pasta base",
    "oxi", "crack", "haxixe", "ecstasy", "mdma", "lança-perfume", "tabletes de",
    "tijolos de", "quilos de droga", "tonelada de droga", "apreensão de drogas",
    "apreende drogas", "boca de fumo", "laboratório de refino", "mula do tráfico",
    "denarc", "drrco", "drco"
]

CERNE_SEGURANCA_ESTADUAL = [
    "polícia civil", "pc-am", "pcam", "polícia militar", "pmam", "pm-am",
    "ssp-am", "sspam", "secretaria de segurança pública", "rocam", "força tática",
    "coe", "cicom", "ronda no bairro", "dip", "distrito integrado de polícia",
    "dehs", "derfd", "depca", "deccm", "delegado", "delegada", "delegacia",
    "viatura", "policiamento", "bombeiros", "cbmam", "seap", "sistema prisional",
    "homicídio", "assassinato", "latrocínio", "feminicídio", "tiroteio", "baleado",
    "disparos de arma", "assalto", "roubo", "furto", "arrastão", "sequestro",
    "cárcere privado", "extorsão", "estelionato", "golpe", "violência doméstica",
    "maria da penha", "estupro", "facção", "comando vermelho", "pcc",
    "família do norte", "fdn", "tribunal do crime", "porte ilegal de arma",
    "arma de fogo", "fuzil", "pistola", "prisão em flagrante", "mandado de prisão",
    "foragido", "operação policial", "segurança pública"
]

TERMOS_QUEIMADA_FOGO = [
    "queimada", "queimadas", "incêndio", "incêndios", "fogo na floresta",
    "fogo na mata", "focos de calor", "focos de incêndio", "fumaça de queimada",
    "nuvem de fumaça", "brigadista", "combate ao fogo", "queima ilegal"
]

TERMOS_MEIO_AMBIENTE_GERAL = TERMOS_QUEIMADA_FOGO + [
    "garimpo", "garimpeiro", "garimpeiros", "extração de ouro",
    "extração ilegal de ouro", "draga", "dragas", "balsa de garimpo", "mercúrio",
    "mineração ilegal", "crime ambiental", "crimes ambientais", "ibama", "icmbio",
    "ipaam", "batalhão ambiental", "bpamb", "dema", "madeira ilegal", "desmatamento",
    "fauna", "pesca ilegal", "pirarucu ilegal", "quelônios", "terra indígena",
    "yanomami", "vale do javari"
]

TERMOS_POLITICOS = [
    "político", "políticos", "política", "prefeito", "prefeita", "ex-prefeito",
    "ex-prefeita", "vice-prefeito", "vereador", "vereadora", "ex-vereador",
    "deputado", "deputada", "ex-deputado", "senador", "senadora", "ex-senador",
    "governador", "ex-governador", "vice-governador", "secretário municipal",
    "secretário estadual", "ex-secretário", "assessor", "assessora", "ex-assessor",
    "chefe de gabinete", "parlamentar", "candidato", "candidata", "gestor público",
    "agente político", "aliado de", "ligado a", "parente de", "esposa do prefeito",
    "filho do prefeito", "empresário ligado", "câmara municipal",
    "assembleia legislativa", "aleam", "prefeitura"
]

TERMOS_CRIME_INVESTIGACAO_POLITICA = [
    "investigação", "investigado", "investigada", "inquérito", "prisão", "preso",
    "presa", "mandado", "busca e apreensão", "operação", "indiciado", "indiciada",
    "acusado", "acusada", "denunciado", "denunciada", "réu", "crime", "crimes",
    "corrupção", "desvio", "peculato", "lavagem de dinheiro", "improbidade",
    "fraude em licitação", "superfaturamento", "propina", "rachadinha",
    "compra de votos", "caixa dois", "crime eleitoral", "afastado do cargo",
    "afastamento", "cassação", "gaeco", "cecor", "drcco", "pf", "polícia federal",
    "polícia civil", "mpf", "mpam", "tce-am"
]

CERNE_REGIONAL = list(set(
    TERMOS_TRAFICO + CERNE_SEGURANCA_ESTADUAL + TERMOS_MEIO_AMBIENTE_GERAL +
    TERMOS_CRIME_INVESTIGACAO_POLITICA + [
        "polícia", "policial", "federal", "civil", "militar", "apreensão",
        "apreendido", "pirataria", "fluvial", "embarcação", "fronteira",
        "justiça", "ministério público", "juiz", "desembargador", "danielle mady"
    ]
))

CERNE_FRONTEIRA = CERNE_REGIONAL + [
    "guerrilha", "guerrilheiro", "guerrilheiros", "farc", "eln", "sendero luminoso",
    "tren de aragua", "dissidentes", "cartel", "narcotráfico", "narcotraficante",
    "narco", "contrabando", "descaminho", "exército", "forças armadas", "soberania",
    "migração", "refugiados", "paramilitar", "armamento", "munição"
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
    return any(re.search(rf'\b{re.escape(mun)}\b', texto_analise) for mun in MUNICIPIOS_E_INDICADORES_AM)


def cita_outro_estado_sem_am(titulo, resumo):
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()
    tem_am = tem_vinculo_amazonas(titulo, resumo)
    cita_outro = any(re.search(rf'\b{re.escape(est)}\b', texto) for est in OUTROS_ESTADOS_CAPITAIS)
    return cita_outro and not tem_am


def eh_noticia_queimada(titulo, resumo):
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()
    return any(q in texto for q in TERMOS_QUEIMADA_FOGO)


def validar_pf_amazonas(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}"
    if not tem_mencao_pf(texto):
        return False
    return tem_vinculo_amazonas(titulo, resumo)


def validar_pf_brasil(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}"
    texto_low = texto.lower()
    if not tem_mencao_pf(texto):
        return False
    if tem_vinculo_amazonas(titulo, resumo):
        return False
    estrangeiras = ["polícia federal argentina", "polícia federal da argentina", "polícia federal mexicana", "polícia federal do méxico"]
    if any(est in texto_low for est in estrangeiras):
        return False
    return True


def validar_trafico_amazonas(titulo, resumo, link):
    """Apreensões e tráfico de drogas no Amazonas em âmbito estadual/integrado (não PF)."""
    if eh_ruido_absoluto(titulo, resumo, link):
        return False
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()

    if tem_mencao_pf(texto):
        return False
    if not tem_vinculo_amazonas(titulo, resumo):
        return False
    if cita_outro_estado_sem_am(titulo, resumo):
        return False

    return any(t in texto for t in TERMOS_TRAFICO)


def validar_seguranca_estadual_amazonas(titulo, resumo, link):
    """Segurança pública estadual no Amazonas, PC-AM e PMAM (exclui PF)."""
    if eh_ruido_absoluto(titulo, resumo, link):
        return False
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()

    if tem_mencao_pf(texto):
        return False
    if not tem_vinculo_amazonas(titulo, resumo):
        return False
    if cita_outro_estado_sem_am(titulo, resumo):
        return False

    return any(c in texto for c in CERNE_SEGURANCA_ESTADUAL)


def validar_meio_ambiente(titulo, resumo, link):
    """
    Garimpo ilegal/ouro/crimes ambientais no AM + qualquer notícia de queimada/incêndio/fogo
    envolvendo Amazônia, Floresta Amazônica, Amazonas, Região Norte ou países pan-amazônicos.
    """
    if eh_ruido_absoluto(titulo, resumo, link):
        return False
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()

    # Ramo A: Queimadas / Incêndios / Fogo na Amazônia, AM, Região Norte ou países pan-amazônicos
    if eh_noticia_queimada(titulo, resumo):
        return any(re.search(rf'\b{re.escape(loc)}\b', texto) for loc in REGIAO_NORTE_E_PAN_AMAZONIA)

    # Ramo B: Garimpo ilegal, extração de ouro e demais crimes ambientais no Amazonas
    if not tem_vinculo_amazonas(titulo, resumo):
        return False
    if cita_outro_estado_sem_am(titulo, resumo):
        return False

    return any(m in texto for m in TERMOS_MEIO_AMBIENTE_GERAL)


def validar_politicos_amazonas(titulo, resumo, link):
    """Investigação, prisão, operação ou crimes envolvendo políticos e aliados no Amazonas."""
    if eh_ruido_absoluto(titulo, resumo, link):
        return False
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()

    if not tem_vinculo_amazonas(titulo, resumo):
        return False
    if cita_outro_estado_sem_am(titulo, resumo):
        return False

    tem_politico = any(p in texto for p in TERMOS_POLITICOS)
    tem_acao_criminal = any(c in texto for c in TERMOS_CRIME_INVESTIGACAO_POLITICA)
    return tem_politico and tem_acao_criminal


def validar_noticia_regional(titulo, resumo, link):
    if eh_ruido_absoluto(titulo, resumo, link):
        return False
    titulo_limpo = limpar_titulo_sem_fonte(titulo)
    texto = f"{titulo_limpo} {resumo}".lower()

    if not any(cerne in texto for cerne in CERNE_REGIONAL):
        return False
    if cita_outro_estado_sem_am(titulo, resumo):
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


def coletar_categoria(buscas, validador, dados_existentes, chave_cat, links_usados, titulos_usados, msg_vazio, marcar_queimada=False):
    lista = []
    if isinstance(dados_existentes.get(chave_cat), list):
        for n in dados_existentes[chave_cat]:
            l, t, r = n.get('link', ''), n.get('titulo', ''), n.get('resumo', '')
            chave_t = normalizar_titulo_dedup(t)
            if validador(t, r, l) and l not in links_usados and chave_t not in titulos_usados:
                links_usados.add(l)
                titulos_usados.add(chave_t)
                if marcar_queimada:
                    n['alerta_queimada'] = eh_noticia_queimada(t, r)
                lista.append(n)

    for termo in buscas:
        try:
            artigos = google_news.get_news(termo)
            if artigos:
                for artigo in artigos:
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or f"Notícia referente a {chave_cat}."
                    chave_tit = normalizar_titulo_dedup(titulo)

                    if link in links_usados or chave_tit in titulos_usados:
                        continue
                    if not validador(titulo, resumo, link):
                        continue

                    links_usados.add(link)
                    titulos_usados.add(chave_tit)
                    obj = {
                        'titulo': titulo,
                        'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Fonte'),
                        'link': link
                    }
                    if marcar_queimada:
                        obj['alerta_queimada'] = eh_noticia_queimada(titulo, resumo)
                    lista.append(obj)
        except Exception:
            pass

    return ordenar_com_prioridade(lista) if lista else msg_vazio


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

    # Migração automática de categorias antigas fundidas/renomeadas
    mapa_migracao = {
        CAT_TRAFICO_AM: ["Tráfico de drogas Amazonas", "Apreensão de drogas Amazonas"],
        CAT_SEGURANCA_ESTADUAL_AM: ["Segurança Pública Amazonas", "Polícia Civil Amazonas", "Polícia Militar Amazonas"],
        CAT_MEIO_AMBIENTE_AM: ["Garimpo ilegal Amazonas", "Extração de ouro Amazonas", "Queimadas Amazonas"],
        CAT_POLITICOS_AM: ["Investigação política Amazonas"]
    }
    for nova_cat, antigas in mapa_migracao.items():
        if not isinstance(dados_existentes.get(nova_cat), list):
            dados_existentes[nova_cat] = []
        for ant in antigas:
            itens = dados_existentes.pop(ant, [])
            if isinstance(itens, list):
                dados_existentes[nova_cat].extend(itens)

    relatorio_geral = {}

    # 1 e 2. Polícia Federal - Amazonas e Polícia Federal - Brasil (mutuamente exclusivas)
    links_pf = set()
    titulos_pf = set()
    relatorio_geral[CAT_PF_AMAZONAS] = coletar_categoria(
        BUSCAS_PF_AMAZONAS, validar_pf_amazonas, dados_existentes, CAT_PF_AMAZONAS,
        links_pf, titulos_pf, "Sem atualizações relevantes da PF no Amazonas nas últimas 24h."
    )
    relatorio_geral[CAT_PF_BRASIL] = coletar_categoria(
        BUSCAS_PF_BRASIL, validar_pf_brasil, dados_existentes, CAT_PF_BRASIL,
        links_pf, titulos_pf, "Sem atualizações relevantes da PF no restante do país nas últimas 24h."
    )

    # 3. Fronteiras, narcotráfico e guerrilhas nos países limítrofes do Amazonas
    links_fronteira = set()
    titulos_fronteira = set()
    relatorio_geral[CATEGORIA_FRONTEIRAS] = coletar_categoria(
        BUSCAS_FRONTEIRAS, validar_noticia_fronteira, dados_existentes, CATEGORIA_FRONTEIRAS,
        links_fronteira, titulos_fronteira, "Sem atualizações relevantes nas últimas 24h."
    )

    # 4. Tráfico de Drogas - Amazonas (âmbito estadual/integrado, sem PF)
    links_trafico = set(links_pf)
    titulos_trafico = set(titulos_pf)
    relatorio_geral[CAT_TRAFICO_AM] = coletar_categoria(
        BUSCAS_TRAFICO_AM, validar_trafico_amazonas, dados_existentes, CAT_TRAFICO_AM,
        links_trafico, titulos_trafico, "Sem atualizações relevantes nas últimas 24h."
    )

    # 5. Segurança Pública Estadual - Amazonas (PC-AM, PMAM e ocorrências estaduais, sem PF)
    links_seg_est = set(links_pf)
    titulos_seg_est = set(titulos_pf)
    relatorio_geral[CAT_SEGURANCA_ESTADUAL_AM] = coletar_categoria(
        BUSCAS_SEGURANCA_ESTADUAL_AM, validar_seguranca_estadual_amazonas, dados_existentes, CAT_SEGURANCA_ESTADUAL_AM,
        links_seg_est, titulos_seg_est, "Sem atualizações relevantes nas últimas 24h."
    )

    # 6. Crimes contra o Meio Ambiente - Amazonas (com flag alerta_queimada)
    links_meio_amb = set()
    titulos_meio_amb = set()
    relatorio_geral[CAT_MEIO_AMBIENTE_AM] = coletar_categoria(
        BUSCAS_MEIO_AMBIENTE, validar_meio_ambiente, dados_existentes, CAT_MEIO_AMBIENTE_AM,
        links_meio_amb, titulos_meio_amb, "Sem atualizações relevantes nas últimas 24h.",
        marcar_queimada=True
    )

    # 7. Investigação Policial envolvendo Políticos - Amazonas
    links_politicos = set()
    titulos_politicos = set()
    relatorio_geral[CAT_POLITICOS_AM] = coletar_categoria(
        BUSCAS_POLITICOS_AM, validar_politicos_amazonas, dados_existentes, CAT_POLITICOS_AM,
        links_politicos, titulos_politicos, "Sem atualizações relevantes nas últimas 24h."
    )

    # 8. Demais Categorias Remanescentes do Amazonas
    links_restantes = set(links_pf | links_trafico | links_seg_est)
    titulos_restantes = set(titulos_pf | titulos_trafico | titulos_seg_est)
    for tema in TEMAS_BUSCA_RESTANTES:
        relatorio_geral[tema] = coletar_categoria(
            [tema], validar_noticia_regional, dados_existentes, tema,
            links_restantes, titulos_restantes, "Sem atualizações relevantes nas últimas 24h."
        )

    # 9. Varredura Oculta e Prioritária no CM7 (roteando para a categoria exata)
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

                    def injetar(cat, l_set, t_set, flag_fogo=False):
                        if link not in l_set and chave_tit not in t_set:
                            l_set.add(link)
                            t_set.add(chave_tit)
                            item = dict(noticia_obj)
                            if flag_fogo:
                                item['alerta_queimada'] = eh_noticia_queimada(titulo, resumo)
                            if not isinstance(relatorio_geral.get(cat), list):
                                relatorio_geral[cat] = []
                            relatorio_geral[cat].append(item)
                            relatorio_geral[cat] = ordenar_com_prioridade(relatorio_geral[cat])

                    if validar_pf_amazonas(titulo, resumo, link):
                        injetar(CAT_PF_AMAZONAS, links_pf, titulos_pf)
                    elif validar_pf_brasil(titulo, resumo, link):
                        injetar(CAT_PF_BRASIL, links_pf, titulos_pf)

                    if validar_trafico_amazonas(titulo, resumo, link):
                        injetar(CAT_TRAFICO_AM, links_trafico, titulos_trafico)
                    elif validar_seguranca_estadual_amazonas(titulo, resumo, link):
                        injetar(CAT_SEGURANCA_ESTADUAL_AM, links_seg_est, titulos_seg_est)

                    if validar_meio_ambiente(titulo, resumo, link):
                        injetar(CAT_MEIO_AMBIENTE_AM, links_meio_amb, titulos_meio_amb, flag_fogo=True)

                    if validar_politicos_amazonas(titulo, resumo, link):
                        injetar(CAT_POLITICOS_AM, links_politicos, titulos_politicos)
        except Exception:
            pass

    # 10. Varredura Nacional: Portais Prioritários + Buscas Abertas
    links_nacionais = set()
    titulos_nacionais = set()
    noticias_brasil = []

    if isinstance(dados_existentes.get(CAT_NACIONAL), list):
        for n in dados_existentes[CAT_NACIONAL]:
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

                    def espelhar(cat, l_set, t_set, flag_fogo=False):
                        if link not in l_set and chave_tit not in t_set:
                            l_set.add(link)
                            t_set.add(chave_tit)
                            item = dict(noticia_obj)
                            if flag_fogo:
                                item['alerta_queimada'] = eh_noticia_queimada(titulo, resumo)
                            if not isinstance(relatorio_geral.get(cat), list):
                                relatorio_geral[cat] = []
                            relatorio_geral[cat].append(item)
                            relatorio_geral[cat] = ordenar_com_prioridade(relatorio_geral[cat])

                    if validar_pf_amazonas(titulo, resumo, link):
                        espelhar(CAT_PF_AMAZONAS, links_pf, titulos_pf)
                    elif validar_pf_brasil(titulo, resumo, link):
                        espelhar(CAT_PF_BRASIL, links_pf, titulos_pf)

                    if validar_noticia_fronteira(titulo, resumo, link):
                        espelhar(CATEGORIA_FRONTEIRAS, links_fronteira, titulos_fronteira)

                    if validar_trafico_amazonas(titulo, resumo, link):
                        espelhar(CAT_TRAFICO_AM, links_trafico, titulos_trafico)
                    elif validar_seguranca_estadual_amazonas(titulo, resumo, link):
                        espelhar(CAT_SEGURANCA_ESTADUAL_AM, links_seg_est, titulos_seg_est)

                    if validar_meio_ambiente(titulo, resumo, link):
                        espelhar(CAT_MEIO_AMBIENTE_AM, links_meio_amb, titulos_meio_amb, flag_fogo=True)

                    if validar_politicos_amazonas(titulo, resumo, link):
                        espelhar(CAT_POLITICOS_AM, links_politicos, titulos_politicos)

                    if link not in links_nacionais and chave_tit not in titulos_nacionais:
                        links_nacionais.add(link)
                        titulos_nacionais.add(chave_tit)
                        noticias_brasil.append(noticia_obj)
                        contador += 1
        except Exception:
            pass

    relatorio_geral[CAT_NACIONAL] = ordenar_com_prioridade(noticias_brasil) if noticias_brasil else "Sem atualizações válidas."

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
