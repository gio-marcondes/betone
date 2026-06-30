import os
import re
import json
import math
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI(title="Predator Web API")

# Permitir requisições do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FICHEIRO_CHAVES = "chaves_api.txt"
FICHEIRO_HISTORICO = "historico_jogos.json"

DICIONARIO_TRADUCOES = {
    "Ball possession": "Posse de Bola",
    "Expected goals": "Gols Esperados (xG)",
    "Big chances": "Grandes Chances",
    "Total shots": "Total de Chutes",
    "Goalkeeper saves": "Defesas do Goleiro",
    "Corner kicks": "Escanteios",
    "Fouls": "Faltas",
    "Passes": "Passes",
    "Tackles": "Desarmes",
    "Free kicks": "Tiros Livres",
    "Yellow cards": "Cartões Amarelos",
    "Red cards": "Cartões Vermelhos",
    "Shots on target": "Chutes no Alvo",
    "Hit woodwork": "Bolas na Trave",
    "Shots off target": "Chutes Fora",
    "Blocked shots": "Chutes Bloqueados",
    "Shots inside box": "Chutes Dentro da Área",
    "Shots outside box": "Chutes Fora da Área",
    "Big chances scored": "Grandes Chances Marcadas",
    "Big chances missed": "Grandes Chances Perdidas",
    "Through balls": "Bolas Enfadas",
    "Touches in penalty area": "Toques na Área Adversária",
    "Fouled in final third": "Faltas Sofridas no Último Terço",
    "Offsides": "Impedimentos",
    "Accurate passes": "Passes Certos",
    "Throw-ins": "Arremessos Laterais",
    "Final third entries": "Entradas no Último Terço",
    "Final third phase": "Fase do Último Terço",
    "Long balls": "Lançamentos/Bolas Longas",
    "Crosses": "Cruzamentos",
    "Duels": "Duelos",
    "Dispossessed": "Desarmado",
    "Ground duels": "Duelos Chão",
    "Aerial duels": "Duelos Aéreos",
    "Dribbles": "Dribbles",
    "Tackles won": "Desarmes Ganhos",
    "Total tackles": "Total de Desarmes",
    "Interceptions": "Interceptações",
    "Recoveries": "Recuperações de Bola",
    "Clearances": "Cortes / Afastadas",
    "Errors lead to a shot": "Erros que Geraram Chute",
    "Total saves": "Total de Defesas",
    "Goals prevented": "Gols Evitados",
    "Big saves": "Defesas Difíceis",
    "High claims": "Bolas Altas Capturadas",
    "Punches": "Socos na Bola",
    "Goal kicks": "Tiros de Meta",
    "Distance covered": "Distância Percorrida",
    "Number of sprints": "Número de Sprints"
}

class ChaveRequest(BaseModel):
    chave: str

class HistoricoItem(BaseModel):
    match_id: str
    nome: str
    url: str

FICHEIRO_TELEGRAM = "telegram_config.json"

class TelegramConfigRequest(BaseModel):
    token: str
    chat_id: str
    enabled: bool = True
    min_prob: int = 70

def carregar_telegram_config() -> dict:
    if os.path.exists(FICHEIRO_TELEGRAM):
        try:
            with open(FICHEIRO_TELEGRAM, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"token": "", "chat_id": "", "enabled": False, "min_prob": 70}

