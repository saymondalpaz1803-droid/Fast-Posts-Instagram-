# -*- coding: utf-8 -*-
"""Roteiro final (narração) do vídeo 01 — Ciclo nasal.

Cada segmento tem um id usado pela linha do tempo das cenas.
Palavras entre *asteriscos* aparecem em AMARELO na legenda.
"""

SEGMENTS = [
    ("hook",     "Já percebeu que, às vezes, uma *narina* parece respirar *melhor* que a outra?"),
    ("hook2",    "Não é impressão. Olha o que acontece *dentro* do seu nariz."),
    ("septo",    "Por dentro, o nariz tem duas *cavidades*, separadas por uma parede chamada *septo*."),
    ("conchas",  "Nas laterais ficam as *conchas* *nasais*, cobertas por uma *mucosa* cheia de *vasos* *sanguíneos*."),
    ("curioso",  "Agora vem a parte curiosa."),
    ("incha",    "De um lado, esses vasos se *enchem* de sangue. A mucosa *incha*, e a passagem de ar fica mais *estreita*."),
    ("desincha", "Do outro lado, ela *desincha*, e o ar passa com mais *facilidade*."),
    ("horas",    "*Horas* *depois*, essa diferença pode se *inverter*."),
    ("ciclo",    "Isso se chama *ciclo* *nasal*. Ele é controlado automaticamente pelo *sistema* *nervoso*."),
    ("compensa", "E como um lado *compensa* o outro, muita gente nem percebe."),
    ("resumo",   "Resumindo: um lado *incha*, o outro *desincha*, e depois eles *trocam*."),
    ("aviso",    "Mas *atenção*: nem todo entupimento é parte desse ciclo. Se for *persistente* ou *intenso*, procure um *profissional* de saúde."),
    ("cta",      "E aí, você já tinha *percebido* isso? Conta nos *comentários*!"),
]

# pausa (s) inserida DEPOIS de cada segmento
GAPS = {
    "hook": 0.25, "hook2": 0.45, "septo": 0.30, "conchas": 0.45, "curioso": 0.25,
    "incha": 0.25, "desincha": 0.45, "horas": 0.35, "ciclo": 0.30, "compensa": 0.45,
    "resumo": 0.45, "aviso": 0.40, "cta": 0.0,
}
LEAD_IN = 0.35   # silêncio antes da 1ª fala
TAIL = 1.4       # tempo após a última fala (cartela final)
