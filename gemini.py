import tkinter as tk
from tkinter import ttk, messagebox
import json
import math
import os
import re
import requests

FICHEIRO_CHAVES = "chaves_api.txt"

# Dicionário de tradução das estatísticas do Sofascore
DICIONARIO_TRADUCOES = {
    # Match Overview
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
    
    # Shots
    "Shots on target": "Chutes no Alvo",
    "Hit woodwork": "Bolas na Trave",
    "Shots off target": "Chutes Fora",
    "Blocked shots": "Chutes Bloqueados",
    "Shots inside box": "Chutes Dentro da Área",
    "Shots outside box": "Chutes Fora da Área",
    
    # Attack
    "Big chances scored": "Grandes Chances Marcadas",
    "Big chances missed": "Grandes Chances Perdidas",
    "Through balls": "Bolas Enfadas",
    "Touches in penalty area": "Toques na Área Adversária",
    "Fouled in final third": "Faltas Sofridas no Último Terço",
    "Offsides": "Impedimentos",
    
    # Passes
    "Accurate passes": "Passes Certos",
    "Throw-ins": "Arremessos Laterais",
    "Final third entries": "Entradas no Último Terço",
    "Final third phase": "Fase do Último Terço",
    "Long balls": "Lançamentos/Bolas Longas",
    "Crosses": "Cruzamentos",
    
    # Duels
    "Duels": "Duelos",
    "Dispossessed": "Desarmado",
    "Ground duels": "Duelos Chão",
    "Aerial duels": "Duelos Aéreos",
    "Dribbles": "Dribbles",
    
    # Defending
    "Tackles won": "Desarmes Ganhos",
    "Total tackles": "Total de Desarmes",
    "Interceptions": "Interceptações",
    "Recoveries": "Recuperações de Bola",
    "Clearances": "Cortes / Afastadas",
    "Errors lead to a shot": "Erros que Geraram Chute",
    
    # Goalkeeping
    "Total saves": "Total de Defesas",
    "Goals prevented": "Gols Evitados",
    "Big saves": "Defesas Difíceis",
    "High claims": "Bolas Altas Capturadas",
    "Punches": "Socos na Bola",
    "Goal kicks": "Tiros de Meta",
    "Distance covered": "Distância Percorrida",
    "Number of sprints": "Número de Sprints"
}

def traduzir_parametro(nome_original):
    return DICIONARIO_TRADUCOES.get(nome_original, nome_original)

def extrair_id_sofascore(url):
    if not url: return "15186905"
    match = re.search(r"id:(\d+)", url)
    if match: return match.group(1)
    numeros = re.findall(r"\d+", url)
    return numeros[-1] if numeros else "15186905"

