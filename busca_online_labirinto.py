"""
Parte IV – Busca Online no Labirinto Desconhecido
-------------------------------------------------
Implementa a estratégia Opção A: Replanning com A*.

Ideia central:
- O simulador possui o mapa real completo.
- O agente NÃO acessa diretamente o mapa real.
- O agente mantém um mapa interno inicialmente desconhecido, preenchido com '?'.
- A cada passo, executa o ciclo:

    perceber -> atualizar mapa interno -> planejar -> agir

Compatibilidade com mapas ASCII:
- 'A' = posição inicial
- 'B' = objetivo final
- '#' = parede
- ' ' = célula livre
- 'C' = tratado como célula livre nesta Parte IV, caso exista no mapa

Exemplo de uso:
    py busca_online_labirinto.py mapas/labirinto_01.txt --saida resultados/online_labirinto_01 --mostrar --frames

Arquivos gerados:
- metricas_online.csv
- trajetoria_online.csv
- mapa_real_com_trajeto.txt
- mapa_interno_final.txt
- frames/frame_0000.txt ... se usar --frames
"""

from __future__ import annotations

import argparse
import csv
import heapq
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

Estado = Tuple[int, int]

ACOES: List[Tuple[str, Tuple[int, int]]] = [
    ("cima", (-1, 0)),
    ("baixo", (1, 0)),
    ("esquerda", (0, -1)),
    ("direita", (0, 1)),
]


@dataclass
class ResultadoAStar:
    caminho: List[Estado]
    custo: float
    expandidos: int


@dataclass
class ResultadoOnline:
    mapa: str
    sucesso: bool
    custo_online: float
    movimentos: int
    custo_offline: float
    razao_online_offline: float
    celulas_reveladas: int
    celulas_revisitadas: int
    replanejamentos: int
    nos_expandidos_planejamento: int
    tempo_s: float
    trajetoria: List[Estado]
    mapa_interno_final: List[List[str]]
    caminho_otimo_offline: List[Estado]


