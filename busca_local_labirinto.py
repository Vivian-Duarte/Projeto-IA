"""
Parte III – Busca Local com Pontos de Coleta
============================================
Trabalho Prático – Agente Inteligente em Labirinto
Curso: Engenharia de Computação / Sistemas de Informação

Dependências:
    pip install matplotlib

Uso:
    python busca_local_labirinto.py mapa_coleta.txt
    python busca_local_labirinto.py mapa_coleta.txt --execucoes 30 --mostrar
    python busca_local_labirinto.py mapa_coleta.txt --saida resultados/ --mostrar

Formato do mapa (.txt):
    '#'  parede
    ' '  célula livre
    'A'  posição inicial
    'B'  objetivo final
    'C'  ponto de coleta obrigatório (pode haver vários)

Compatibilidade com ASCII Maze Generator (https://www.asciiart.eu/ascii-maze-generator):
    - Use o tema "Classic" ('#' para paredes, espaços para caminhos).
    - Substitua 'S' por 'A', 'E' por 'B' e adicione os pontos 'C' manualmente
      nas células livres do labirinto gerado.

O que este módulo implementa
-----------------------------
1. LabirintoColeta – lê o mapa, extrai pontos de coleta e pré-computa as
   distâncias mínimas entre todos os pontos relevantes via A*.
2. Hill-Climbing com reinício aleatório.
3. Simulated Annealing.
4. Métricas obrigatórias: melhor/pior/médio custo, tempo médio, iterações,
   curva de convergência e taxa de sucesso.
5. Visualização textual e gráficos Matplotlib (curva de convergência,
   boxplot de custos, comparativo de algoritmos).
6. Exportação de resultados em CSV.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
import random
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import heapq

Estado = Tuple[int, int]

ACOES = [
    ("cima",     (-1,  0)),
    ("baixo",    ( 1,  0)),
    ("esquerda", ( 0, -1)),
    ("direita",  ( 0,  1)),
]


@dataclass
class No:
    estado: Estado
    pai: Optional["No"] = None
    acao: Optional[str] = None
    g: float = 0.0

class LabirintoColeta:
    """
    Lê um labirinto com pontos de coleta obrigatórios ('C') e pré-computa
    as distâncias mínimas entre todos os pares relevantes:
        A ↔ Ci, Ci ↔ Cj, Ci ↔ B.

    A distância entre dois pontos é calculada por A* no grafo do labirinto.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.grade: List[List[str]] = []
        self.paredes: List[List[bool]] = []
        self.inicio: Estado
        self.objetivo: Estado
        self.coletas: List[Estado] = []          
        self._ler_mapa(filename)

        self.nos_relevantes: List[Estado] = (
            [self.inicio] + list(self.coletas) + [self.objetivo]
        )

        self.dist: Dict[Tuple[Estado, Estado], float] = {}
        self._precomputar_distancias()

    def _ler_mapa(self, filename: str) -> None:
        with open(filename, encoding="utf-8") as f:
            conteudo = f.read()

        linhas = conteudo.splitlines()
        while linhas and linhas[-1].strip() == "":
            linhas.pop()
        if not linhas:
            raise ValueError("Arquivo de labirinto vazio.")
        
        total_A = sum(l.count("A") for l in linhas)
        total_S = sum(l.count("S") for l in linhas)
        total_B = sum(l.count("B") for l in linhas)
        total_E = sum(l.count("E") for l in linhas)

        linhas_norm = []
        for linha in linhas:
            if total_A == 0 and total_S == 1:
                linha = linha.replace("S", "A")
            if total_B == 0 and total_E == 1:
                linha = linha.replace("E", "B")
            linhas_norm.append(linha)
        linhas = linhas_norm

        if sum(l.count("A") for l in linhas) != 1:
            raise ValueError("O labirinto deve ter exatamente um ponto 'A'.")
        if sum(l.count("B") for l in linhas) != 1:
            raise ValueError("O labirinto deve ter exatamente um ponto 'B'.")

        self.altura = len(linhas)
        self.largura = max(len(l) for l in linhas)

        coletas_raw: List[Estado] = []

        for i, linha in enumerate(linhas):
            linha = linha.ljust(self.largura, "#")
            row_grade: List[str] = []
            row_paredes: List[bool] = []

            for j, ch in enumerate(linha):
                if ch == "A":
                    self.inicio = (i, j)
                    row_grade.append("A")
                    row_paredes.append(False)
                elif ch == "B":
                    self.objetivo = (i, j)
                    row_grade.append("B")
                    row_paredes.append(False)
                elif ch == "C":
                    coletas_raw.append((i, j))
                    row_grade.append("C")
                    row_paredes.append(False)
                elif ch == "#":
                    row_grade.append("#")
                    row_paredes.append(True)
                else:
                    row_grade.append(ch)
                    row_paredes.append(False)

            self.grade.append(row_grade)
            self.paredes.append(row_paredes)

        if not coletas_raw:
            raise ValueError(
                "O mapa não tem pontos de coleta 'C'. "
                "A Parte III exige ao menos um ponto de coleta."
            )

        self.coletas = sorted(coletas_raw)

    def transitavel(self, estado: Estado) -> bool:
        l, c = estado
        return (
            0 <= l < self.altura
            and 0 <= c < self.largura
            and not self.paredes[l][c]
        )

    def vizinhos(self, estado: Estado) -> List[Tuple[str, Estado, float]]:
        l, c = estado
        resultado = []
        for acao, (dl, dc) in ACOES:
            prox = (l + dl, c + dc)
            if self.transitavel(prox):
                resultado.append((acao, prox, 1.0))
        return resultado

    def h_manhattan(self, a: Estado, b: Estado) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _a_estrela(self, origem: Estado, destino: Estado) -> float:
        """
        Retorna o custo do menor caminho entre origem e destino via A*.
        Retorna math.inf se não existir caminho.
        """
        contador = itertools.count()
        inicio = No(origem, g=0.0)
        fronteira: List[Tuple[float, int, No]] = []
        heapq.heappush(
            fronteira,
            (self.h_manhattan(origem, destino), next(contador), inicio),
        )
        fechados: Set[Estado] = set()
        melhor_g: Dict[Estado, float] = {origem: 0.0}

        while fronteira:
            _, _, no = heapq.heappop(fronteira)
            if no.estado in fechados:
                continue
            if no.estado == destino:
                return no.g
            fechados.add(no.estado)
            for _, prox, custo in self.vizinhos(no.estado):
                if prox in fechados:
                    continue
                novo_g = no.g + custo
                if novo_g < melhor_g.get(prox, math.inf):
                    filho = No(prox, pai=no, g=novo_g)
                    melhor_g[prox] = novo_g
                    heapq.heappush(
                        fronteira,
                        (
                            novo_g + self.h_manhattan(prox, destino),
                            next(contador),
                            filho,
                        ),
                    )
        return math.inf

    def _a_estrela_caminho(
        self, origem: Estado, destino: Estado
    ) -> List[Estado]:
        """
        Retorna a lista de estados do caminho ótimo de origem a destino.
        Retorna lista vazia se não houver caminho.
        """
        contador = itertools.count()
        inicio = No(origem, g=0.0)
        fronteira: List[Tuple[float, int, No]] = []
        heapq.heappush(
            fronteira,
            (self.h_manhattan(origem, destino), next(contador), inicio),
        )
        fechados: Set[Estado] = set()
        melhor_g: Dict[Estado, float] = {origem: 0.0}

        while fronteira:
            _, _, no = heapq.heappop(fronteira)
            if no.estado in fechados:
                continue
            if no.estado == destino:
                path: List[Estado] = []
                atual: Optional[No] = no
                while atual is not None:
                    path.append(atual.estado)
                    atual = atual.pai
                path.reverse()
                return path
            fechados.add(no.estado)
            for _, prox, custo in self.vizinhos(no.estado):
                if prox in fechados:
                    continue
                novo_g = no.g + custo
                if novo_g < melhor_g.get(prox, math.inf):
                    filho = No(prox, pai=no, g=novo_g)
                    melhor_g[prox] = novo_g
                    heapq.heappush(
                        fronteira,
                        (
                            novo_g + self.h_manhattan(prox, destino),
                            next(contador),
                            filho,
                        ),
                    )
        return []

    def _precomputar_distancias(self) -> None:
        """
        Calcula d(X, Y) para todos os pares relevantes (X, Y) onde
        X, Y ∈ {A, C1, …, Ck, B}.

        Complexity: O(n² × A*), onde n = 2 + k.
        Para labirintos razoáveis e k pequeno, isto é rápido.
        """
        nos = self.nos_relevantes
        for i in range(len(nos)):
            for j in range(len(nos)):
                if i != j:
                    par = (nos[i], nos[j])
                    if par not in self.dist:
                        self.dist[par] = self._a_estrela(nos[i], nos[j])

    def custo_solucao(self, permutacao: List[Estado]) -> float:
        """
        Recebe uma lista com a ordem de visitação dos pontos de coleta.
        Retorna math.inf se algum trecho for inacessível.
        """
        if not permutacao:
            return self.dist.get((self.inicio, self.objetivo), math.inf)

        custo = self.dist.get((self.inicio, permutacao[0]), math.inf)
        for i in range(len(permutacao) - 1):
            custo += self.dist.get(
                (permutacao[i], permutacao[i + 1]), math.inf
            )
        custo += self.dist.get((permutacao[-1], self.objetivo), math.inf)
        return custo

    @staticmethod
    def vizinhanca_swap(permutacao: List[Estado]) -> List[List[Estado]]:
        """
        Gera todos os vizinhos por troca de dois pontos de coleta.
        Para k coletas, gera k*(k-1)/2 vizinhos.
        """
        vizinhos = []
        n = len(permutacao)
        for i in range(n):
            for j in range(i + 1, n):
                viz = permutacao.copy()
                viz[i], viz[j] = viz[j], viz[i]
                vizinhos.append(viz)
        return vizinhos

    def caminho_completo(self, permutacao: List[Estado]) -> List[Estado]:
        """
        Concatena os caminhos A→Cπ(1)→…→Cπ(k)→B usando A*.
        Retorna a lista completa de células visitadas.
        """
        pontos = [self.inicio] + permutacao + [self.objetivo]
        caminho: List[Estado] = [pontos[0]]
        for i in range(len(pontos) - 1):
            trecho = self._a_estrela_caminho(pontos[i], pontos[i + 1])
            if not trecho:
                return []
            caminho.extend(trecho[1:])
        return caminho

    def visualizar(self, permutacao: List[Estado]) -> str:
        """
        Retorna visualização textual do labirinto com o caminho da solução.

        Legenda:
            '#'  parede
            '.'  caminho percorrido
            'A'  início
            'B'  objetivo
            'C'  ponto de coleta (na posição original)
            '*'  ponto de coleta já visitado no caminho
        """
        vis = [row.copy() for row in self.grade]
        caminho = self.caminho_completo(permutacao)

        for l, c in caminho:
            ch = vis[l][c]
            if ch not in {"A", "B", "C", "#"}:
                vis[l][c] = "."
            elif ch == "C":
                vis[l][c] = "*"

        vis[self.inicio[0]][self.inicio[1]] = "A"
        vis[self.objetivo[0]][self.objetivo[1]] = "B"

        return "\n".join("".join(row) for row in vis)

