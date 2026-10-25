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

# Temas que virarão as ABAS do site
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

# Buscas ocultas do CM7 (não viram abas, alimentam as abas acima)
BUSCAS_OCULTAS_CM7 = [
    "site:cm7brasil.com polícia",
    "site:cm7brasil.com amazonas"
]

FONTES_NACIONAIS = [
    {"nome": "G1", "termo": "site:g1.globo.com"},
    {"nome": "UOL", "termo": "site:uol.com.br"},
    {"nome": "R7", "termo": "site:r7.com"},
    {"nome": "Metrópoles", "termo": "site:metropoles.com"},
    {"nome": "CNN Brasil", "termo": "site:cnnbrasil.com.br"}
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
    "urucurituba", "amazonas", "am", "alto solimões", "rio negro", "rio solimões"
]

CERNE_TEMATICO = [
    "polícia", "policial", "delegado", "delegada", "pf", "prf", "federal", "civil", 
    "militar", "operação", "investigação", "investigado", "prisão", "preso", 
    "apreensão", "apreendido", "droga", "drogas", "tráfico", "crime", "criminoso", 
    "garimpo", "ouro", "desmatamento", "queimada", "ambiental", "meio ambiente", 
    "pirataria", "fluvial", "justiça", "ministério", "governo", "deputado", 
    "senador", "vereador", "prefeito", "corregedoria", "supremo", "tribunal", "juiz"
]

TERMOS_RUIDO = [
    "vestibular", "biblioteca", "escola municipal", "ensino fundamental", 
    "educação inclusiva", "formatura", "teatro", "exposição cultural", 
    "campeonato municipal", "festa de", "campeonato de futebol", 
    "concurso público municipal", "matrícula escolar", "merenda escolar"
]

def validar_relevancia_noticia(titulo, resumo, link):
    texto = f"{titulo} {resumo}".lower()
    link_baixado = link.lower()
    for ruido in TERMOS_RUIDO:
        if ruido in texto:
            return False
    if "cm7brasil.com" in link_baixado:
        tem_am = any(mun in texto for mun in MUNICIPIOS_AM) or "manaus" in texto or "amazonas" in texto
        tem_cerne = any(cerne in texto for cerne in CERNE_TEMATICO)
        if tem_am or tem_cerne:
            return True
    termos_superintendente = ["danielle mady", "danielle de meneses", "delegada danielle", "superintendente danielle"]
    if any(termo in texto for termo in termos_superintendente):
        return True
    tem_vinculo_am = any(mun in texto for mun in MUNICIPIOS_AM)
    if not tem_vinculo_am:
        return False
    return any(cerne in texto for cerne in CERNE_TEMATICO)