class LabirintoOnline:
    def __init__(self, filename: str, raio_percepcao: int = 1):
        self.filename = filename
        self.raio_percepcao = raio_percepcao
        self.real: List[List[str]] = []
        self.altura = 0
        self.largura = 0
        self.inicio: Estado = (-1, -1)
        self.objetivo: Estado = (-1, -1)
        self._ler_mapa(filename)

    def _ler_mapa(self, filename: str) -> None:
        with open(filename, encoding="utf-8") as f:
            linhas = f.read().splitlines()

        if not linhas:
            raise ValueError("O arquivo do labirinto está vazio.")

        qtd_a = sum(linha.count("A") for linha in linhas)
        qtd_b = sum(linha.count("B") for linha in linhas)

        if qtd_a != 1:
            raise ValueError("O mapa deve ter exatamente um ponto inicial 'A'.")
        if qtd_b != 1:
            raise ValueError("O mapa deve ter exatamente um objetivo 'B'.")

        self.altura = len(linhas)
        self.largura = max(len(linha) for linha in linhas)
        self.real = []

        for i, linha in enumerate(linhas):
            # Preenche linhas menores com parede para evitar caminhos artificiais.
            linha_pad = linha.ljust(self.largura, "#")
            row = []
            for j, ch in enumerate(linha_pad):
                if ch == "A":
                    self.inicio = (i, j)
                    row.append("A")
                elif ch == "B":
                    self.objetivo = (i, j)
                    row.append("B")
                elif ch == "#":
                    row.append("#")
                else:
                    # Espaço, C ou qualquer outro símbolo não parede é tratado como livre.
                    row.append(ch if ch in {" ", "C"} else " ")
            self.real.append(row)

    def dentro(self, estado: Estado) -> bool:
        l, c = estado
        return 0 <= l < self.altura and 0 <= c < self.largura

    def eh_livre_real(self, estado: Estado) -> bool:
        if not self.dentro(estado):
            return False
        l, c = estado
        return self.real[l][c] != "#"

    @staticmethod
    def eh_livre_interno_char(ch: str) -> bool:
        return ch in {" ", "A", "B", "C"}

    def vizinhos_reais(self, estado: Estado) -> List[Estado]:
        l, c = estado
        viz = []
        for _, (dl, dc) in ACOES:
            n = (l + dl, c + dc)
            if self.eh_livre_real(n):
                viz.append(n)
        return viz

    def vizinhos_internos(self, estado: Estado, interno: List[List[str]]) -> List[Estado]:
        l, c = estado
        viz = []
        for _, (dl, dc) in ACOES:
            n = (l + dl, c + dc)
            if not self.dentro(n):
                continue
            nl, nc = n
            if self.eh_livre_interno_char(interno[nl][nc]):
                viz.append(n)
        return viz

    @staticmethod
    def manhattan(a: Estado, b: Estado) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def astar_real(self, origem: Estado, destino: Estado) -> ResultadoAStar:
        return self._astar(
            origem=origem,
            objetivos={destino},
            vizinhos_fn=self.vizinhos_reais,
            heuristica_fn=lambda e: self.manhattan(e, destino),
        )

    def astar_interno(
        self,
        origem: Estado,
        objetivos: Set[Estado],
        interno: List[List[str]],
    ) -> ResultadoAStar:
        if not objetivos:
            return ResultadoAStar([], math.inf, 0)

        def h(e: Estado) -> int:
            return min(self.manhattan(e, obj) for obj in objetivos)

        return self._astar(
            origem=origem,
            objetivos=objetivos,
            vizinhos_fn=lambda e: self.vizinhos_internos(e, interno),
            heuristica_fn=h,
        )

    def _astar(
        self,
        origem: Estado,
        objetivos: Set[Estado],
        vizinhos_fn,
        heuristica_fn,
    ) -> ResultadoAStar:
        contador = 0
        fronteira: List[Tuple[float, int, Estado]] = []
        heapq.heappush(fronteira, (heuristica_fn(origem), contador, origem))

        veio_de: Dict[Estado, Optional[Estado]] = {origem: None}
        g: Dict[Estado, float] = {origem: 0.0}
        fechados: Set[Estado] = set()
        expandidos = 0

        while fronteira:
            _, _, atual = heapq.heappop(fronteira)
            if atual in fechados:
                continue
            fechados.add(atual)

            if atual in objetivos:
                caminho = self._reconstruir_caminho(veio_de, atual)
                return ResultadoAStar(caminho, g[atual], expandidos)

            expandidos += 1

            for viz in vizinhos_fn(atual):
                novo_g = g[atual] + 1
                if novo_g < g.get(viz, math.inf):
                    veio_de[viz] = atual
                    g[viz] = novo_g
                    contador += 1
                    f = novo_g + heuristica_fn(viz)
                    heapq.heappush(fronteira, (f, contador, viz))

        return ResultadoAStar([], math.inf, expandidos)

    @staticmethod
    def _reconstruir_caminho(veio_de: Dict[Estado, Optional[Estado]], fim: Estado) -> List[Estado]:
        caminho = [fim]
        atual = fim
        while veio_de[atual] is not None:
            atual = veio_de[atual]
            caminho.append(atual)
        caminho.reverse()
        return caminho

    def criar_mapa_interno(self) -> List[List[str]]:
        return [["?" for _ in range(self.largura)] for _ in range(self.altura)]

    def perceber(self, pos: Estado, interno: List[List[str]], reveladas: Set[Estado]) -> None:
        """
        Percepção local com raio 1 ortogonal: posição atual + quatro vizinhos.
        Para raio_percepcao > 1, revela células por distância Manhattan <= raio.
        """
        l0, c0 = pos
        for dl in range(-self.raio_percepcao, self.raio_percepcao + 1):
            for dc in range(-self.raio_percepcao, self.raio_percepcao + 1):
                if abs(dl) + abs(dc) > self.raio_percepcao:
                    continue
                p = (l0 + dl, c0 + dc)
                if not self.dentro(p):
                    continue
                l, c = p
                interno[l][c] = self.real[l][c]
                reveladas.add(p)

    def objetivo_revelado(self, interno: List[List[str]]) -> Optional[Estado]:
        l, c = self.objetivo
        if interno[l][c] == "B":
            return self.objetivo
        return None

    def celulas_fronteira(self, interno: List[List[str]]) -> Set[Estado]:
        """
        Fronteira explorável: célula livre conhecida que tem pelo menos um vizinho desconhecido.
        O agente planeja até uma fronteira para revelar novas áreas.
        """
        fronteiras: Set[Estado] = set()
        for l in range(self.altura):
            for c in range(self.largura):
                if not self.eh_livre_interno_char(interno[l][c]):
                    continue
                estado = (l, c)
                for _, (dl, dc) in ACOES:
                    n = (l + dl, c + dc)
                    if self.dentro(n):
                        nl, nc = n
                        if interno[nl][nc] == "?":
                            fronteiras.add(estado)
                            break
        return fronteiras

    def executar_replanning_astar(self, max_passos: Optional[int] = None, salvar_frames: bool = False, pasta_frames: Optional[Path] = None) -> ResultadoOnline:
        if max_passos is None:
            max_passos = self.altura * self.largura * 4

        inicio_tempo = time.perf_counter()

        interno = self.criar_mapa_interno()
        atual = self.inicio
        trajetoria: List[Estado] = [atual]
        visitas: Dict[Estado, int] = {atual: 1}
        reveladas: Set[Estado] = set()

        movimentos = 0
        revisitadas = 0
        replanejamentos = 0
        expandidos_planejamento = 0
        sucesso = False

        # Custo ótimo offline com mapa completo, para comparação online/offline.
        offline = self.astar_real(self.inicio, self.objetivo)
        custo_offline = offline.custo

        if salvar_frames:
            if pasta_frames is None:
                raise ValueError("pasta_frames deve ser informada quando salvar_frames=True")
            pasta_frames.mkdir(parents=True, exist_ok=True)

        passo = 0
        while movimentos < max_passos:
            # perceber -> atualizar mapa interno
            self.perceber(atual, interno, reveladas)

            if salvar_frames:
                self.salvar_frame(pasta_frames / f"frame_{passo:04d}.txt", interno, atual, trajetoria)

            if atual == self.objetivo:
                sucesso = True
                break

            # planejar
            objetivo_conhecido = self.objetivo_revelado(interno)
            replanejamentos += 1

            if objetivo_conhecido is not None:
                plano = self.astar_interno(atual, {objetivo_conhecido}, interno)
                expandidos_planejamento += plano.expandidos

                # Se o objetivo foi revelado, mas ainda não há caminho conhecido, continue explorando fronteiras.
                if not plano.caminho or math.isinf(plano.custo):
                    plano = self._planejar_para_fronteira(atual, interno)
                    expandidos_planejamento += plano.expandidos
            else:
                plano = self._planejar_para_fronteira(atual, interno)
                expandidos_planejamento += plano.expandidos

            if not plano.caminho or len(plano.caminho) < 2:
                # Sem plano para objetivo ou fronteira: falha.
                break

            proximo = plano.caminho[1]

            # agir: executa apenas o próximo passo e depois replaneja.
            if not self.eh_livre_real(proximo):
                # Não deveria ocorrer, pois o próximo passo é sempre em célula conhecida como livre.
                break

            if visitas.get(proximo, 0) > 0:
                revisitadas += 1

            atual = proximo
            visitas[atual] = visitas.get(atual, 0) + 1
            trajetoria.append(atual)
            movimentos += 1
            passo += 1

        # percepção final, para registrar o mapa interno após a parada.
        self.perceber(atual, interno, reveladas)
        if atual == self.objetivo:
            sucesso = True

        tempo_s = time.perf_counter() - inicio_tempo
        custo_online = float(movimentos) if sucesso else math.inf
        razao = custo_online / custo_offline if sucesso and custo_offline > 0 and not math.isinf(custo_offline) else math.inf

        return ResultadoOnline(
            mapa=self.filename,
            sucesso=sucesso,
            custo_online=custo_online,
            movimentos=movimentos,
            custo_offline=custo_offline,
            razao_online_offline=razao,
            celulas_reveladas=len(reveladas),
            celulas_revisitadas=revisitadas,
            replanejamentos=replanejamentos,
            nos_expandidos_planejamento=expandidos_planejamento,
            tempo_s=tempo_s,
            trajetoria=trajetoria,
            mapa_interno_final=interno,
            caminho_otimo_offline=offline.caminho,
        )

    def _planejar_para_fronteira(self, atual: Estado, interno: List[List[str]]) -> ResultadoAStar:
        fronteiras = self.celulas_fronteira(interno)
        # Não faz sentido planejar para a posição atual; queremos avançar para revelar novas regiões.
        if atual in fronteiras and len(fronteiras) > 1:
            fronteiras.remove(atual)
        return self.astar_interno(atual, fronteiras, interno)

    def renderizar_mapa_real_com_trajeto(self, trajetoria: Sequence[Estado]) -> str:
        grid = [row[:] for row in self.real]
        for p in trajetoria:
            l, c = p
            if grid[l][c] not in {"A", "B", "#"}:
                grid[l][c] = "."
        # Mantém A e B destacados.
        il, ic = self.inicio
        bl, bc = self.objetivo
        grid[il][ic] = "A"
        grid[bl][bc] = "B"
        return "\n".join("".join(row) for row in grid)

    def renderizar_mapa_interno(self, interno: List[List[str]], pos_agente: Optional[Estado] = None) -> str:
        grid = [row[:] for row in interno]
        if pos_agente is not None:
            l, c = pos_agente
            if grid[l][c] not in {"A", "B"}:
                grid[l][c] = "R"
        return "\n".join("".join(row) for row in grid)

    def renderizar_mapa_interno_com_trajeto(self, interno: List[List[str]], trajetoria: Sequence[Estado], pos_agente: Optional[Estado] = None) -> str:
        grid = [row[:] for row in interno]
        for p in trajetoria:
            l, c = p
            if grid[l][c] not in {"A", "B", "#", "?"}:
                grid[l][c] = "."
        if pos_agente is not None:
            l, c = pos_agente
            if grid[l][c] not in {"A", "B"}:
                grid[l][c] = "R"
        il, ic = self.inicio
        grid[il][ic] = "A"
        if interno[self.objetivo[0]][self.objetivo[1]] == "B":
            bl, bc = self.objetivo
            grid[bl][bc] = "B"
        return "\n".join("".join(row) for row in grid)

    def salvar_frame(self, path: Path, interno: List[List[str]], atual: Estado, trajetoria: Sequence[Estado]) -> None:
        path.write_text(self.renderizar_mapa_interno_com_trajeto(interno, trajetoria, atual), encoding="utf-8")