@dataclass
class ResultadoBuscaLocal:
    algoritmo: str
    melhor_custo: float
    melhor_permutacao: List[Estado]
    pior_custo: float
    custo_medio: float
    tempo_medio: float
    iteracoes_media: float
    curvas_convergencia: List[List[float]]   
    taxa_sucesso: float                      
    todos_custos: List[float]

def hill_climbing(
    lab: LabirintoColeta,
    max_iter: int = 10_000,
    seed: Optional[int] = None,
) -> Tuple[float, List[Estado], List[float], int]:
    """
    Hill-Climbing de subida mais íngreme para minimização.

    Vizinhança: todos os swaps.
    Para problema de minimização, aceita apenas movimentos que reduzam o custo.
    Para em mínimo local quando nenhum vizinho é melhor.

    Retorna: (melhor_custo, melhor_permutacao, curva_convergencia, iteracoes)
    """
    rng = random.Random(seed)

    coletas = lab.coletas.copy()
    perm_atual = coletas.copy()
    rng.shuffle(perm_atual)
    custo_atual = lab.custo_solucao(perm_atual)

    curva = [custo_atual]

    for it in range(1, max_iter + 1):
        vizinhos = lab.vizinhanca_swap(perm_atual)
        rng.shuffle(vizinhos) 

        melhor_viz = None
        melhor_custo_viz = custo_atual

        for viz in vizinhos:
            c = lab.custo_solucao(viz)
            if c < melhor_custo_viz:
                melhor_custo_viz = c
                melhor_viz = viz

        if melhor_viz is None:
            curva.append(custo_atual)
            return custo_atual, perm_atual, curva, it

        perm_atual = melhor_viz
        custo_atual = melhor_custo_viz
        curva.append(custo_atual)

    return custo_atual, perm_atual, curva, max_iter


