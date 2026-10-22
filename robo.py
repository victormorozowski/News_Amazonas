from datetime import datetime, timedelta
import json
import os
from email.utils import parsedate_to_datetime
from gnews import GNews

google_news = GNews(language='pt', country='BR', period='1d', max_results=10)

TEMAS_BUSCA = [
    "Superintendência da Polícia Federal no Amazonas",
    "Superintendente da Polícia Federal no Amazonas",
    "Delegada de Polícia Federal Danielle de Meneses Oliveira Mady",
    "Tráfico de drogas no Amazonas",
    "Apreensão de drogas no Amazonas",
    "Segurança Pública no Amazonas",
    "Desmatamento no Amazonas",
    "Queimadas no Amazonas",
    "Garimpo ilegal no Amazonas",
    "Extração de ouro no Amazonas",
    "Prisão no Amazonas",
    "Pirataria fluvial Amazonas",
    "Política no Amazonas fatos relevantes",
    "Polícia Civil do Amazonas",
    "Polícia Militar do Amazonas",
    "Polícia Federal do Amazonas",
    "Operações da Polícia Federal Amazonas",
    "Órgãos Federais atuantes no Amazonas",
]

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
        ("weeks", "semanas"), ("week", "semana"),
        ("months ago", "meses atrás"), ("month ago", "mês atrás"),
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
    
    try:
        for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%d/%m/%Y %H:%M'):
            try:
                return datetime.strptime(str(data_str).strip(), fmt)
            except ValueError:
                continue
    except:
        pass
        
    return datetime.min

def buscar_noticias():
    data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')
    data_hoje = datetime.now().strftime('%Y-%m-%d')

    print(f"Iniciando varredura de notícias - {data_execucao}\n" + "=" * 50)

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
                    links_processados.add(link)

                    titulo = artigo.get('title', 'Sem Título')
                    fonte = artigo.get('publisher', {}).get('title', 'Fonte Desconhecida')
                    
                    data_crua = artigo.get('published date', '')
                    data_pub = formatar_data_brasil(data_crua)
                    
                    descricao = artigo.get('description', '')
                    resumo = descricao if descricao else f"Notícia referente a {tema}."

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
