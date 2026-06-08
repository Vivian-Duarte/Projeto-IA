from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Set, Callable, Iterable
from collections import deque
import heapq
import itertools
import math
import time
import csv
import argparse
from pathlib import Path

Estado = Tuple[int, int]

ACOES = [
    ("cima", (-1, 0)),
    ("baixo", (1, 0)),
    ("esquerda", (0, -1)),
    ("direita", (0, 1)),
]


@dataclass
class No:
    estado: Estado
    pai: Optional["No"] = None
    acao: Optional[str] = None
    g: float = 0.0  


@dataclass
class ResultadoBusca:
    algoritmo: str
    encontrado: bool
    caminho: List[Estado]
    acoes: List[str]
    custo_caminho: Optional[float]
    nos_explorados: int
    nos_expandidos: int
    tempo_execucao: float
    tamanho_max_fronteira: int
    estados_explorados: List[Estado]
    estados_expandidos: List[Estado]

    @property
    def passos(self) -> Optional[int]:
        """Quantidade de movimentos no caminho encontrado."""
        return len(self.acoes) if self.encontrado else None

    def linha_csv(self, mapa: str = "") -> Dict[str, object]:
        return {
            "mapa": mapa,
            "algoritmo": self.algoritmo,
            "sucesso": self.encontrado,
            "custo": self.custo_caminho if self.custo_caminho is not None else "",
            "passos": self.passos if self.passos is not None else "",
            "nos_explorados": self.nos_explorados,
            "nos_expandidos": self.nos_expandidos,
            "tempo_execucao_s": f"{self.tempo_execucao:.8f}",
            "fronteira_maxima": self.tamanho_max_fronteira,
        }