def hill_climbing_multiplos_reinicios(
    lab: LabirintoColeta,
    num_reinicios: int = 20,
    max_iter_por_reinicio: int = 10_000,
    seed: Optional[int] = None,
) -> Tuple[float, List[Estado], List[float], int]:
    """
    Executa Hill-Climbing com múltiplos reinícios aleatórios.
    Retorna o melhor resultado encontrado entre todos os reinícios.
    """
    rng = random.Random(seed)

    melhor_global: float = math.inf
    melhor_perm_global: List[Estado] = []
    melhor_curva: List[float] = []
    total_iter = 0

    for i in range(num_reinicios):
        custo, perm, curva, iters = hill_climbing(
            lab,
            max_iter=max_iter_por_reinicio,
            seed=rng.randint(0, 2**31),
        )
        total_iter += iters
        if custo < melhor_global:
            melhor_global = custo
            melhor_perm_global = perm
            melhor_curva = curva

    return melhor_global, melhor_perm_global, melhor_curva, total_iter

def simulated_annealing(
    lab: LabirintoColeta,
    temperatura_inicial: float = 1000.0,
    taxa_resfriamento: float = 0.995,
    temperatura_minima: float = 0.1,
    max_iter: int = 50_000,
    seed: Optional[int] = None,
) -> Tuple[float, List[Estado], List[float], int]:
    """
    Simulated Annealing para minimização do custo de visitação.

    Parâmetros:
        temperatura_inicial : temperatura de início do resfriamento.
        taxa_resfriamento   : fator multiplicativo por iteração (0 < α < 1).
        temperatura_minima  : interrompe quando T < temperatura_minima.
        max_iter            : limite máximo de iterações.

    Retorna: (melhor_custo, melhor_permutacao, curva_convergencia, iteracoes)
    """
    rng = random.Random(seed)

    coletas = lab.coletas.copy()
    perm_atual = coletas.copy()
    rng.shuffle(perm_atual)
    custo_atual = lab.custo_solucao(perm_atual)

    melhor_custo = custo_atual
    melhor_perm = perm_atual.copy()

    T = temperatura_inicial
    curva: List[float] = [melhor_custo]
    it = 0

    while T > temperatura_minima and it < max_iter:
        n = len(perm_atual)
        if n < 2:
            break
        i, j = rng.sample(range(n), 2)
        viz = perm_atual.copy()
        viz[i], viz[j] = viz[j], viz[i]
        custo_viz = lab.custo_solucao(viz)

        delta = custo_viz - custo_atual
        if delta < 0 or rng.random() < math.exp(-delta / T):
            perm_atual = viz
            custo_atual = custo_viz

        if custo_atual < melhor_custo:
            melhor_custo = custo_atual
            melhor_perm = perm_atual.copy()

        T *= taxa_resfriamento
        it += 1
        curva.append(melhor_custo)

    return melhor_custo, melhor_perm, curva, it