def formatar_data_brasil(data_str):
    if not data_str:
        return "Data não informada"
    str_val = str(data_str).strip()
    try:
        dt_utc = parsedate_to_datetime(str_val)
        if dt_utc:
            return (dt_utc - timedelta(hours=4)).strftime('%d/%m/%Y às %H:%M (GMT-4 Manaus)')
    except:
        pass
    return str_val

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
    if not google_news:
        return
    dados_existentes = {}
    if os.path.exists('noticias_atualizadas.json'):
        try:
            with open('noticias_atualizadas.json', 'r', encoding='utf-8') as f:
                dados_existentes = json.load(f)
                # Remove as abas feias do histórico se existirem
                dados_existentes.pop("site:cm7brasil.com polícia", None)
                dados_existentes.pop("site:cm7brasil.com amazonas", None)
        except:
            pass

    links_processados = set()
    for noticias in dados_existentes.values():
        if isinstance(noticias, list):
            for n in noticias:
                if 'link' in n:
                    links_processados.add(n['link'])

    relatorio_geral = {}

    # 1. Processa Temas Principais
    for tema in TEMAS_BUSCA:
        try:
            artigos = google_news.get_news(tema)
            noticias_tema = list(dados_existentes.get(tema, [])) if isinstance(dados_existentes.get(tema), list) else []
            if artigos:
                for artigo in artigos:
                    link = artigo.get('url', '#')
                    if link in links_processados:
                        continue
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or f"Notícia referente a {tema}."
                    if not validar_relevancia_noticia(titulo, resumo, link):
                        continue
                    links_processados.add(link)
                    noticias_tema.append({
                        'titulo': titulo, 'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'Fonte'),
                        'link': link
                    })
            if noticias_tema:
                noticias_tema.sort(key=lambda x: converter_data_para_ordenacao(x.get('data_original')), reverse=True)
                relatorio_geral[tema] = noticias_tema
            else:
                relatorio_geral[tema] = "Sem atualizações relevantes nas últimas 24h."
        except:
            relatorio_geral[tema] = dados_existentes.get(tema, "Sem atualizações.")

    # 2. Processa o CM7 em background e distribui nas abas corretas
    for busca_cm7 in BUSCAS_OCULTAS_CM7:
        try:
            artigos_cm7 = google_news.get_news(busca_cm7)
            if artigos_cm7:
                for artigo in artigos_cm7:
                    link = artigo.get('url', '#')
                    if link in links_processados:
                        continue
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Notícia CM7."
                    if not validar_relevancia_noticia(titulo, resumo, link):
                        continue
                    
                    links_processados.add(link)
                    noticia_obj = {
                        'titulo': titulo, 'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', 'CM7 Brasil'),
                        'link': link
                    }
                    
                    # Tenta jogar no Tráfico, se couber. Senão, joga em Segurança Pública.
                    aba_destino = "Segurança Pública Amazonas"
                    if "droga" in (titulo+resumo).lower():
                        aba_destino = "Tráfico de drogas Amazonas"
                        
                    if isinstance(relatorio_geral.get(aba_destino), list):
                        relatorio_geral[aba_destino].append(noticia_obj)
                        relatorio_geral[aba_destino].sort(key=lambda x: converter_data_para_ordenacao(x.get('data_original')), reverse=True)
        except:
            pass

    # 3. Processa Notícias Nacionais
    noticias_brasil = []
    for fonte_info in FONTES_NACIONAIS:
        try:
            artigos_portal = google_news.get_news(fonte_info["termo"])
            if artigos_portal:
                contador = 0
                for artigo in artigos_portal:
                    if contador >= 5:
                        break
                    link = artigo.get('url', '#')
                    titulo = artigo.get('title', 'Sem Título')
                    resumo = artigo.get('description', '') or "Destaque nacional."
                    noticia_obj = {
                        'titulo': titulo, 'resumo': resumo,
                        'data': formatar_data_brasil(artigo.get('published date', '')),
                        'data_original': str(artigo.get('published date', '')),
                        'fonte': artigo.get('publisher', {}).get('title', fonte_info["nome"]),
                        'link': link
                    }
                    if any(mun in f"{titulo} {resumo}".lower() for mun in MUNICIPIOS_AM):
                        for t_reg, l_not in relatorio_geral.items():
                            if t_reg in TEMAS_BUSCA[:18] and validar_relevancia_noticia(titulo, resumo, link):
                                if isinstance(l_not, list) and not any(n.get('link') == link for n in l_not):
                                    l_not.append(noticia_obj)
                                    l_not.sort(key=lambda x: converter_data_para_ordenacao(x.get('data_original')), reverse=True)
                                break
                    noticias_brasil.append(noticia_obj)
                    contador += 1
        except:
            pass

    if noticias_brasil:
        noticias_brasil.sort(key=lambda x: converter_data_para_ordenacao(x.get('data_original')), reverse=True)
        relatorio_geral["Principais Notícias do Brasil"] = noticias_brasil
    else:
        relatorio_geral["Principais Notícias do Brasil"] = "Sem atualizações."

    with open('noticias_atualizadas.json', 'w', encoding='utf-8') as f:
        json.dump(relatorio_geral, f, ensure_ascii=False, indent=4)

    historico = {}
    if os.path.exists('historico_geral.json'):
        try:
            with open('historico_geral.json', 'r', encoding='utf-8') as f:
                historico = json.load(f)
        except:
            pass
    historico[datetime.now().strftime('%Y-%m-%d')] = relatorio_geral
    with open('historico_geral.json', 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    buscar_noticias()