class JogoAba:
    """Classe que representa a aba de um jogo individual."""
    def __init__(self, notebook, parent_app, match_id, nome_exibicao):
        self.notebook = notebook
        self.parent_app = parent_app
        self.match_id = match_id
        self.nome_exibicao = nome_exibicao
        
        self.minuto_atual_jogo = 45
        self.minuto_manual_ativo = False
        self.gols_atuais = 0
        self.dados_atuais = {}
        
        # Criação do frame da aba
        self.frame = tk.Frame(self.notebook, bg="#0d0e15")
        self.notebook.add(self.frame, text=nome_exibicao)
        
        self.criar_widgets_aba()

    def criar_widgets_aba(self):
        # 1. Painel de Status/Placar com Design Premium
        score_bg = "#161824"
        self.score_frame = tk.Frame(self.frame, bg=score_bg, bd=0)
        self.score_frame.pack(fill="x", padx=15, pady=10, ipady=10)
        
        # Grid para o placar e cronômetro
        self.score_frame.columnconfigure(0, weight=3)
        self.score_frame.columnconfigure(1, weight=1)
        self.score_frame.columnconfigure(2, weight=3)
        
        self.lbl_time_casa = tk.Label(self.score_frame, text="MANDANTE", bg=score_bg, fg="#89b4fa", font=("Outfit", 15, "bold"))
        self.lbl_time_casa.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_placar = tk.Label(self.score_frame, text="0 - 0", bg=score_bg, fg="#f38ba8", font=("Outfit", 24, "bold"))
        self.lbl_placar.grid(row=0, column=1, sticky="nsew")
        
        self.lbl_time_fora = tk.Label(self.score_frame, text="VISITANTE", bg=score_bg, fg="#f9e2af", font=("Outfit", 15, "bold"))
        self.lbl_time_fora.grid(row=0, column=2, sticky="nsew")
        
        self.lbl_tempo_jogo = tk.Label(self.score_frame, text="AGUARDANDO DADOS...", bg=score_bg, fg="#a6e3a1", font=("Consolas", 11, "bold"))
        self.lbl_tempo_jogo.grid(row=1, column=0, columnspan=3, pady=(5, 0))

        # Controles rápidos por Aba
        ctrl_frame = tk.Frame(self.frame, bg="#0d0e15")
        ctrl_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(ctrl_frame, text="Minuto Atual:", bg="#0d0e15", fg="#bac2de", font=("Arial", 9, "bold")).pack(side="left")
        self.ent_minuto = tk.Entry(ctrl_frame, width=5, bg="#161824", fg="#cdd6f4", bd=0, justify="center", font=("Arial", 10, "bold"), insertbackground="white")
        self.ent_minuto.insert(0, str(self.minuto_atual_jogo))
        self.ent_minuto.pack(side="left", padx=5, ipady=3)
        self.ent_minuto.bind("<Return>", lambda e: self.aplicar_minuto_manual())
        
        btn_calc = tk.Button(ctrl_frame, text="Definir Minuto", bg="#89b4fa", fg="#11111b", font=("Arial", 8, "bold"), bd=0, cursor="hand2", command=self.aplicar_minuto_manual)
        btn_calc.pack(side="left", padx=3, ipady=2, ipadx=5)
        
        btn_auto = tk.Button(ctrl_frame, text="Auto (API)", bg="#313244", fg="#cdd6f4", font=("Arial", 8, "bold"), bd=0, cursor="hand2", command=self.voltar_minuto_auto)
        btn_auto.pack(side="left", padx=3, ipady=2, ipadx=5)
        
        btn_remover = tk.Button(ctrl_frame, text="Fechar Jogo", bg="#f38ba8", fg="#11111b", font=("Arial", 8, "bold"), bd=0, cursor="hand2", command=self.fechar_aba)
        btn_remover.pack(side="right", padx=3, ipady=2, ipadx=5)

        # 2. Divisão da Tela: Dados x Sugestões
        paned = ttk.Panedwindow(self.frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Sub-frame Esquerda (Matriz)
        left_sub = tk.LabelFrame(paned, text=" Estatísticas Traduzidas ", bg="#161824", fg="#f5c2e7", font=("Outfit", 10, "bold"), bd=1, labelanchor="n")
        paned.add(left_sub, weight=3)
        
        self.tree = ttk.Treeview(left_sub, columns=("Home", "Item", "Away"), show="headings")
        self.tree.heading("Home", text="CASA")
        self.tree.heading("Item", text="ESTATÍSTICA")
        self.tree.heading("Away", text="VISITANTE")
        self.tree.column("Home", anchor="center", width=70)
        self.tree.column("Item", anchor="w", width=200)
        self.tree.column("Away", anchor="center", width=70)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Sub-frame Direita (Sugestões)
        right_sub = tk.LabelFrame(paned, text=" Análise de Cenário & Entradas sugeridas ", bg="#161824", fg="#f9e2af", font=("Outfit", 10, "bold"), bd=1, labelanchor="n")
        paned.add(right_sub, weight=2)
        
        self.txt_sugestoes = tk.Text(right_sub, bg="#11111b", fg="#cdd6f4", font=("Consolas", 10), bd=0, wrap="word")
        self.txt_sugestoes.pack(fill="both", expand=True, padx=8, pady=8)

    def aplicar_minuto_manual(self):
        valor = self.ent_minuto.get().strip()
        try:
            minuto = float(valor)
            if 0 <= minuto <= 130:
                self.minuto_atual_jogo = minuto
                self.minuto_manual_ativo = True
                self.lbl_tempo_jogo.config(text=f"MINUTO MANUAL: {minuto:.0f}' | RESTANTE: {self.minutos_restantes():.0f} MIN", fg="#f9e2af")
                self.renderizar_dados_tela()
        except ValueError:
            pass

    def voltar_minuto_auto(self):
        self.minuto_manual_ativo = False
        self.parent_app.requisitar_e_atualizar_dados_jogo(self)

    def minutos_restantes(self):
        return max(90.0 - float(self.minuto_atual_jogo), 0.0)

    def fechar_aba(self):
        # Remove a aba do notebook e o registro do app
        self.notebook.forget(self.frame)
        self.parent_app.remover_jogo_da_lista(self.match_id)

    def renderizar_dados_tela(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not self.dados_atuais or "statistics" not in self.dados_atuais: 
            return

        self.txt_sugestoes.delete("1.0", tk.END)
        periodo_selecionado = self.parent_app.obter_periodo_filtro()
        metricas = {}

        for p in self.dados_atuais.get("statistics", []):
            if p.get("period") == periodo_selecionado:
                for grupo in p.get("groups", []):
                    for item in grupo.get("statisticsItems", []):
                        name = item.get("name")
                        traduzido = traduzir_parametro(name)
                        home = item.get("home", str(item.get("homeValue", 0)))
                        away = item.get("away", str(item.get("awayValue", 0)))
                        key = item.get("key")

                        metricas[key] = {
                            "home_val": float(item.get("homeValue", 0)),
                            "away_val": float(item.get("awayValue", 0))
                        }
                        self.tree.insert("", "end", values=(home, f"[{grupo['groupName']}] {traduzido}", away))

        if metricas:
            self.calcular_veredito_operacional(metricas)

    def calcular_veredito_operacional(self, m):
        def v(k, side="home_val"): return m[k][side] if k in m else 0.0
        def prob_mais_um(lmbda): return max(0.03, min(0.94, 1.0 - math.exp(-max(lmbda, 0.0))))
        def odd(prob): return 99.0 if prob <= 0 else 1.0 / prob
        
        def nivel_estilizado(prob):
            if prob >= 0.68: return "🟢 FORTE"
            if prob >= 0.56: return "🟡 BOA"
            if prob >= 0.48: return "⚪ OBSERVAR"
            return "🔴 FRACA"

        def linha(txt=""): self.txt_sugestoes.insert(tk.END, txt + "\n")
        
        def dica(mercado, selecao, prob, motivo):
            linha(f" {nivel_estilizado(prob):<11} | {mercado}")
            linha(f"   👉 Seleção: {selecao}")
            linha(f"   📊 Probabilidade: {prob * 100:.0f}% | Odd Mínima Ideal: {odd(prob):.2f}")
            linha(f"   💡 Raciocínio: {motivo}")
            linha()

        xg_c, xg_v = v("expectedGoals"), v("expectedGoals", "away_val")
        alvo_c, alvo_v = v("shotsOnGoal"), v("shotsOnGoal", "away_val")
        tiros_c, tiros_v = v("totalShotsOnGoal"), v("totalShotsOnGoal", "away_val")
        box_c, box_v = v("totalShotsInsideBox"), v("totalShotsInsideBox", "away_val")
        chances_c, chances_v = v("bigChanceCreated"), v("bigChanceCreated", "away_val")
        toques_c, toques_v = v("touchesInOppBox"), v("touchesInOppBox", "away_val")
        entradas_c, entradas_v = v("finalThirdEntries"), v("finalThirdEntries", "away_val")
        cantos_c, cantos_v = v("cornerKicks"), v("cornerKicks", "away_val")
        bloqueados = v("blockedScoringAttempt") + v("blockedScoringAttempt", "away_val")
        cartoes = v("yellowCards") + v("yellowCards", "away_val")
        faltas = v("fouls") + v("fouls", "away_val")

        minuto = max(float(self.minuto_atual_jogo), 1.0)
        restante = self.minutos_restantes()
        janela10 = min(10.0, restante)
        fator_fim = 1.18 if minuto >= 75 else 1.08 if minuto >= 60 else 1.0

        total_xg = xg_c + xg_v
        total_alvo = alvo_c + alvo_v
        total_chances = chances_c + chances_v
        total_box = box_c + box_v
        total_toques = toques_c + toques_v
        total_entradas = entradas_c + entradas_v
        total_cantos = cantos_c + cantos_v

        perigo_c = (xg_c * 18) + (alvo_c * 3) + (box_c * 1.4) + (toques_c * 0.35) + (entradas_c * 0.18) + (chances_c * 5)
        perigo_v = (xg_v * 18) + (alvo_v * 3) + (box_v * 1.4) + (toques_v * 0.35) + (entradas_v * 0.18) + (chances_v * 5)

        gols_rest = min(3.2, max(0.03, (((total_xg * 0.62) + (total_alvo * 0.09) + (total_box * 0.035) + (total_chances * 0.16) + (total_toques * 0.012)) / minuto) * restante * fator_fim * 0.58))
        cantos_rest = min(5.5, max(0.05, (((total_cantos * 0.75) + (bloqueados * 0.22) + (total_entradas * 0.035)) / minuto) * restante * 0.72))
        cartoes_rest = min(3.8, max(0.02, (((cartoes * 0.85) + (faltas * 0.08)) / minuto) * restante * (1.22 if minuto >= 65 else 1.0) * 0.78))

        prob_gol = prob_mais_um(gols_rest)
        prob_canto_10 = prob_mais_um(cantos_rest * (janela10 / max(restante, 1.0)))

        linha_gols = max(self.gols_atuais + 0.5, math.floor(self.gols_atuais + gols_rest) + 0.5)
        linha_cantos = max(total_cantos + 0.5, math.floor(total_cantos + cantos_rest) + 0.5)
        linha_cartoes = max(cartoes + 0.5, math.floor(cartoes + cartoes_rest) + 0.5)

        # Renderização do Relatório
        linha("=" * 60)
        linha("              PREDATOR OPERATIONAL ANALYSIS")
        linha("=" * 60)
        linha(f"Tempo: {minuto:.0f}' | Restante: {restante:.0f} min | Placar Atual: {self.gols_atuais} gols")
        linha(f"Projeção até 90': +{gols_rest:.2f} gols | +{cantos_rest:.1f} cantos")
        linha("-" * 60)
        linha()

        linha("🔥 SUGESTÕES DETECTADAS:")
        linha()
        dica("Mais Gols na Partida", f"Over {linha_gols:.1f}", max(0.03, min(0.94, prob_gol * 0.72)), f"Expectativa de Gols do Modelo é {gols_rest:.2f} gols no restante.")
        dica("Total de Escanteios", f"Over {linha_cantos:.1f}", prob_mais_um(cantos_rest * 0.55), f"Frequência ativa de ataques com {total_cantos:.0f} escanteios já cobrados.")
        dica("Escanteio Próximos 10 Minutos", "Over 0.5 Cantos (10 Min)", prob_canto_10, f"Pressão no último terço ({total_entradas:.0f} entradas) com bola na caixa.")
        dica("Cartões Totais", f"Over {linha_cartoes:.1f}", prob_mais_um(cartoes_rest * 0.55), f"Média alta de faltas e cartões ativos ({cartoes:.0f} cartões).")
        linha("=" * 60)

class AppLiveScannerPredator:
    def __init__(self, root):
        self.root = root
        self.root.title("PREDATOR LIVE SCANNER - Pro")
        self.root.geometry("1380x880")
        self.root.configure(bg="#0b0b11")

        self.abas_jogos = {} # match_id -> JogoAba
        self.lista_chaves = self.carregar_chaves_locais()
        self.chave_atual_index = 0

        self.configurar_estilos()
        self.criar_widgets_principais()
        self.atualizar_combobox_chaves()

    def carregar_chaves_locais(self):
        if os.path.exists(FICHEIRO_CHAVES):
            with open(FICHEIRO_CHAVES, "r", encoding="utf-8") as f:
                chaves = [linha.strip() for list_linha in f if (linha := list_linha.strip())]
                if chaves:
                    return chaves
        return ["c7d04000d0msh3f6770ff746185fp1e7485jsn84e83064e659"]

    def salvar_chaves_locais(self):
        with open(FICHEIRO_CHAVES, "w", encoding="utf-8") as f:
            for chave in self.lista_chaves:
                f.write(f"{chave}\n")

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Tema Escuro moderno
        style.configure(".", background="#0d0e15", foreground="#cdd6f4")
        style.configure("TLabel", background="#0d0e15", foreground="#cdd6f4")
        style.configure("TCombobox", fieldbackground="#161824", background="#313244", foreground="#cdd6f4")
        
        # Estilização das abas (Notebook)
        style.configure("TNotebook", background="#0d0e15", borderwidth=0)
        style.configure("TNotebook.Tab", background="#161824", foreground="#a6adc8", font=("Outfit", 10, "bold"), padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", "#0d0e15")], foreground=[("selected", "#a6e3a1")])
        
        # Estilo Treeview
        style.configure("Treeview", background="#161824", foreground="#cdd6f4", fieldbackground="#161824", rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background="#313244", foreground="#a6e3a1", font=("Outfit", 9, "bold"))
        style.map("Treeview", background=[("selected", "#313244")])

    def criar_widgets_principais(self):
        # 1. Barra de Controles Superior
        top_frame = tk.Frame(self.root, bg="#11111b", bd=0)
        top_frame.pack(fill="x", padx=15, pady=10, ipady=8)

        tk.Label(top_frame, text="URL SOFASCORE:", bg="#11111b", fg="#bac2de", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 5))
        self.ent_url = tk.Entry(top_frame, width=35, bg="#161824", fg="#cdd6f4", insertbackground="white", bd=0, font=("Arial", 10))
        self.ent_url.pack(side="left", padx=5, ipady=4)

        btn_adicionar = tk.Button(top_frame, text="+ ADICIONAR JOGO", bg="#a6e3a1", fg="#11111b", font=("Arial", 9, "bold"), bd=0, cursor="hand2", command=self.adicionar_novo_jogo)
        btn_adicionar.pack(side="left", padx=10, ipady=3, ipadx=8)

        # Filtro de Período
        tk.Label(top_frame, text="PERÍODO:", bg="#11111b", fg="#bac2de", font=("Arial", 9, "bold")).pack(side="left", padx=(20, 5))
        self.cbo_periodo = ttk.Combobox(top_frame, values=["ALL", "1ST", "2ND"], width=6, state="readonly")
        self.cbo_periodo.set("ALL")
        self.cbo_periodo.pack(side="left", padx=5)
        self.cbo_periodo.bind("<<ComboboxSelected>>", lambda e: self.re_renderizar_todos_jogos())

        btn_json = tk.Button(top_frame, text="CARREGAR JSON LOCAL", bg="#f9e2af", fg="#11111b", font=("Arial", 9, "bold"), bd=0, cursor="hand2", command=self.carregar_json_local)
        btn_json.pack(side="left", padx=(20, 5), ipady=3, ipadx=8)

        # Painel de API no topo à direita
        api_frame = tk.Frame(top_frame, bg="#11111b")
        api_frame.pack(side="right", padx=10)

        self.cbo_chaves_salvas = ttk.Combobox(api_frame, values=[], width=22, state="readonly", font=("Consolas", 8))
        self.cbo_chaves_salvas.pack(side="left", padx=5)
        
        btn_del_key = tk.Button(api_frame, text="REMOVER KEY", bg="#f38ba8", fg="#11111b", font=("Arial", 8, "bold"), bd=0, command=self.remover_chave_lista)
        btn_del_key.pack(side="left", padx=2)

        # Entrada para nova API Key
        self.ent_nova_chave = tk.Entry(api_frame, width=15, bg="#161824", fg="#cdd6f4", insertbackground="white", bd=0, font=("Consolas", 8))
        self.ent_nova_chave.pack(side="left", padx=5, ipady=3)
        self.ent_nova_chave.insert(0, "Nova API Key...")
        self.ent_nova_chave.bind("<FocusIn>", lambda e: self.ent_nova_chave.delete(0, tk.END) if self.ent_nova_chave.get() == "Nova API Key..." else None)

        btn_add_key = tk.Button(api_frame, text="+ SALVAR KEY", bg="#a6e3a1", fg="#11111b", font=("Arial", 8, "bold"), bd=0, command=self.adicionar_chave_lista)
        btn_add_key.pack(side="left", padx=2)

        # 2. Notebook para as Abas de Jogos
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def obter_periodo_filtro(self):
        return self.cbo_periodo.get()

    def re_renderizar_todos_jogos(self):
        for aba in self.abas_jogos.values():
            aba.renderizar_dados_tela()

    def remover_jogo_da_lista(self, match_id):
        if match_id in self.abas_jogos:
            del self.abas_jogos[match_id]

    def adicionar_chave_lista(self):
        nova_key = self.ent_nova_chave.get().strip()
        if not nova_key or nova_key == "Nova API Key...":
            messagebox.showwarning("Aviso", "Introduza uma chave API válida.")
            return
        if nova_key in self.lista_chaves:
            messagebox.showinfo("Informação", "Esta chave já existe.")
            return
        self.lista_chaves.append(nova_key)
        self.salvar_chaves_locais()
        self.atualizar_combobox_chaves()
        self.ent_nova_chave.delete(0, tk.END)
        messagebox.showinfo("Sucesso", "Chave API salva com sucesso!")

    def remover_chave_lista(self):
        selecionada = self.cbo_chaves_salvas.get()
        if not selecionada: return
        chave_limpa = selecionada.split(" - ")[1]
        if len(self.lista_chaves) <= 1:
            messagebox.showwarning("Aviso", "Você precisa de ter pelo menos uma chave.")
            return
        self.lista_chaves.remove(chave_limpa)
        self.salvar_chaves_locais()
        self.chave_atual_index = 0
        self.atualizar_combobox_chaves()

    def atualizar_combobox_chaves(self):
        valores = [f"Pos {i+1} - {key[:8]}...{key[-5:]}" for i, key in enumerate(self.lista_chaves)]
        self.cbo_chaves_salvas["values"] = valores
        if valores:
            self.cbo_chaves_salvas.current(min(self.chave_atual_index, len(valores)-1))

    def obter_chave_ativa(self):
        if 0 <= self.chave_atual_index < len(self.lista_chaves):
            return self.lista_chaves[self.chave_atual_index]
        return self.lista_chaves[0]

    def rotacionar_chave_api(self):
        self.chave_atual_index += 1
        if self.chave_atual_index >= len(self.lista_chaves):
            self.chave_atual_index = 0
            return False
        self.atualizar_combobox_chaves()
        return True

    def realizar_requisicao_segura(self, url):
        tentativas = 0
        max_tentativas = len(self.lista_chaves)
        while tentativas < max_tentativas:
            chave = self.obter_chave_ativa()
            headers = {
                "x-rapidapi-host": "sofascore-sport-api.p.rapidapi.com",
                "x-rapidapi-key": chave
            }
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    return res
                elif res.status_code in [401, 403, 429]:
                    print(f"⚠️ Rotação de chave ativada...")
                    if not self.rotacionar_chave_api():
                        break
                else:
                    return res
            except Exception as e:
                print(f"❌ Erro de conexão com a chave atual: {e}")
                if not self.rotacionar_chave_api():
                    break
            tentativas += 1
        return None

    def adicionar_novo_jogo(self):
        url = self.ent_url.get().strip()
        if not url: return

        match_id = extrair_id_sofascore(url)
        if match_id in self.abas_jogos:
            messagebox.showinfo("Informação", "Este jogo já está aberto em uma aba.")
            return

        nome_exibicao = f"Jogo ({match_id})"
        if match_id != "15186905":
            api_url = f"https://sofascore-sport-api.p.rapidapi.com/api/event/{match_id}"
            res = self.realizar_requisicao_segura(api_url)
            if res and res.status_code == 200:
                ev = res.json().get("event", {})
                casa = ev.get("homeTeam", {}).get("shortName", "Casa")
                fora = ev.get("awayTeam", {}).get("shortName", "Fora")
                nome_exibicao = f"{casa} x {fora}"

        # Criar a nova aba para o jogo
        nova_aba = JogoAba(self.notebook, self, match_id, nome_exibicao)
        self.abas_jogos[match_id] = nova_aba
        self.ent_url.delete(0, tk.END)

        # Focar na nova aba criada
        self.notebook.select(nova_aba.frame)
        self.requisitar_e_atualizar_dados_jogo(nova_aba)

    def requisitar_e_atualizar_dados_jogo(self, aba):
        if not aba.match_id: return

        minuto_atual = aba.minuto_atual_jogo
        api_url_ev = f"https://sofascore-sport-api.p.rapidapi.com/api/event/{aba.match_id}"
        
        res_ev = self.realizar_requisicao_segura(api_url_ev)
        if res_ev and res_ev.status_code == 200:
            ev = res_ev.json().get("event", {})
            aba.lbl_time_casa.config(text=ev.get("homeTeam", {}).get("name", "CASA").upper())
            aba.lbl_time_fora.config(text=ev.get("awayTeam", {}).get("name", "FORA").upper())
            g_casa = ev.get("homeScore", {}).get("current", 0)
            g_fora = ev.get("awayScore", {}).get("current", 0)
            aba.gols_atuais = g_casa + g_fora
            aba.lbl_placar.config(text=f"{g_casa} - {g_fora}")

            status_match = ev.get("status", {})
            if status_match.get("type", "") == "inprogress":
                nums = re.findall(r"\d+", status_match.get("description", "45'"))
                minuto_atual = int(nums[0]) if nums else minuto_atual
                if not aba.minuto_manual_ativo:
                    aba.lbl_tempo_jogo.config(text=f"MINUTO: {minuto_atual}' | AO VIVO", fg="#a6e3a1")

        if not aba.minuto_manual_ativo:
            aba.minuto_atual_jogo = minuto_atual
            aba.ent_minuto.delete(0, tk.END)
            aba.ent_minuto.insert(0, str(int(float(minuto_atual))))

        api_url_stat = f"https://sofascore-sport-api.p.rapidapi.com/api/event/{aba.match_id}/statistics"
        res_stat = self.realizar_requisicao_segura(api_url_stat)
        if res_stat and res_stat.status_code == 200:
            aba.dados_atuais = res_stat.json()
        elif res_stat is None:
            aba.txt_sugestoes.delete("1.0", tk.END)
            aba.txt_sugestoes.insert(tk.END, "❌ TODAS AS CHAVES API FALHARAM.")

        aba.renderizar_dados_tela()

    def carregar_json_local(self):
        caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a.json")
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar a.json:\n{str(e)}")
            return

        # Abre uma aba offline de simulação
        match_id_offline = "offline_sim"
        if match_id_offline in self.abas_jogos:
            self.abas_jogos[match_id_offline].fechar_aba()

        aba_offline = JogoAba(self.notebook, self, match_id_offline, "offline_sim (Simulação)")
        aba_offline.dados_atuais = dados
        aba_offline.lbl_time_casa.config(text="CASA (JSON)")
        aba_offline.lbl_time_fora.config(text="VISITANTE (JSON)")
        aba_offline.lbl_placar.config(text="3 - 2")
        aba_offline.gols_atuais = 5
        aba_offline.minuto_atual_jogo = 72
        aba_offline.lbl_tempo_jogo.config(text="DADOS LOCAL CARREGADOS", fg="#f9e2af")
        
        self.abas_jogos[match_id_offline] = aba_offline
        self.notebook.select(aba_offline.frame)
        aba_offline.renderizar_dados_tela()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLiveScannerPredator(root)
    root.mainloop()