def salvar_resultados(resultado: ResultadoOnline, lab: LabirintoOnline, saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)

    # CSV de métricas principais.
    csv_metricas = saida / "metricas_online.csv"
    with open(csv_metricas, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "mapa",
                "sucesso",
                "custo_online",
                "movimentos",
                "custo_offline",
                "razao_online_offline",
                "celulas_reveladas",
                "celulas_revisitadas",
                "replanejamentos",
                "nos_expandidos_planejamento",
                "tempo_s",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "mapa": resultado.mapa,
                "sucesso": resultado.sucesso,
                "custo_online": f"{resultado.custo_online:.2f}" if not math.isinf(resultado.custo_online) else "inf",
                "movimentos": resultado.movimentos,
                "custo_offline": f"{resultado.custo_offline:.2f}" if not math.isinf(resultado.custo_offline) else "inf",
                "razao_online_offline": f"{resultado.razao_online_offline:.4f}" if not math.isinf(resultado.razao_online_offline) else "inf",
                "celulas_reveladas": resultado.celulas_reveladas,
                "celulas_revisitadas": resultado.celulas_revisitadas,
                "replanejamentos": resultado.replanejamentos,
                "nos_expandidos_planejamento": resultado.nos_expandidos_planejamento,
                "tempo_s": f"{resultado.tempo_s:.6f}",
            }
        )

    # CSV passo a passo da trajetória.
    csv_traj = saida / "trajetoria_online.csv"
    with open(csv_traj, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["passo", "linha", "coluna"])
        writer.writeheader()
        for i, (l, c) in enumerate(resultado.trajetoria):
            writer.writerow({"passo": i, "linha": l, "coluna": c})

    # Visualizações textuais.
    (saida / "mapa_real_com_trajeto.txt").write_text(
        lab.renderizar_mapa_real_com_trajeto(resultado.trajetoria), encoding="utf-8"
    )
    (saida / "mapa_interno_final.txt").write_text(
        lab.renderizar_mapa_interno(resultado.mapa_interno_final), encoding="utf-8"
    )
    (saida / "mapa_interno_final_com_trajeto.txt").write_text(
        lab.renderizar_mapa_interno_com_trajeto(
            resultado.mapa_interno_final,
            resultado.trajetoria,
            resultado.trajetoria[-1] if resultado.trajetoria else None,
        ),
        encoding="utf-8",
    )

    # Caminho ótimo offline, para comparação.
    (saida / "caminho_otimo_offline.txt").write_text(
        lab.renderizar_mapa_real_com_trajeto(resultado.caminho_otimo_offline), encoding="utf-8"
    )