def executar_experimentos(
    lab: LabirintoColeta,
    num_execucoes: int = 20,
    # Hill-Climbing
    hc_reinicios: int = 10,
    hc_max_iter: int = 10_000,
    # Simulated Annealing
    sa_temp_inicial: float = 1000.0,
    sa_taxa_resfriamento: float = 0.995,
    sa_temp_minima: float = 0.1,
    sa_max_iter: int = 50_000,
    calcular_otimo: bool = True,
    seed_base: int = 42,
) -> Dict[str, ResultadoBuscaLocal]:
    """
    Executa Hill-Climbing e Simulated Annealing por `num_execucoes` rodadas
    e coleta todas as métricas obrigatórias do enunciado.

    Limiar de "solução aceitável": custo ≤ 1.10 × melhor custo conhecido/ótimo.
    """
    resultados: Dict[str, ResultadoBuscaLocal] = {}
    custo_otimo = _custo_otimo(lab) if calcular_otimo and len(lab.coletas) <= 8 else None
    limiar_aceitavel_fator = 1.10

    for nome_alg, funcao_alg in [
        ("Hill-Climbing", _exec_hc),
        ("Simulated Annealing", _exec_sa),
    ]:
        custos: List[float] = []
        tempos: List[float] = []
        iteracoes: List[int] = []
        curvas: List[List[float]] = []
        melhores_perms: List[List[Estado]] = []

        for rodada in range(num_execucoes):
            seed = seed_base + rodada * 997 

            t0 = time.perf_counter()
            if nome_alg == "Hill-Climbing":
                custo, perm, curva, iters = _exec_hc(
                    lab, seed, hc_reinicios, hc_max_iter
                )
            else:
                custo, perm, curva, iters = _exec_sa(
                    lab, seed, sa_temp_inicial, sa_taxa_resfriamento,
                    sa_temp_minima, sa_max_iter
                )
            t1 = time.perf_counter()

            custos.append(custo)
            tempos.append(t1 - t0)
            iteracoes.append(iters)
            curvas.append(curva)
            melhores_perms.append(perm)

        melhor_custo = min(custos)
        melhor_perm = melhores_perms[custos.index(melhor_custo)]
        referencia = custo_otimo if custo_otimo is not None else melhor_custo
        limiar = referencia * limiar_aceitavel_fator
        taxa = sum(1 for c in custos if c <= limiar) / num_execucoes

        resultados[nome_alg] = ResultadoBuscaLocal(
            algoritmo=nome_alg,
            melhor_custo=melhor_custo,
            melhor_permutacao=melhor_perm,
            pior_custo=max(custos),
            custo_medio=sum(custos) / len(custos),
            tempo_medio=sum(tempos) / len(tempos),
            iteracoes_media=sum(iteracoes) / len(iteracoes),
            curvas_convergencia=curvas,
            taxa_sucesso=taxa,
            todos_custos=custos,
        )

    return resultados