def salvar_telegram_config(config: dict):
    with open(FICHEIRO_TELEGRAM, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

ALERTAS_ENVIADOS = set()


def carregar_chaves():
    if os.path.exists(FICHEIRO_CHAVES):
        with open(FICHEIRO_CHAVES, "r", encoding="utf-8") as f:
            chaves = [linha.strip() for list_linha in f if (linha := list_linha.strip())]
            if chaves:
                return chaves
    return ["c7d04000d0msh3f6770ff746185fp1e7485jsn84e83064e659"]

def salvar_chaves(chaves):
    with open(FICHEIRO_CHAVES, "w", encoding="utf-8") as f:
        for chave in chaves:
            f.write(f"{chave}\n")

def carregar_historico() -> List[Dict]:
    if os.path.exists(FICHEIRO_HISTORICO):
        try:
            with open(FICHEIRO_HISTORICO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_historico(historico: List[Dict]):
    with open(FICHEIRO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)

def adicionar_ao_historico(match_id: str, nome: str, url: str):
    historico = carregar_historico()
    # Evitar duplicações
    historico = [item for item in historico if item["match_id"] != match_id]
    historico.insert(0, {
        "match_id": match_id,
        "nome": nome,
        "url": url
    })
    salvar_historico(historico)

def extrair_id_sofascore(url: str) -> str:
    match = re.search(r"id:(\d+)", url)
    if match: return match.group(1)
    numeros = re.findall(r"\d+", url)
    return numeros[-1] if numeros else ""

def realizar_requisicao(url: str, chaves: list) -> tuple:
    for i, chave in enumerate(chaves):
        headers = {
            "x-rapidapi-host": "sofascore-sport-api.p.rapidapi.com",
            "x-rapidapi-key": chave
        }
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                return res.json(), i
        except Exception as e:
            print(f"Erro na chave {i}: {e}")
    return None, 0

@app.get("/api/chaves")
def listar_chaves():
    return {"chaves": carregar_chaves()}

@app.get("/api/jogo/buscar_scraping")
def buscar_jogo_scraping(q: str):
    # Tratar termos de busca
    termos = [t.lower().strip() for t in q.split() if t.strip()]
    if not termos:
        raise HTTPException(status_code=400, detail="Termo de busca vazio")

    # Configurar Chrome Headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Acessa o site usando o navegador virtual
        driver.get("https://www.sofascore.com/pt")
        driver.implicitly_wait(4)
        
        # Obter todos os links de jogos no HTML renderizado
        elements = driver.find_elements("xpath", "//a[@href]")
        links_encontrados = []
        
        for elem in elements:
            try:
                href = elem.get_attribute("href")
                if href and "/football/match/" in href:
                    href_lower = href.lower()
                    if all(termo in href_lower for termo in termos):
                        links_encontrados.append(href)
            except:
                continue

        if links_encontrados:
            url_alvo = links_encontrados[0]
            match_id = extrair_id_sofascore(url_alvo)
            return {"url": url_alvo, "match_id": match_id}

        raise HTTPException(status_code=404, detail="Nenhum jogo correspondente encontrado no Sofascore atual.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no scraping com Selenium: {str(e)}")
    finally:
        if driver:
            driver.quit()

@app.post("/api/chaves")
def add_chave(req: ChaveRequest):
    chaves = carregar_chaves()
    # Se a chave já existir, removemos e inserimos no topo para que vire padrão
    if req.chave in chaves:
        chaves.remove(req.chave)
    chaves.insert(0, req.chave)
    salvar_chaves(chaves)
    return {"status": "ok", "chaves": chaves}

@app.post("/api/chaves/definir_padrao")
def definir_chave_padrao(req: ChaveRequest):
    chaves = carregar_chaves()
    if req.chave in chaves:
        chaves.remove(req.chave)
        chaves.insert(0, req.chave)
        salvar_chaves(chaves)
        return {"status": "ok", "chaves": chaves}
    raise HTTPException(status_code=404, detail="Chave não encontrada na lista")

@app.delete("/api/chaves/{chave}")
def remove_chave(chave: str):
    chaves = carregar_chaves()
    if chave in chaves:
        if len(chaves) <= 1:
            raise HTTPException(status_code=400, detail="Mínimo de uma chave ativa exigido")
        chaves.remove(chave)
        salvar_chaves(chaves)
    return {"status": "ok", "chaves": chaves}

@app.get("/api/historico")
def obter_historico_jogos():
    return {"historico": carregar_historico()}

@app.delete("/api/historico/{match_id}")
def remover_do_historico(match_id: str):
    historico = carregar_historico()
    historico = [item for item in historico if item["match_id"] != match_id]
    salvar_historico(historico)
    return {"status": "ok", "historico": historico}

@app.get("/api/telegram/config")
def obter_telegram_config():
    return carregar_telegram_config()

@app.post("/api/telegram/config")
def atualizar_telegram_config(config: TelegramConfigRequest):
    cfg = config.dict()
    salvar_telegram_config(cfg)
    return {"status": "ok", "config": cfg}

@app.post("/api/telegram/test")
def testar_telegram(config: TelegramConfigRequest):
    url_tg = f"https://api.telegram.org/bot{config.token}/sendMessage"
    payload = {
        "chat_id": config.chat_id,
        "text": "🤖 *Predator Scanner* - Conexão de teste efetuada com sucesso!",
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url_tg, json=payload, timeout=5)
        if r.status_code == 200:
            return {"status": "ok"}
        return {"status": "error", "detail": r.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jogos/aovivo")
def obter_jogos_ao_vivo():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    lista_formatada = []
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get("https://www.sofascore.com/pt")
        driver.implicitly_wait(6)
        
        elements = driver.find_elements("xpath", "//*[contains(@class, 'd_flex') and contains(@class, 'flex-wrap_wrap') and contains(@class, 'gap_md')]//a[@href]")
        
        if not elements:
            elements = driver.find_elements("xpath", "//a[contains(@href, '/football/match/')]")

        links_vistos = set()
        for elem in elements:
            try:
                href = elem.get_attribute("href")
                if href and "/football/match/" in href and href not in links_vistos:
                    links_vistos.add(href)
                    match_id = extrair_id_sofascore(href)
                    
                    texto = elem.text.strip()
                    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
                    
                    nome = "Jogo"
                    placar = "0 - 0"
                    minuto = 45
                    
                    try:
                        slug = href.split("/")[-2]
                        slug_parts = slug.split("-")
                        if len(slug_parts) >= 2:
                            nome = f"{slug_parts[0].capitalize()} x {slug_parts[1].capitalize()}"
                    except:
                        pass
                        
                    status = f"{minuto}'"
                    if len(linhas) >= 2:
                        is_finalizado = any(x in linhas for x in ["FT", "Fim", "Encerrado", "Ended"])
                        is_intervalo = any(x in linhas for x in ["HT", "Intervalo"])
                        
                        if is_finalizado:
                            status = "Finalizado"
                            minuto = 90
                        elif is_intervalo:
                            status = "Intervalo"
                            minuto = 45

                        if nome == "Jogo":
                            nome = " x ".join([l for l in linhas if not l.isdigit() and ":" not in l and "'" not in l and l not in ["FT", "Fim", "Encerrado", "Ended", "HT", "Intervalo"]][:2])
                        
                        scores = [l for l in linhas if l.isdigit()]
                        if len(scores) >= 2:
                            placar = f"{scores[0]} - {scores[1]}"
                            
                        if not is_finalizado and not is_intervalo:
                            min_match = [l for l in linhas if "'" in l]
                            if min_match:
                                nums = re.findall(r"\d+", min_match[0])
                                if nums:
                                    minuto = int(nums[0])
                                    status = f"{minuto}'"
                    
                    lista_formatada.append({
                        "match_id": match_id,
                        "nome": nome,
                        "placar": placar,
                        "minuto": minuto,
                        "status": status,
                        "url": href
                    })
            except:
                continue
                
        return {"jogos": lista_formatada[:20]}
    except Exception as e:
        print(f"Erro ao buscar ao vivo via Selenium: {e}")
        return {"jogos": []}
    finally:
        if driver:
            driver.quit()

@app.get("/api/jogo/detalhes")
def obter_jogo_detalhes(url: str):
    match_id = extrair_id_sofascore(url)
    if not match_id:
        raise HTTPException(status_code=400, detail="URL inválida do Sofascore")
    
    chaves = carregar_chaves()
    api_url = f"https://sofascore-sport-api.p.rapidapi.com/api/event/{match_id}"
    dados, index = realizar_requisicao(api_url, chaves)
    if not dados:
        raise HTTPException(status_code=502, detail="Erro ao se comunicar com a API do Sofascore")
    
    event = dados.get("event", {})
    casa = event.get("homeTeam", {}).get("name", "Casa")
    fora = event.get("awayTeam", {}).get("name", "Fora")
    nome_jogo = f"{casa} x {fora}"
    
    # Salvar no histórico local em JSON
    adicionar_ao_historico(match_id, nome_jogo, url)
    
    return {"match_id": match_id, "event": event}

def calcular_ap1_ap2(match_id: str, minuto_atual: int) -> dict:
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/graph"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    ap_data = {
        "ap1_home": 0.0,
        "ap1_away": 0.0,
        "ap2_home": 0.0,
        "ap2_away": 0.0
    }
    
    if match_id == "offline_sim":
        ap_data["ap1_home"] = 65.0
        ap_data["ap1_away"] = 30.0
        ap_data["ap2_home"] = 80.0
        ap_data["ap2_away"] = 15.0
        return ap_data
        
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            dados = r.json()
            pts = dados.get("graphPoints", [])
            
            pts_valido = [p for p in pts if p.get("minute", 0) <= minuto_atual]
            
            pts_10 = [p for p in pts_valido if p.get("minute", 0) >= max(0, minuto_atual - 10)]
            if pts_10:
                h10 = sum(p.get("value", 0) for p in pts_10 if p.get("value", 0) > 0)
                a10 = sum(abs(p.get("value", 0)) for p in pts_10 if p.get("value", 0) < 0)
                ap_data["ap1_home"] = min(100.0, (h10 / 10.0) * 3.5)
                ap_data["ap1_away"] = min(100.0, (a10 / 10.0) * 3.5)
                
            pts_5 = [p for p in pts_valido if p.get("minute", 0) >= max(0, minuto_atual - 5)]
            if pts_5:
                h5 = sum(p.get("value", 0) for p in pts_5 if p.get("value", 0) > 0)
                a5 = sum(abs(p.get("value", 0)) for p in pts_5 if p.get("value", 0) < 0)
                ap_data["ap2_home"] = min(100.0, (h5 / 5.0) * 4.5)
                ap_data["ap2_away"] = min(100.0, (a5 / 5.0) * 4.5)
    except Exception as e:
        print(f"Erro ao calcular AP1/AP2: {e}")
        
    return ap_data

@app.get("/api/jogo/estatisticas/{match_id}")
def obter_estatisticas(match_id: str, periodo: str = "ALL", minuto: Optional[int] = None):
    chaves = carregar_chaves()
    
    api_url_ev = f"https://sofascore-sport-api.p.rapidapi.com/api/event/{match_id}"
    dados_ev, _ = realizar_requisicao(api_url_ev, chaves)
    
    api_url_stat = f"https://sofascore-sport-api.p.rapidapi.com/api/event/{match_id}/statistics"
    dados_stat, _ = realizar_requisicao(api_url_stat, chaves)
    
    if not dados_stat:
        raise HTTPException(status_code=502, detail="Erro nas estatísticas da API")
        
    return processar_estatisticas(dados_ev, dados_stat, periodo, minuto, match_id)

def processar_estatisticas(dados_ev, dados_stat, periodo_selecionado, minuto_manual=None, match_id="offline_sim"):
    event = dados_ev.get("event", {}) if dados_ev else {}
    home_name = event.get("homeTeam", {}).get("name", "CASA")
    away_name = event.get("awayTeam", {}).get("name", "VISITANTE")
    g_casa = event.get("homeScore", {}).get("current", 0)
    g_fora = event.get("awayScore", {}).get("current", 0)
    gols_atuais = g_casa + g_fora

    minuto_atual = 45
    status_match = event.get("status", {})
    if status_match.get("type", "") == "inprogress":
        nums = re.findall(r"\d+", status_match.get("description", "45"))
        minuto_atual = int(nums[0]) if nums else 45

    if minuto_manual is not None:
        minuto_atual = minuto_manual

    metricas_traduzidas = []
    m_dict = {}

    for p in dados_stat.get("statistics", []):
        if p.get("period") == periodo_selecionado:
            for grupo in p.get("groups", []):
                for item in grupo.get("statisticsItems", []):
                    name = item.get("name")
                    traduzido = DICIONARIO_TRADUCOES.get(name, name)
                    home = item.get("home", str(item.get("homeValue", 0)))
                    away = item.get("away", str(item.get("awayValue", 0)))
                    key = item.get("key")

                    home_val = float(item.get("homeValue", 0))
                    away_val = float(item.get("awayValue", 0))
                    m_dict[key] = {"home": home_val, "away": away_val}

                    metricas_traduzidas.append({
                        "grupo": grupo.get("groupName", "Geral"),
                        "nome": traduzido,
                        "home": home,
                        "away": away,
                        "home_val": home_val,
                        "away_val": away_val
                    })

    analise = calcular_analise(m_dict, minuto_atual, gols_atuais)
    ap_data = calcular_ap1_ap2(match_id, minuto_atual)

    # Enviar alertas do Telegram se configurado e habilitado
    tg_cfg = carregar_telegram_config()
    if tg_cfg.get("enabled") and tg_cfg.get("token") and tg_cfg.get("chat_id"):
        for sug in analise.get("sugestoes", []):
            prob = sug.get("probabilidade", 0)
            if prob >= tg_cfg.get("min_prob", 70):
                chave_alerta = f"{match_id}_{sug.get('mercado')}_{sug.get('selecao')}"
                if chave_alerta not in ALERTAS_ENVIADOS:
                    ALERTAS_ENVIADOS.add(chave_alerta)
                    txt = (
                        f"🚨 *NOVO SINAL PREDATOR* 🚨\n\n"
                        f"🏟️ *Jogo:* {home_name} x {away_name}\n"
                        f"⏱️ *Tempo:* {minuto_atual}' (Placar: {g_casa} - {g_fora})\n"
                        f"📊 *Mercado:* {sug.get('mercado')}\n"
                        f"🎯 *Entrada:* `{sug.get('selecao')}`\n"
                        f"📈 *Confiança:* {prob}%\n"
                        f"🔥 *Odd Justa:* {sug.get('odd_justa')}\n"
                        f"⚡ *AP1 (C/V):* {ap_data['ap1_home']:.0f}% | {ap_data['ap1_away']:.0f}%\n"
                        f"⚡ *AP2 (C/V):* {ap_data['ap2_home']:.0f}% | {ap_data['ap2_away']:.0f}%\n\n"
                        f"💡 *Raciocínio:* {sug.get('raciocinio')}"
                    )
                    url_tg = f"https://api.telegram.org/bot{tg_cfg['token']}/sendMessage"
                    try:
                        requests.post(url_tg, json={"chat_id": tg_cfg["chat_id"], "text": txt, "parse_mode": "Markdown"}, timeout=5)
                    except Exception as tg_err:
                        print(f"Erro ao enviar sinal para Telegram: {tg_err}")

    return {
        "home": home_name,
        "away": away_name,
        "placar": f"{g_casa} - {g_fora}",
        "gols_atuais": gols_atuais,
        "minuto": minuto_atual,
        "estatisticas": metricas_traduzidas,
        "analise": analise,
        "ap": ap_data
    }


def calcular_analise(m, minuto, gols_atuais):
    def v(k, side="home"): return m[k][side] if k in m else 0.0
    def prob_mais_um(lmbda): return max(0.03, min(0.95, 1.0 - math.exp(-max(lmbda, 0.0))))
    def odd(prob): return 99.0 if prob <= 0 else 1.0 / prob

    minuto_calc = max(float(minuto), 1.0)
    restante = max(90.0 - minuto_calc, 0.0)
    janela10 = min(10.0, restante)

    # Coleta de dados
    xg_c, xg_v = v("expectedGoals"), v("expectedGoals", "away")
    alvo_c, alvo_v = v("shotsOnGoal"), v("shotsOnGoal", "away")
    box_c, box_v = v("totalShotsInsideBox"), v("totalShotsInsideBox", "away")
    chances_c, chances_v = v("bigChanceCreated"), v("bigChanceCreated", "away")
    toques_c, toques_v = v("touchesInOppBox"), v("touchesInOppBox", "away")
    entradas_c, entradas_v = v("finalThirdEntries"), v("finalThirdEntries", "away")
    cantos_c, cantos_v = v("cornerKicks"), v("cornerKicks", "away")
    bloqueados = v("blockedScoringAttempt") + v("blockedScoringAttempt", "away")
    cartoes = v("yellowCards") + v("yellowCards", "away")
    faltas = v("fouls") + v("fouls", "away")

    total_xg = xg_c + xg_v
    total_alvo = alvo_c + alvo_v
    total_chances = chances_c + chances_v
    total_box = box_c + box_v
    total_toques = toques_c + toques_v
    total_cantos = cantos_c + cantos_v

    # Modelo calibrado com decaimento exponencial do tempo e ponderações mais rígidas
    # Evita inflar quando o placar está 0x0
    taxa_pressao = ((total_xg * 0.4) + (total_alvo * 0.1) + (total_box * 0.05) + (total_chances * 0.15)) / minuto_calc
    
    # Se está 0-0 aos 60 minutos com baixo xG, a projeção de novos gols deve cair drasticamente
    fator_ritmo = 0.5 if (gols_atuais == 0 and total_xg < 1.0) else 1.0
    
    gols_rest = max(0.01, (taxa_pressao * restante * 0.45 * fator_ritmo))
    cantos_rest = max(0.05, (((total_cantos * 0.65) + (bloqueados * 0.15)) / minuto_calc) * restante * 0.8)
    cartoes_rest = max(0.02, (((cartoes * 0.8) + (faltas * 0.05)) / minuto_calc) * restante)

    prob_gol = prob_mais_um(gols_rest)
    prob_canto_10 = prob_mais_um(cantos_rest * (janela10 / max(restante, 1.0)))
    prob_cartao = prob_mais_um(cartoes_rest)

    # Linhas de Handicap de acordo com o cenário real
    linha_gols = max(gols_atuais + 0.5, gols_atuais + 0.5 if gols_rest > 0.4 else gols_atuais)
    linha_cantos = max(total_cantos + 0.5, math.floor(total_cantos + cantos_rest) + 0.5)
    linha_cartoes = max(cartoes + 0.5, math.floor(cartoes + cartoes_rest) + 0.5)

    return {
        "proj_gols": f"+{gols_rest:.2f}",
        "proj_cantos": f"+{cantos_rest:.1f}",
        "sugestoes": [
            {
                "mercado": "Mais Gols na Partida",
                "selecao": f"Over {linha_gols:.1f}",
                "probabilidade": int(prob_gol * 100),
                "odd_justa": f"{odd(prob_gol):.2f}",
                "raciocinio": f"Projeção de gols para os minutos finais: +{gols_rest:.2f} gols. Ritmo do jogo considerado."
            },
            {
                "mercado": "Total de Escanteios",
                "selecao": f"Over {linha_cantos:.1f}",
                "probabilidade": int(prob_mais_um(cantos_rest * 0.55) * 100),
                "odd_justa": f"{odd(prob_mais_um(cantos_rest * 0.55)):.2f}",
                "raciocinio": f"Média ativa de cantos. Estimados +{cantos_rest:.1f} escanteios até o fim."
            },
            {
                "mercado": "Escanteio nos Próximos 10 Minutos",
                "selecao": "Over 0.5 Cantos (10 Min)",
                "probabilidade": int(prob_canto_10 * 100),
                "odd_justa": f"{odd(prob_canto_10):.2f}",
                "raciocinio": "Frequência projetada de volume de ataque no terço final nas janelas dinâmicas."
            },
            {
                "mercado": "Cartões Totais",
                "selecao": f"Over {linha_cartoes:.1f}",
                "probabilidade": int(prob_cartao * 100),
                "odd_justa": f"{odd(prob_cartao):.2f}",
                "raciocinio": f"Tendência disciplinar. Faltas ativas sugerem cartões adicionais."
            }
        ]
    }

@app.post("/api/jogo/simular")
def simular_jogo_local():
    caminho = "a.json"
    if not os.path.exists(caminho):
         raise HTTPException(status_code=404, detail="Arquivo a.json não encontrado localmente")
    with open(caminho, "r", encoding="utf-8") as f:
        dados_stat = json.load(f)
    
    dados_ev = {
        "event": {
            "homeTeam": {"name": "CASA (SIMULADO)"},
            "awayTeam": {"name": "VISITANTE (SIMULADO)"},
            "homeScore": {"current": 3},
            "awayScore": {"current": 2},
            "status": {"type": "inprogress", "description": "72'"}
        }
    }
    return processar_estatisticas(dados_ev, dados_stat, "ALL")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