class LabirintoBusca:
    """
    Implementacao da Parte II do TP: Busca Classica no Labirinto Conhecido.

    Atende aos requisitos:
    - leitura de mapa em .txt;
    - busca de A ate B;
    - BFS, DFS, UCS, Gulosa e A*;
    - heuristica Manhattan para buscas informadas;
    - metricas: sucesso, custo, passos, explorados, expandidos, tempo e fronteira maxima;
    - visualizacao textual do caminho e dos estados expandidos.

    Padrao esperado do mapa:
    - '#': parede;
    - ' ': celula livre;
    - 'A': inicio;
    - 'B': objetivo.

    Compatibilidade com ASCII Maze Generator:
    - se o mapa vier com 'S' e 'E', eles sao normalizados para 'A' e 'B'.
    - recomenda-se usar o tema Classic: '#' para paredes e espacos para caminhos.
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.grade: List[List[str]] = []
        self.paredes: List[List[bool]] = []
        self.inicio: Estado
        self.objetivo: Estado
        self._ler_mapa(filename)

    def _ler_mapa(self, filename: str) -> None:
        with open(filename, encoding="utf-8") as f:
            conteudo = f.read()

        linhas = conteudo.splitlines()
        while linhas and linhas[-1] == "":
            linhas.pop()

        if not linhas:
            raise ValueError("O arquivo do labirinto esta vazio.")

        # Compatibilidade com geradores que usam S/E para Start/End.
        total_A = sum(linha.count("A") for linha in linhas)
        total_B = sum(linha.count("B") for linha in linhas)
        total_S = sum(linha.count("S") for linha in linhas)
        total_E = sum(linha.count("E") for linha in linhas)

        linhas_normalizadas = []
        for linha in linhas:
            if total_A == 0 and total_S == 1:
                linha = linha.replace("S", "A")
            if total_B == 0 and total_E == 1:
                linha = linha.replace("E", "B")
            linhas_normalizadas.append(linha)
        linhas = linhas_normalizadas

        total_A = sum(linha.count("A") for linha in linhas)
        total_B = sum(linha.count("B") for linha in linhas)

        if total_A != 1:
            raise ValueError("O labirinto deve ter exatamente um ponto inicial A. Se usar o gerador, troque S por A.")
        if total_B != 1:
            raise ValueError("O labirinto deve ter exatamente um objetivo B. Se usar o gerador, troque E por B.")

        self.altura = len(linhas)
        self.largura = max(len(linha) for linha in linhas)

        for i, linha_original in enumerate(linhas):
            linha = linha_original.ljust(self.largura, "#")
            linha_grade: List[str] = []
            linha_paredes: List[bool] = []

            for j, char in enumerate(linha):
                if char == "A":
                    self.inicio = (i, j)
                    linha_grade.append("A")
                    linha_paredes.append(False)
                elif char == "B":
                    self.objetivo = (i, j)
                    linha_grade.append("B")
                    linha_paredes.append(False)
                elif char == "#":
                    linha_grade.append("#")
                    linha_paredes.append(True)
                else:
                    linha_grade.append(char)
                    linha_paredes.append(False)

            self.grade.append(linha_grade)
            self.paredes.append(linha_paredes)

    def dentro_dos_limites(self, estado: Estado) -> bool:
        linha, coluna = estado
        return 0 <= linha < self.altura and 0 <= coluna < self.largura

    def transitavel(self, estado: Estado) -> bool:
        linha, coluna = estado
        return self.dentro_dos_limites(estado) and not self.paredes[linha][coluna]

    def vizinhos(self, estado: Estado) -> List[Tuple[str, Estado, float]]:
        """Retorna as transicoes validas: (acao, novo_estado, custo)."""
        linha, coluna = estado
        resultado = []
        for acao, (dl, dc) in ACOES:
            proximo = (linha + dl, coluna + dc)
            if self.transitavel(proximo):
                resultado.append((acao, proximo, 1.0))
        return resultado

    def h(self, estado: Estado) -> float:
        """Heuristica de Manhattan para movimentos ortogonais com custo unitario."""
        return abs(estado[0] - self.objetivo[0]) + abs(estado[1] - self.objetivo[1])

    @staticmethod
    def reconstruir(no: No) -> Tuple[List[Estado], List[str]]:
        """Reconstrói caminho e acoes de A ate B."""
        estados: List[Estado] = []
        acoes: List[str] = []
        atual: Optional[No] = no

        while atual is not None:
            estados.append(atual.estado)
            if atual.acao is not None:
                acoes.append(atual.acao)
            atual = atual.pai

        estados.reverse()
        acoes.reverse()
        return estados, acoes

    def _resultado_falha(
        self,
        algoritmo: str,
        inicio_tempo: float,
        nos_explorados: int,
        nos_expandidos: int,
        tamanho_max_fronteira: int,
        estados_explorados: List[Estado],
        estados_expandidos: List[Estado],
    ) -> ResultadoBusca:
        return ResultadoBusca(
            algoritmo=algoritmo,
            encontrado=False,
            caminho=[],
            acoes=[],
            custo_caminho=None,
            nos_explorados=nos_explorados,
            nos_expandidos=nos_expandidos,
            tempo_execucao=time.perf_counter() - inicio_tempo,
            tamanho_max_fronteira=tamanho_max_fronteira,
            estados_explorados=estados_explorados,
            estados_expandidos=estados_expandidos,
        )

    def busca_largura(self) -> ResultadoBusca:
        """BFS: expande por nivel e usa fila FIFO."""
        algoritmo = "BFS"
        inicio_tempo = time.perf_counter()
        inicio = No(self.inicio, g=0.0)

        fronteira = deque([inicio])
        em_fronteira: Set[Estado] = {self.inicio}
        explorados: Set[Estado] = set()

        estados_explorados: List[Estado] = []
        estados_expandidos: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0
        tamanho_max_fronteira = 1

        while fronteira:
            no = fronteira.popleft()
            em_fronteira.remove(no.estado)

            nos_explorados += 1
            estados_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca(
                    algoritmo, True, caminho, acoes, no.g,
                    nos_explorados, nos_expandidos,
                    time.perf_counter() - inicio_tempo,
                    tamanho_max_fronteira,
                    estados_explorados, estados_expandidos,
                )

            explorados.add(no.estado)
            nos_expandidos += 1
            estados_expandidos.append(no.estado)

            for acao, estado, custo in self.vizinhos(no.estado):
                if estado not in explorados and estado not in em_fronteira:
                    filho = No(estado=estado, pai=no, acao=acao, g=no.g + custo)
                    fronteira.append(filho)
                    em_fronteira.add(estado)

            tamanho_max_fronteira = max(tamanho_max_fronteira, len(fronteira))

        return self._resultado_falha(
            algoritmo, inicio_tempo, nos_explorados, nos_expandidos,
            tamanho_max_fronteira, estados_explorados, estados_expandidos,
        )

    def busca_profundidade(self) -> ResultadoBusca:
        """DFS: expande o no mais profundo primeiro e usa pilha LIFO."""
        algoritmo = "DFS"
        inicio_tempo = time.perf_counter()
        inicio = No(self.inicio, g=0.0)

        fronteira = [inicio]
        em_fronteira: Set[Estado] = {self.inicio}
        explorados: Set[Estado] = set()

        estados_explorados: List[Estado] = []
        estados_expandidos: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0
        tamanho_max_fronteira = 1

        while fronteira:
            no = fronteira.pop()
            em_fronteira.remove(no.estado)

            nos_explorados += 1
            estados_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca(
                    algoritmo, True, caminho, acoes, no.g,
                    nos_explorados, nos_expandidos,
                    time.perf_counter() - inicio_tempo,
                    tamanho_max_fronteira,
                    estados_explorados, estados_expandidos,
                )

            explorados.add(no.estado)
            nos_expandidos += 1
            estados_expandidos.append(no.estado)
            for acao, estado, custo in reversed(self.vizinhos(no.estado)):
                if estado not in explorados and estado not in em_fronteira:
                    filho = No(estado=estado, pai=no, acao=acao, g=no.g + custo)
                    fronteira.append(filho)
                    em_fronteira.add(estado)

            tamanho_max_fronteira = max(tamanho_max_fronteira, len(fronteira))

        return self._resultado_falha(
            algoritmo, inicio_tempo, nos_explorados, nos_expandidos,
            tamanho_max_fronteira, estados_explorados, estados_expandidos,
        )

    def busca_prioridade(self, algoritmo: str, prioridade: Callable[[No], float]) -> ResultadoBusca:
        """
        Estrutura comum para UCS, Gulosa e A*.

        UCS:     f(n) = g(n)
        Gulosa:  f(n) = h(n)
        A*:      f(n) = g(n) + h(n)
        """
        inicio_tempo = time.perf_counter()
        contador = itertools.count()
        inicio = No(self.inicio, g=0.0)

        fronteira: List[Tuple[float, int, No]] = []
        heapq.heappush(fronteira, (prioridade(inicio), next(contador), inicio))

        melhor_g: Dict[Estado, float] = {self.inicio: 0.0}
        fechados: Set[Estado] = set()

        estados_explorados: List[Estado] = []
        estados_expandidos: List[Estado] = []
        nos_explorados = 0
        nos_expandidos = 0
        tamanho_max_fronteira = 1

        while fronteira:
            _, _, no = heapq.heappop(fronteira)

            if no.estado in fechados:
                continue

            nos_explorados += 1
            estados_explorados.append(no.estado)

            if no.estado == self.objetivo:
                caminho, acoes = self.reconstruir(no)
                return ResultadoBusca(
                    algoritmo, True, caminho, acoes, no.g,
                    nos_explorados, nos_expandidos,
                    time.perf_counter() - inicio_tempo,
                    tamanho_max_fronteira,
                    estados_explorados, estados_expandidos,
                )

            fechados.add(no.estado)
            nos_expandidos += 1
            estados_expandidos.append(no.estado)

            for acao, estado, custo in self.vizinhos(no.estado):
                if estado in fechados:
                    continue

                novo_g = no.g + custo

                if novo_g < melhor_g.get(estado, math.inf):
                    filho = No(estado=estado, pai=no, acao=acao, g=novo_g)
                    melhor_g[estado] = novo_g
                    heapq.heappush(fronteira, (prioridade(filho), next(contador), filho))

            tamanho_max_fronteira = max(tamanho_max_fronteira, len(fronteira))

        return self._resultado_falha(
            algoritmo, inicio_tempo, nos_explorados, nos_expandidos,
            tamanho_max_fronteira, estados_explorados, estados_expandidos,
        )

    def busca_custo_uniforme(self) -> ResultadoBusca:
        """UCS: expande o no de menor custo acumulado g(n)."""
        return self.busca_prioridade("UCS", lambda no: no.g)

    def busca_gulosa(self) -> ResultadoBusca:
        """Greedy Best-First: expande o no com menor h(n)."""
        return self.busca_prioridade("Gulosa", lambda no: self.h(no.estado))

    def busca_a_estrela(self) -> ResultadoBusca:
        """A*: expande o no com menor f(n) = g(n) + h(n)."""
        return self.busca_prioridade("A*", lambda no: no.g + self.h(no.estado))

    def executar_todos(self) -> List[ResultadoBusca]:
        return [
            self.busca_largura(),
            self.busca_profundidade(),
            self.busca_custo_uniforme(),
            self.busca_gulosa(),
            self.busca_a_estrela(),
        ]

    def visualizar(
        self,
        resultado: ResultadoBusca,
        mostrar_expandidos: bool = True,
    ) -> str:
        """
        Gera visualizacao em texto:
        - '#': parede;
        - 'x': estado expandido/visitado;
        - '.': caminho final;
        - 'A': inicio;
        - 'B': objetivo.
        """
        vis = [linha.copy() for linha in self.grade]

        if mostrar_expandidos:
            for l, c in resultado.estados_expandidos:
                if (l, c) not in {self.inicio, self.objetivo} and vis[l][c] != "#":
                    vis[l][c] = "x"

        for l, c in resultado.caminho:
            if (l, c) not in {self.inicio, self.objetivo} and vis[l][c] != "#":
                vis[l][c] = "."

        il, ic = self.inicio
        ol, oc = self.objetivo
        vis[il][ic] = "A"
        vis[ol][oc] = "B"

        return "\n".join("".join(linha) for linha in vis)


def salvar_resultados_csv(resultados: Iterable[ResultadoBusca], arquivo_csv: str, nome_mapa: str = "") -> None:
    caminho = Path(arquivo_csv)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    campos = [
        "mapa",
        "algoritmo",
        "sucesso",
        "custo",
        "passos",
        "nos_explorados",
        "nos_expandidos",
        "tempo_execucao_s",
        "fronteira_maxima",
    ]

    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in resultados:
            writer.writerow(r.linha_csv(nome_mapa))


def salvar_visualizacoes(lab: LabirintoBusca, resultados: Iterable[ResultadoBusca], diretorio: str) -> None:
    saida = Path(diretorio)
    saida.mkdir(parents=True, exist_ok=True)

    for r in resultados:
        nome = r.algoritmo.lower().replace("*", "estrela").replace(" ", "_")
        arquivo = saida / f"{nome}.txt"
        arquivo.write_text(lab.visualizar(r), encoding="utf-8")


def imprimir_tabela(resultados: List[ResultadoBusca]) -> None:
    print("\nResultados da Busca Classica")
    print("-" * 105)
    print(f"{'Algoritmo':<10} {'Sucesso':<8} {'Custo':<8} {'Passos':<8} {'Explorados':<12} {'Expandidos':<12} {'Tempo(s)':<12} {'Fronteira':<10}")
    print("-" * 105)

    for r in resultados:
        custo = "-" if r.custo_caminho is None else f"{r.custo_caminho:.0f}"
        passos = "-" if r.passos is None else str(r.passos)
        print(
            f"{r.algoritmo:<10} "
            f"{str(r.encontrado):<8} "
            f"{custo:<8} "
            f"{passos:<8} "
            f"{r.nos_explorados:<12} "
            f"{r.nos_expandidos:<12} "
            f"{r.tempo_execucao:<12.8f} "
            f"{r.tamanho_max_fronteira:<10}"
        )
    print("-" * 105)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parte II - Busca Classica em Labirinto Conhecido")
    parser.add_argument("mapa", help="Caminho do arquivo .txt do labirinto")
    parser.add_argument("--saida-csv", default="resultados/resultados_busca_classica.csv", help="Arquivo CSV de saida")
    parser.add_argument("--saida-vis", default="resultados/visualizacoes_busca_classica", help="Diretorio para salvar visualizacoes")
    parser.add_argument("--mostrar", action="store_true", help="Mostra no terminal a visualizacao de cada algoritmo")
    args = parser.parse_args()

    lab = LabirintoBusca(args.mapa)
    resultados = lab.executar_todos()

    imprimir_tabela(resultados)
    salvar_resultados_csv(resultados, args.saida_csv, nome_mapa=args.mapa)
    salvar_visualizacoes(lab, resultados, args.saida_vis)

    print(f"\nCSV salvo em: {args.saida_csv}")
    print(f"Visualizacoes salvas em: {args.saida_vis}")

    if args.mostrar:
        for r in resultados:
            print(f"\n{r.algoritmo}")
            print(lab.visualizar(r))


if __name__ == "__main__":
    main()
