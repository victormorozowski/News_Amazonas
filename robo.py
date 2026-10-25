# Filtro agressivo expandido (agora com equipas europeias, transmissões e formato de jogo)
TERMOS_RUIDO = [
    "vestibular", "biblioteca", "escola municipal", "ensino fundamental", 
    "educação inclusiva", "formatura", "teatro", "exposição cultural", 
    "campeonato municipal", "festa de", "concurso público municipal", 
    "matrícula escolar", "merenda escolar",
    "futebol", "brasileirão", "libertadores", "copa do brasil", "champions league",
    "série a", "série b", "flamengo", "corinthians", "palmeiras", "são paulo",
    "vasco", "botafogo", "fluminense", "cruzeiro", "atlético-mg", "grêmio",
    "internacional", "esporte", "esportes", "tênis", "vôlei", "basquete", "nba",
    "fórmula 1", "ufc", "mma", "olimpíadas", "atleta", "medalha", "torneio", "copa do mundo",
    "ginástica", "trave", "bronze", "prata", "ouro", "pódio", "mundial de", "campeonato",
    "campeão", "campeã", "seleção", "liga", "clube", "partida", "jogo",
    "golo", "gol", "placar", "resultado", "empate", "vitória", "derrota", "treinador", 
    "técnico", "medalhista", "rebeca andrade", "flávia saraiva", "simone biles", "surfe", "skate",
    "barcelona", "real madrid", "espanhol", "premier league", "la liga", "assistir ao vivo", 
    "onde vai passar", "onde assistir", "transmissão", "escalação", "desfalque", "classificação",
    " x "  # Bloqueia o formato clássico de jogos, ex: "Barcelona x Real Madrid"
]