def _exec_hc(
    lab: LabirintoColeta,
    seed: int,
    reinicios: int,
    max_iter: int,
) -> Tuple[float, List[Estado], List[float], int]:
    return hill_climbing_multiplos_reinicios(
        lab,
        num_reinicios=reinicios,
        max_iter_por_reinicio=max_iter,
        seed=seed,
    )


def _exec_sa(
    lab: LabirintoColeta,
    seed: int,
    temp_ini: float,
    taxa: float,
    temp_min: float,
    max_iter: int,
) -> Tuple[float, List[Estado], List[float], int]:
    return simulated_annealing(
        lab,
        temperatura_inicial=temp_ini,
        taxa_resfriamento=taxa,
        temperatura_minima=temp_min,
        max_iter=max_iter,
        seed=seed,
    )


def _custo_otimo(lab: LabirintoColeta) -> float:
    """
    Custo ótimo por força bruta (enumeração de todas as permutações).
    Viável apenas para k ≤ 8 pontos de coleta.
    """
    import itertools as it
    melhor = math.inf
    for perm in it.permutations(lab.coletas):
        c = lab.custo_solucao(list(perm))
        if c < melhor:
            melhor = c
    return melhor

def salvar_resultados_csv(
    resultados: Dict[str, ResultadoBuscaLocal],
    diretorio: str,
    nome_mapa: str = "",
) -> None:
    """Salva métricas agregadas em CSV."""
    saida = Path(diretorio)
    saida.mkdir(parents=True, exist_ok=True)
    arquivo = saida / "resultados_busca_local.csv"

    campos = [
        "mapa", "algoritmo",
        "melhor_custo", "pior_custo", "custo_medio",
        "tempo_medio_s", "iteracoes_media", "taxa_sucesso",
    ]
    with arquivo.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in resultados.values():
            writer.writerow({
                "mapa": nome_mapa,
                "algoritmo": r.algoritmo,
                "melhor_custo": f"{r.melhor_custo:.2f}",
                "pior_custo": f"{r.pior_custo:.2f}",
                "custo_medio": f"{r.custo_medio:.2f}",
                "tempo_medio_s": f"{r.tempo_medio:.6f}",
                "iteracoes_media": f"{r.iteracoes_media:.1f}",
                "taxa_sucesso": f"{r.taxa_sucesso:.2%}",
            })
    arquivo_raw = saida / "resultados_busca_local_raw.csv"
    with arquivo_raw.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["mapa", "algoritmo", "execucao", "custo"]
        )
        writer.writeheader()
        for r in resultados.values():
            for i, c in enumerate(r.todos_custos):
                writer.writerow({
                    "mapa": nome_mapa,
                    "algoritmo": r.algoritmo,
                    "execucao": i + 1,
                    "custo": f"{c:.2f}",
                })

    print(f"  CSV métricas  : {arquivo}")
    print(f"  CSV raw       : {arquivo_raw}")