def imprimir_resumo(resultado: ResultadoOnline) -> None:
    print("\n=======================================================")
    print("  Parte IV – Busca Online no Labirinto Desconhecido")
    print("=======================================================")
    print(f"  Mapa                         : {resultado.mapa}")
    print(f"  Sucesso                      : {resultado.sucesso}")
    print(f"  Movimentos / custo online    : {resultado.movimentos}")
    print(f"  Custo ótimo offline          : {resultado.custo_offline}")
    print(f"  Razão online/offline         : {resultado.razao_online_offline:.4f}" if not math.isinf(resultado.razao_online_offline) else "  Razão online/offline         : inf")
    print(f"  Células reveladas            : {resultado.celulas_reveladas}")
    print(f"  Células revisitadas          : {resultado.celulas_revisitadas}")
    print(f"  Replanejamentos              : {resultado.replanejamentos}")
    print(f"  Nós expandidos no planejamento: {resultado.nos_expandidos_planejamento}")
    print(f"  Tempo(s)                     : {resultado.tempo_s:.6f}")
    print("=======================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parte IV – Busca Online com Replanning A*.")
    parser.add_argument("mapa", help="Arquivo .txt do labirinto real.")
    parser.add_argument("--saida", default="resultados/online", help="Pasta de saída dos resultados.")
    parser.add_argument("--raio", type=int, default=1, help="Raio de percepção em distância Manhattan. Padrão: 1.")
    parser.add_argument("--max-passos", type=int, default=None, help="Limite máximo de movimentos do agente.")
    parser.add_argument("--mostrar", action="store_true", help="Mostra visualizações no terminal.")
    parser.add_argument("--frames", action="store_true", help="Salva frames passo a passo do mapa interno.")
    args = parser.parse_args()

    saida = Path(args.saida)
    lab = LabirintoOnline(args.mapa, raio_percepcao=args.raio)

    pasta_frames = saida / "frames" if args.frames else None
    resultado = lab.executar_replanning_astar(
        max_passos=args.max_passos,
        salvar_frames=args.frames,
        pasta_frames=pasta_frames,
    )

    imprimir_resumo(resultado)
    salvar_resultados(resultado, lab, saida)

    print(f"Resultados salvos em: {saida}")
    print(f"CSV métricas         : {saida / 'metricas_online.csv'}")
    print(f"CSV trajetória       : {saida / 'trajetoria_online.csv'}")
    print(f"Mapa real + trajeto  : {saida / 'mapa_real_com_trajeto.txt'}")
    print(f"Mapa interno final   : {saida / 'mapa_interno_final.txt'}")
    if args.frames:
        print(f"Frames passo a passo : {pasta_frames}")

    if args.mostrar:
        print("\nMapa real com trajetória online:")
        print(lab.renderizar_mapa_real_com_trajeto(resultado.trajetoria))
        print("\nMapa interno final do agente:")
        print(lab.renderizar_mapa_interno_com_trajeto(
            resultado.mapa_interno_final,
            resultado.trajetoria,
            resultado.trajetoria[-1] if resultado.trajetoria else None,
        ))


if __name__ == "__main__":
    main()
