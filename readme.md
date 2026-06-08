# Projeto IA - Agente Inteligente em Labirinto

Este projeto foi desenvolvido para o Trabalho Prático de Inteligência Artificial sobre agentes inteligentes em labirintos. O objetivo é implementar e analisar um agente capaz de resolver labirintos em três situações diferentes:

1. **Busca clássica** em labirinto conhecido;
2. **Busca local** com pontos de coleta obrigatórios;
3. **Busca online** em labirinto inicialmente desconhecido.

O projeto foi implementado em **Python** e gera resultados experimentais em arquivos `.csv`, visualizações textuais em `.txt`, gráficos `.png` e frames da trajetória online.

---

## 1. Estrutura do projeto

A estrutura principal do projeto é:

```text
projeto_IA/
├── mapas/
│   ├── labirinto_01.txt
│   ├── labirinto_02.txt
│   ├── labirinto_03.txt
│   ├── coletas_01.txt
│   ├── coletas_02.txt
│   └── coletas_03.txt
│
├── resultados/
│   ├── coletas_01/
│   ├── coletas_02/
│   ├── coletas_03/
│   ├── online_labirinto_01/
│   ├── online_labirinto_02/
│   ├── online_labirinto_03/
│   ├── vis_labirinto_01/
│   ├── vis_labirinto_02/
│   └── vis_labirinto_03/
│
├── busca_classica_labirinto.py
├── busca_local_labirinto.py
├── busca_online_labirinto.py
├── README.md
├── uso_ia.md
└── relatório.pdf
```

---

## 2. Requisitos

Para executar o projeto, é necessário ter o Python instalado.

Versão utilizada nos testes:

```bash
Python 3.12.10
```

A única biblioteca externa necessária é o `matplotlib`, usado para gerar os gráficos da busca local.

Para instalar:

```bash
python -m pip install matplotlib
```

Caso o PowerShell apresente problemas com caracteres especiais, execute antes:

```powershell
chcp 65001
$env:PYTHONIOENCODING="utf-8"
```

---

## 3. Formato dos mapas

Os mapas são arquivos `.txt` em formato ASCII.

Legenda utilizada:

```text
A = posição inicial do agente
B = objetivo final
C = ponto de coleta obrigatório
# = parede ou obstáculo
  = célula livre
? = célula desconhecida no modo online
```

O agente pode se mover apenas em quatro direções ortogonais:

```text
cima, baixo, esquerda e direita
```

Não são permitidos movimentos diagonais.

---

## 4. Parte II - Busca Clássica no Labirinto Conhecido

Nesta parte, o agente conhece o mapa completo desde o início e deve encontrar um caminho de `A` até `B`.

Algoritmos implementados:

1. BFS - Busca em Largura;
2. DFS - Busca em Profundidade;
3. UCS - Busca de Custo Uniforme;
4. Busca Gulosa;
5. A*.

A heurística utilizada nos algoritmos informados foi a distância de Manhattan:

```text
h(n) = |x_n - x_B| + |y_n - y_B|
```

### Executar Labirinto 01

```powershell
python busca_classica_labirinto.py mapas/labirinto_01.txt --saida-csv resultados/resultados_busca_classica_labirinto_01.csv --saida-vis resultados/vis_labirinto_01 --mostrar
```

### Executar Labirinto 02

```powershell
python busca_classica_labirinto.py mapas/labirinto_02.txt --saida-csv resultados/resultados_busca_classica_labirinto_02.csv --saida-vis resultados/vis_labirinto_02 --mostrar
```

### Executar Labirinto 03

```powershell
python busca_classica_labirinto.py mapas/labirinto_03.txt --saida-csv resultados/resultados_busca_classica_labirinto_03.csv --saida-vis resultados/vis_labirinto_03 --mostrar
```

### Arquivos gerados na busca clássica

Para cada labirinto, são gerados:

```text
resultados/resultados_busca_classica_labirinto_XX.csv
resultados/vis_labirinto_XX/bfs.txt
resultados/vis_labirinto_XX/dfs.txt
resultados/vis_labirinto_XX/ucs.txt
resultados/vis_labirinto_XX/gulosa.txt
resultados/vis_labirinto_XX/aestrela.txt
```

Nas visualizações textuais:

```text
. = caminho encontrado
x = nós expandidos ou visitados
A = início
B = objetivo
# = parede
```

---

## 5. Parte III - Busca Local com Pontos de Coleta

Nesta parte, o agente deve sair de `A`, visitar todos os pontos de coleta `C` e terminar em `B`.

O problema passa a ser encontrar uma boa ordem de visitação:

```text
A -> Cπ(1) -> Cπ(2) -> ... -> Cπ(k) -> B
```

Algoritmos implementados:

1. Hill-Climbing;
2. Simulated Annealing.

A solução é representada como uma permutação dos pontos de coleta.

A função de custo soma as menores distâncias entre os pontos relevantes:

```text
C(s) = d(A, Cπ(1)) + Σ d(Cπ(i), Cπ(i+1)) + d(Cπ(k), B)
```