def gerar_graficos(
    resultados: Dict[str, ResultadoBuscaLocal],
    diretorio: str,
    nome_mapa: str = "",
) -> None:
    """
    Gera os gráficos obrigatórios e os salva em PNG.

    1. Curva de convergência (iteração × melhor custo) por algoritmo.
    2. Boxplot de custos por algoritmo.
    3. Gráfico de barras: melhor, pior e médio custo.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # backend sem display
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [AVISO] matplotlib não instalado – gráficos ignorados.")
        print("          Execute: pip install matplotlib")
        return

    saida = Path(diretorio)
    saida.mkdir(parents=True, exist_ok=True)

    titulo_base = f"Busca Local – {Path(nome_mapa).stem}" if nome_mapa else "Busca Local"
    cores = {"Hill-Climbing": "#e05c2e", "Simulated Annealing": "#2e7be0"}
    fig, axes = plt.subplots(
        1, len(resultados), figsize=(7 * len(resultados), 5), sharey=True
    )
    if len(resultados) == 1:
        axes = [axes]

    for ax, (nome, r) in zip(axes, resultados.items()):
        cor = cores.get(nome, "steelblue")
        # Plota curva de cada execução em cinza claro
        for curva in r.curvas_convergencia:
            ax.plot(curva, color="lightgray", linewidth=0.7, alpha=0.6)
        # Destaca a curva da melhor execução
        melhor_idx = r.todos_custos.index(r.melhor_custo)
        ax.plot(
            r.curvas_convergencia[melhor_idx],
            color=cor, linewidth=2.0, label="Melhor execução",
        )
        ax.set_title(nome, fontsize=13, fontweight="bold")
        ax.set_xlabel("Iteração", fontsize=11)
        ax.set_ylabel("Melhor custo", fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.4)

    fig.suptitle(f"Curva de Convergência – {titulo_base}", fontsize=14)
    fig.tight_layout()
    arq1 = saida / "convergencia.png"
    fig.savefig(arq1, dpi=150)
    plt.close(fig)
    print(f"  Gráfico 1     : {arq1}")
    fig, ax = plt.subplots(figsize=(6, 5))
    nomes = list(resultados.keys())
    dados = [r.todos_custos for r in resultados.values()]
    bp = ax.boxplot(
        dados,
        tick_labels=nomes,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=2),
    )
    for patch, nome in zip(bp["boxes"], nomes):
        patch.set_facecolor(cores.get(nome, "steelblue"))
        patch.set_alpha(0.7)
    ax.set_title(f"Distribuição de Custos – {titulo_base}", fontsize=13)
    ax.set_ylabel("Custo da solução", fontsize=11)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    arq2 = saida / "boxplot_custos.png"
    fig.savefig(arq2, dpi=150)
    plt.close(fig)
    print(f"  Gráfico 2     : {arq2}")
    fig, ax = plt.subplots(figsize=(7, 5))
    x = list(range(len(nomes)))
    largura = 0.25

    melhores = [r.melhor_custo for r in resultados.values()]
    medios   = [r.custo_medio  for r in resultados.values()]
    piores   = [r.pior_custo   for r in resultados.values()]

    ax.bar([xi - largura for xi in x], melhores, width=largura,
           label="Melhor", color="#2ecc71", alpha=0.85)
    ax.bar(x,                          medios,   width=largura,
           label="Médio",  color="#3498db", alpha=0.85)
    ax.bar([xi + largura for xi in x], piores,   width=largura,
           label="Pior",   color="#e74c3c", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(nomes, fontsize=11)
    ax.set_ylabel("Custo", fontsize=11)
    ax.set_title(f"Comparativo de Custos – {titulo_base}", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    arq3 = saida / "comparativo_custos.png"
    fig.savefig(arq3, dpi=150)
    plt.close(fig)
    print(f"  Gráfico 3     : {arq3}")
    fig, ax = plt.subplots(figsize=(5, 4))
    taxas = [r.taxa_sucesso * 100 for r in resultados.values()]
    bars = ax.bar(nomes, taxas, color=[cores.get(n, "steelblue") for n in nomes], alpha=0.85)
    for bar, taxa in zip(bars, taxas):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{taxa:.1f}%",
            ha="center", va="bottom", fontsize=10,
        )
    ax.set_ylim(0, 115)
    ax.set_ylabel("Taxa de sucesso (%)", fontsize=11)
    ax.set_title(f"Taxa de Sucesso – {titulo_base}", fontsize=13)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    arq4 = saida / "taxa_sucesso.png"
    fig.savefig(arq4, dpi=150)
    plt.close(fig)
    print(f"  Gráfico 4     : {arq4}")

def imprimir_tabela(resultados: Dict[str, ResultadoBuscaLocal]) -> None:
    sep = "-" * 100
    print("\n" + sep)
    print("Resultados da Busca Local (Parte III)")
    print(sep)
    print(
        f"{'Algoritmo':<22} {'Melhor':>8} {'Pior':>8} {'Médio':>8} "
        f"{'Tempo(s)':>10} {'Iterações':>10} {'Sucesso':>8}"
    )
    print(sep)
    for r in resultados.values():
        print(
            f"{r.algoritmo:<22} "
            f"{r.melhor_custo:>8.1f} "
            f"{r.pior_custo:>8.1f} "
            f"{r.custo_medio:>8.1f} "
            f"{r.tempo_medio:>10.4f} "
            f"{r.iteracoes_media:>10.0f} "
            f"{r.taxa_sucesso:>7.1%}"
        )
    print(sep)

MAPA_DEMO = """\
###########
#A   #    #
# ## # ## #
#  C   B  #
# ## # ## #
#  C #    #
###########
"""

def criar_mapa_demo(caminho: str) -> None:
    """Cria um arquivo de labirinto de demonstração se não existir."""
    p = Path(caminho)
    if not p.exists():
        p.write_text(MAPA_DEMO, encoding="utf-8")
        print(f"  Mapa de demo criado: {p}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parte III – Busca Local com Pontos de Coleta\n"
            "Labirintos gerados em https://www.asciiart.eu/ascii-maze-generator\n"
            "Use o tema Classic e adicione 'C' nos pontos de coleta."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "mapa",
        nargs="?",
        default="mapa_coleta.txt",
        help="Caminho do arquivo .txt do labirinto (padrão: mapa_coleta.txt)",
    )
    parser.add_argument(
        "--execucoes", type=int, default=20,
        help="Número de execuções independentes por algoritmo (padrão: 20)",
    )
    parser.add_argument(
        "--saida", default="resultados_parte3",
        help="Diretório de saída para CSV, gráficos e visualizações (padrão: resultados_parte3)",
    )
    parser.add_argument(
        "--mostrar", action="store_true",
        help="Exibe no terminal o labirinto com o melhor caminho de cada algoritmo",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Cria e executa o mapa de demonstração embutido",
    )
    parser.add_argument("--sa-temp-ini",  type=float, default=1000.0)
    parser.add_argument("--sa-resfr",     type=float, default=0.995)
    parser.add_argument("--sa-temp-min",  type=float, default=0.1)
    parser.add_argument("--sa-max-iter",  type=int,   default=50_000)
    parser.add_argument(
        "--hc-reinicios", type=int, default=1,
        help="Número de reinícios do Hill-Climbing. Use 1 para o HC puro pedido no TP (padrão: 1).",
    )
    parser.add_argument(
        "--hc-max-iter", type=int, default=10_000,
        help="Máximo de iterações por execução/reinício do Hill-Climbing (padrão: 10000).",
    )

    args = parser.parse_args()

    if args.demo:
        criar_mapa_demo(args.mapa)
    print(f"\n{'='*55}")
    print(f"  Parte III – Busca Local com Pontos de Coleta")
    print(f"{'='*55}")
    print(f"  Mapa       : {args.mapa}")

    lab = LabirintoColeta(args.mapa)

    print(f"  Dimensões  : {lab.altura} × {lab.largura}")
    print(f"  Início     : {lab.inicio}")
    print(f"  Objetivo   : {lab.objetivo}")
    print(f"  Coletas    : {len(lab.coletas)} ponto(s) — {lab.coletas}")
    print(f"  Execuções  : {args.execucoes} por algoritmo")

    print("\n  Pré-computando distâncias via A*…", end=" ", flush=True)
    print("OK")

    print("  Executando experimentos…")
    resultados = executar_experimentos(
        lab,
        num_execucoes=args.execucoes,
        hc_reinicios=args.hc_reinicios,
        hc_max_iter=args.hc_max_iter,
        sa_temp_inicial=args.sa_temp_ini,
        sa_taxa_resfriamento=args.sa_resfr,
        sa_temp_minima=args.sa_temp_min,
        sa_max_iter=args.sa_max_iter,
        calcular_otimo=(len(lab.coletas) <= 8),
    )

    imprimir_tabela(resultados)

    if args.mostrar:
        for nome, r in resultados.items():
            print(f"\n{'-'*55}")
            print(f"  {nome} – melhor permutação: {r.melhor_permutacao}")
            print(f"  Custo: {r.melhor_custo:.1f}")
            print()
            print(lab.visualizar(r.melhor_permutacao))
        print()

    print(f"\n  Salvando resultados em '{args.saida}/'…")
    salvar_resultados_csv(resultados, args.saida, nome_mapa=args.mapa)
    gerar_graficos(resultados, args.saida, nome_mapa=args.mapa)

    print(f"\n{'='*55}")
    print("  Parte III concluída.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