As distâncias entre os pontos são calculadas com A*.

### Antes de executar
Antes de executar os comandos, para evitar problema de acento/caractere especial, rode:
```powershell
chcp 65001
$env:PYTHONIOENCODING="utf-8"
```

### Executar Coletas 01

```powershell
python busca_local_labirinto.py mapas/coletas_01.txt --execucoes 30 --saida resultados/coletas_01 --mostrar
```

### Executar Coletas 02

```powershell
python busca_local_labirinto.py mapas/coletas_02.txt --execucoes 30 --saida resultados/coletas_02 --mostrar
```

### Executar Coletas 03

```powershell
python busca_local_labirinto.py mapas/coletas_03.txt --execucoes 30 --saida resultados/coletas_03 --mostrar
```

### Salvar também a visualização textual da rota otimizada

Para salvar a saída exibida no terminal em um arquivo `.txt`, use:

```powershell
python busca_local_labirinto.py mapas/coletas_01.txt --execucoes 30 --saida resultados/coletas_01 --mostrar | Tee-Object -FilePath resultados/coletas_01/visualizacao_rota_otimizada.txt -Encoding utf8
```

### Arquivos gerados na busca local

Para cada mapa de coleta, são gerados:

```text
resultados/coletas_XX/resultados_busca_local.csv
resultados/coletas_XX/resultados_busca_local_raw.csv
resultados/coletas_XX/convergencia.png
resultados/coletas_XX/boxplot_custos.png
resultados/coletas_XX/comparativo_custos.png
resultados/coletas_XX/taxa_sucesso.png
```

Função dos principais arquivos:

```text
resultados_busca_local.csv      = métricas agregadas
resultados_busca_local_raw.csv  = custos individuais por execução
convergencia.png                = curva iteração × melhor custo
boxplot_custos.png              = distribuição dos custos
comparativo_custos.png          = comparação entre melhor, médio e pior custo
taxa_sucesso.png                = taxa de sucesso dos algoritmos
```

Na visualização textual da rota:

```text
. = caminho da rota
* = ponto de coleta visitado
A = início
B = objetivo
# = parede
```

---

## 6. Parte IV - Busca Online no Labirinto Desconhecido

Nesta parte, o agente não conhece o mapa completo no início.

O simulador possui o mapa real, mas o agente utiliza apenas um mapa interno inicialmente desconhecido, preenchido com `?`.

A estratégia implementada foi:

```text
Replanning com A*
```

A cada passo, o agente executa o ciclo:

```text
perceber -> atualizar mapa interno -> planejar -> agir
```

O agente percebe apenas uma vizinhança local com raio de percepção `r = 1`.

### Executar Labirinto 01

```powershell
python busca_online_labirinto.py mapas/labirinto_01.txt --saida resultados/online_labirinto_01 --mostrar --frames
```

### Executar Labirinto 02

```powershell
python busca_online_labirinto.py mapas/labirinto_02.txt --saida resultados/online_labirinto_02 --mostrar --frames
```

### Executar Labirinto 03

```powershell
python busca_online_labirinto.py mapas/labirinto_03.txt --saida resultados/online_labirinto_03 --mostrar --frames
```

### Arquivos gerados na busca online

Para cada labirinto, são gerados:

```text
resultados/online_labirinto_XX/metricas_online.csv
resultados/online_labirinto_XX/trajetoria_online.csv
resultados/online_labirinto_XX/mapa_real_com_trajeto.txt
resultados/online_labirinto_XX/mapa_interno_final.txt
resultados/online_labirinto_XX/mapa_interno_final_com_trajeto.txt
resultados/online_labirinto_XX/caminho_otimo_offline.txt
resultados/online_labirinto_XX/frames/
```

Função dos principais arquivos:

```text
metricas_online.csv                  = métricas finais da busca online
trajetoria_online.csv                = trajetória passo a passo do agente
mapa_real_com_trajeto.txt            = mapa real com o trajeto percorrido
mapa_interno_final.txt               = mapa interno construído pelo agente
mapa_interno_final_com_trajeto.txt   = mapa interno final com trajetória
caminho_otimo_offline.txt            = caminho ótimo calculado com mapa completo
frames/                              = evolução passo a passo da trajetória online
```

Na visualização online:

```text
. = trajetória percorrida
? = célula ainda desconhecida
A = início
B = objetivo
# = parede
```

---

## 7. Métricas coletadas

### Busca Clássica

Foram coletadas as seguintes métricas:

```text
sucesso
custo do caminho
passos
nós explorados
nós expandidos
tempo de execução
tamanho máximo da fronteira
```

### Busca Local

Foram coletadas as seguintes métricas:

```text
melhor custo encontrado
pior custo encontrado
custo médio
tempo médio
número médio de iterações
taxa de sucesso
curva de convergência
```

### Busca Online

Foram coletadas as seguintes métricas:

```text
sucesso
custo online
custo offline
razão online/offline
células reveladas
células revisitadas
replanejamentos
nós expandidos no planejamento
tempo de execução
```

A métrica central da busca online é:

```text
razão online/offline = custo percorrido pelo agente online / custo ótimo offline
```

---

## 8. Visualizações obrigatórias

O projeto gera visualizações para atender aos requisitos do trabalho.

### Mapa original

Os mapas originais estão em:

```text
mapas/labirinto_01.txt
mapas/labirinto_02.txt
mapas/labirinto_03.txt
mapas/coletas_01.txt
mapas/coletas_02.txt
mapas/coletas_03.txt
```

### Caminho encontrado e nós expandidos

As visualizações da busca clássica estão em:

```text
resultados/vis_labirinto_01/
resultados/vis_labirinto_02/
resultados/vis_labirinto_03/
```

### Rota otimizada da busca local

As visualizações e gráficos da busca local estão em:

```text
resultados/coletas_01/
resultados/coletas_02/
resultados/coletas_03/
```

### Trajetória online passo a passo

Os frames e arquivos da busca online estão em:

```text
resultados/online_labirinto_01/frames/
resultados/online_labirinto_02/frames/
resultados/online_labirinto_03/frames/
```

---

## 9. Resultados esperados

Ao executar os códigos, espera-se que:

1. A busca clássica encontre caminhos de `A` até `B` nos três labirintos;
2. BFS, UCS e A* encontrem caminhos de custo ótimo nos mapas testados;
3. A busca local encontre uma ordem válida para visitar todos os pontos de coleta;
4. Hill-Climbing e Simulated Annealing gerem métricas e gráficos comparativos;
5. A busca online alcance o objetivo mesmo sem conhecer o mapa completo inicialmente;
6. A razão online/offline seja maior que 1 quando o agente online percorre caminho maior que o ótimo offline.

---

## 10. Executando tudo novamente

Para reproduzir todos os resultados principais, execute os comandos abaixo na raiz do projeto.

### Busca clássica

```powershell
python busca_classica_labirinto.py mapas/labirinto_01.txt --saida-csv resultados/resultados_busca_classica_labirinto_01.csv --saida-vis resultados/vis_labirinto_01 --mostrar
python busca_classica_labirinto.py mapas/labirinto_02.txt --saida-csv resultados/resultados_busca_classica_labirinto_02.csv --saida-vis resultados/vis_labirinto_02 --mostrar
python busca_classica_labirinto.py mapas/labirinto_03.txt --saida-csv resultados/resultados_busca_classica_labirinto_03.csv --saida-vis resultados/vis_labirinto_03 --mostrar
```

### Busca local

```powershell
python busca_local_labirinto.py mapas/coletas_01.txt --execucoes 30 --saida resultados/coletas_01 --mostrar
python busca_local_labirinto.py mapas/coletas_02.txt --execucoes 30 --saida resultados/coletas_02 --mostrar
python busca_local_labirinto.py mapas/coletas_03.txt --execucoes 30 --saida resultados/coletas_03 --mostrar
```

### Busca online

```powershell
python busca_online_labirinto.py mapas/labirinto_01.txt --saida resultados/online_labirinto_01 --mostrar --frames
python busca_online_labirinto.py mapas/labirinto_02.txt --saida resultados/online_labirinto_02 --mostrar --frames
python busca_online_labirinto.py mapas/labirinto_03.txt --saida resultados/online_labirinto_03 --mostrar --frames
```

---

## 11. Execução em mapas novos

Os códigos aceitam mapas novos, desde que estejam no formato correto.

Para busca clássica e busca online, o mapa deve conter:

```text
exatamente um A
exatamente um B
paredes representadas por #
células livres representadas por espaço em branco
```

Para busca local, o mapa deve conter:

```text
exatamente um A
exatamente um B
ao menos um ponto C
paredes representadas por #
células livres representadas por espaço em branco
```

Exemplo de execução com mapa novo:

```powershell
python busca_classica_labirinto.py mapas/novo_labirinto.txt --saida-csv resultados/novo_labirinto.csv --saida-vis resultados/vis_novo_labirinto --mostrar
```

---

## 12. Arquivo de uso de IA

O uso de IA generativa foi declarado no relatório e detalhado no arquivo:

```text
uso_ia.md
```

Esse arquivo descreve:

```text
ferramentas utilizadas
principais prompts
trechos sugeridos por IA
sugestões aceitas
sugestões rejeitadas
erros cometidos pela IA
forma de validação feita pelo grupo
modificações realizadas pelo grupo
```

---

## 13. Observações finais

Os algoritmos de busca foram implementados diretamente no código, utilizando estruturas básicas da linguagem Python, como filas, pilhas, heaps e listas.

Não foram utilizadas bibliotecas prontas de busca.

A biblioteca `matplotlib` foi utilizada apenas para geração dos gráficos da busca local.

Os resultados podem apresentar pequenas variações no tempo de execução, pois essa métrica depende do computador, do terminal e dos processos em execução no momento do teste.
