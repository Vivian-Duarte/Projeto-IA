# Uso de IA Generativa

Este arquivo documenta o uso de ferramentas de IA generativa durante o desenvolvimento do Trabalho Prático de Inteligência Artificial: **Agente Inteligente em Labirinto**, conforme solicitado no enunciado da disciplina.

A IA generativa foi utilizada como ferramenta de apoio para estudo, revisão, organização e validação conceitual. Os códigos, resultados e análises foram conferidos por meio de execução local, comparação com os arquivos gerados e revisão com base nos materiais da disciplina.

Todas as sugestões foram avaliadas criticamente antes de serem aceitas, adaptadas ou rejeitadas.

---

## 1. Ferramenta utilizada

A ferramenta de IA utilizada foi:

- **ChatGPT**

A ferramenta foi usada para apoio em:

- interpretar os requisitos do enunciado;
- apoiar a correção de problemas em partes do código;
- explicar erros de execução;
- sugerir comandos de execução;
- sugerir melhorias de formatação no relatório;
- apoiar a organização do relatório técnico;
- auxiliar na criação da documentação do projeto.

---

## 2. Principais usos da IA

A IA foi utilizada principalmente para:

1. interpretar o enunciado do trabalho;
2. conferir se os códigos implementaram algoritmos obrigatórios;
3. comparar resultados obtidos com as tabelas do relatório;
4. explicar erros de execução no PowerShell;
5. sugerir comandos para instalação de dependências;
6. sugerir comandos para executar os códigos;
7. explicar os gráficos gerados pela busca local;
8. sugerir melhorias na estrutura do relatório.

---

## 3. Principais prompts utilizados

### Prompt 1 - Interpretação do enunciado

```text
No arquivo "pdf Trabalho IA", está tudo o que meu professor pediu para que fosse feito.
Quero que você interprete cuidadosamente todos os requisitos e confira se meu trabalho atende ao que foi solicitado.
```

### Prompt 2 - Revisão dos códigos

```text
Nos arquivos "Código busca_online_labirinto.py", "código do busca_local_labirinto" e "código do busca_classica_labirinto", estão meus códigos referentes ao trabalho.
Quero que você confira se eles estão corretos com base no que o professor pediu.
```

### Prompt 3 - Explicação de erro de execução

```text
Estou tentando executar o código no PowerShell e apareceu este erro.
Explique o que está acontecendo e como corrigir.
```

### Prompt 4 - Dúvida conceitual sobre métricas

```text
No meu código de busca clássica, estou contando nós explorados e nós expandidos separadamente.
Qual é a diferença exata entre os dois?
Estou contando certo se explorados são os nós retirados da fronteira e expandidos são os nós cujos filhos foram gerados?
```

### Prompt 5 - Visualizações obrigatórias

```text
Quais arquivos do meu projeto já servem como visualização obrigatória para cada parte do trabalho?
```

### Prompt 6 - Dúvida sobre admissibilidade da heurística

```text
A heurística de Manhattan é admissível para este labirinto?
E se os custos dos movimentos fossem diferentes de 1, ela continuaria sendo admissível?
```

### Prompt 7 - Dúvida sobre o ciclo da busca online

```text
No meu agente online, após perceber o ambiente, devo executar o caminho completo planejado pelo A* ou apenas o próximo passo e replanejar depois?
```

### Prompt 8 - Revisão da modelagem PEAS

```text
Baseado no enunciado do professor, revisei minha modelagem PEAS.
Você consegue identificar se algum componente está incompleto ou incorreto?
A função de desempenho J que defini está coerente com o que o professor pediu?
```

### Prompt 9 - Revisão de trecho de código

```text
Corrija o erro no código.
Por que ele não está compilando?
```

---

## 4. Trechos e comandos sugeridos por IA

A IA sugeriu principalmente comandos de execução, comandos de instalação e pequenas correções práticas para melhorar a reprodutibilidade do projeto.

### 4.1 Instalação de dependência

```powershell
python -m pip install matplotlib
```

Esse comando foi usado porque o projeto gera gráficos da busca local com Matplotlib.

---

### 4.2 Correção de codificação no PowerShell

```powershell
chcp 65001
$env:PYTHONIOENCODING="utf-8"
```

Esses comandos foram sugeridos para evitar problemas de codificação ao imprimir caracteres especiais no terminal do Windows.

---

### 4.3 Execução da busca clássica

```powershell
python busca_classica_labirinto.py mapas/labirinto_01.txt --saida-csv resultados/resultados_busca_classica_labirinto_01.csv --saida-vis resultados/vis_labirinto_01 --mostrar
```

---

### 4.4 Execução da busca local

```powershell
python busca_local_labirinto.py mapas/coletas_01.txt --execucoes 30 --saida resultados/coletas_01 --mostrar
```

---

### 4.5 Execução da busca online

```powershell
python busca_online_labirinto.py mapas/labirinto_01.txt --saida resultados/online_labirinto_01 --mostrar --frames
```

---

### 4.6 Salvamento da saída em arquivo `.txt`

```powershell
python busca_local_labirinto.py mapas/coletas_01.txt --execucoes 30 --saida resultados/coletas_01 --mostrar | Tee-Object -FilePath resultados/coletas_01/visualizacao_rota_otimizada.txt -Encoding utf8
```

Esse comando foi sugerido para salvar a visualização textual da busca local em arquivo, além de exibi-la no terminal.

---

### 4.7 Correção sugerida em impressão textual

A IA sugeriu trocar caracteres especiais de linha, como:

```python
print(f"\n{'─'*55}")
```

por:

```python
print(f"\n{'-'*55}")
```

Essa alteração foi sugerida apenas para evitar erro de codificação no Windows/PowerShell. Ela não altera a lógica dos algoritmos.

---

## 5. Sugestões aceitas

As principais sugestões aceitas foram:

1. organizar o relatório por partes, separando busca clássica, busca local e busca online;
2. adicionar visualizações no relatório;
3. inserir uma visualização da busca clássica;
4. inserir o gráfico de convergência da busca local;
5. inserir o mapa interno final da busca online;
6. explicar os gráficos da busca local, como boxplot, comparativo de custos e curva de convergência;
7. corrigir pequenos erros de escrita e formatação no relatório;
8. ajustar comandos de execução para facilitar a reprodução do projeto;
9. revisar se os entregáveis obrigatórios estavam presentes.

---

## 6. Sugestões rejeitadas ou não utilizadas

Algumas sugestões não foram utilizadas ou foram adaptadas pelo grupo.

### 6.1 Criar uma interface gráfica completa

A IA explicou que o professor exigia uma visualização do comportamento do agente, mas não obrigatoriamente uma interface gráfica ou web.

Como o projeto já gerava visualizações em `.txt`, gráficos `.png` e frames da busca online, decidimos não criar uma interface adicional.

---

### 6.2 Inserir todos os gráficos no relatório

A IA explicou que os gráficos `boxplot_custos.png`, `comparativo_custos.png`, `convergencia.png` e `taxa_sucesso.png` eram úteis.

Porém, para evitar um relatório muito grande, o grupo priorizou a curva de convergência e manteve os demais gráficos nos arquivos de resultados.

---

### 6.3 Implementar Algoritmo Genético

O Algoritmo Genético foi considerado, mas não foi implementado porque, no enunciado, ele aparecia como bônus, não como algoritmo obrigatório.

Decidimos focar nos algoritmos obrigatórios:

- Hill-Climbing;
- Simulated Annealing.

---

### 6.4 Mudar os algoritmos principais depois dos testes

Após os resultados ficarem coerentes com o relatório, o grupo optou por não alterar a lógica principal dos algoritmos, realizando apenas ajustes de documentação e formatação.

---

## 7. Erros cometidos pela IA

Durante o uso da IA, algumas respostas precisaram ser revisadas criticamente.

### 7.2 Possível excesso de confiança em respostas intermediárias

Algumas respostas iniciais da IA precisaram ser verificadas com os arquivos reais do projeto, especialmente quando envolviam tabelas, imagens e resultados.

---

### 7.3 Sugestões de formatação que precisaram ser adaptadas

Algumas sugestões de legenda, organização de tabela e texto foram adaptadas para manter o estilo do relatório e evitar excesso de formalidade.

---

### 7.4 Contagem incorreta de nós explorados e nós expandidos

Em uma revisão do código, a IA afirmou que “nós explorados” e “nós expandidos” eram a mesma métrica e que bastava registrar um único contador.

Após conferência com o material da disciplina, identificamos que são conceitos distintos:

- **nós explorados** são os retirados da fronteira para análise;
- **nós expandidos** são aqueles cujos sucessores foram gerados.

O código já implementava os dois contadores separadamente desde o início, e a resposta da IA foi descartada.

---

### 7.5 Sugestão incorreta sobre a admissibilidade da heurística de Manhattan com custos variáveis

Ao perguntar se a heurística de Manhattan continuaria admissível caso os custos dos movimentos variassem, a IA respondeu que sim, desde que os custos fossem positivos.

Isso está incorreto.

A admissibilidade depende de `h(n)` nunca superestimar o custo real. Se um movimento puder custar menos que 1, a distância de Manhattan poderia superestimar o custo real e deixaria de ser admissível.

A resposta foi corrigida com base na definição formal estudada em aula.

---

### 7.6 Orientação errada sobre o critério de parada do Hill-Climbing

A IA sugeriu que o Hill-Climbing deveria continuar executando mesmo sem encontrar melhoria, reiniciando automaticamente com uma nova solução aleatória a cada iteração sem melhoria.

Isso confundia o Hill-Climbing simples com o Hill-Climbing com múltiplos reinícios, que são estratégias diferentes.

No código implementado, o Hill-Climbing simples para ao atingir um mínimo local, e os reinícios são controlados externamente pelo parâmetro:

```powershell
--hc-reinicios
```

A sugestão foi rejeitada para manter a separação conceitual correta entre os dois comportamentos.

---

### 7.7 Erro na interpretação do ciclo da busca online

Em uma consulta sobre a busca online, a IA sugeriu que o agente deveria planejar o caminho completo até `B` a cada replanejamento e executar todos os passos antes de replanejar novamente.

Essa abordagem ignora o princípio central da busca online, que é executar apenas o próximo passo e replanejar após cada percepção.

O código implementado segue o ciclo correto:

```text
perceber -> atualizar mapa interno -> planejar -> agir um passo -> repetir
```

---

## 8. Como avaliamos a solução

A validação da solução foi feita manualmente pelo grupo, por meio de execução, conferência dos resultados e comparação com a teoria estudada na disciplina.

---

### 8.1 Execução dos códigos

Os três códigos principais foram executados localmente:

```text
busca_classica_labirinto.py
busca_local_labirinto.py
busca_online_labirinto.py
```

Foram realizados testes com os mapas:

```text
labirinto_01.txt
labirinto_02.txt
labirinto_03.txt
coletas_01.txt
coletas_02.txt
coletas_03.txt
```

---

### 8.2 Conferência dos resultados

Os resultados impressos no terminal foram comparados com:

```text
arquivos .csv gerados
tabelas do relatório
visualizações em .txt
gráficos .png
frames da busca online
```

---

### 8.3 Conferência das métricas obrigatórias

Foram verificadas as métricas exigidas no enunciado.

#### Busca clássica

```text
sucesso
custo
passos
nós explorados
nós expandidos
tempo
fronteira máxima
```

#### Busca local

```text
melhor custo
pior custo
custo médio
tempo médio
iterações médias
taxa de sucesso
curva de convergência
```

#### Busca online

```text
sucesso
custo online
custo offline
razão online/offline
células reveladas
células revisitadas
replanejamentos
nós expandidos
tempo
```

---

### 8.4 Conferência das visualizações

Foram conferidas visualizações como:

```text
resultados/vis_labirinto_01/aestrela.txt
resultados/coletas_03/convergencia.png
resultados/online_labirinto_03/mapa_interno_final.txt
resultados/online_labirinto_03/frames/
```

---

### 8.5 Comparação com a teoria da disciplina

Foi conferido se o comportamento dos algoritmos era coerente com os conceitos vistos em aula:

- BFS encontra menor caminho quando os custos são uniformes;
- DFS não garante otimalidade em geral;
- UCS é adequado para custos acumulados;
- Busca Gulosa usa apenas a heurística;
- A* combina custo real e heurística;
- Hill-Climbing pode parar em mínimos locais;
- Simulated Annealing pode aceitar soluções piores temporariamente;
- Busca online pode tomar decisões subótimas por falta de informação.

---

## 9. Modificações feitas pelo grupo após o uso da IA

Após as sugestões e revisões com IA, o grupo realizou as seguintes modificações:

1. ajustou a tabela da busca clássica no relatório;
2. inseriu a tabela de resultados da busca local;
3. inseriu a tabela de resultados da busca online;
4. corrigiu nomes de arquivos, como `coletas_03.txt`;
5. adicionou explicações sobre os gráficos da busca local;
6. adicionou explicações sobre o mapa interno da busca online;
7. corrigiu pequenos erros de digitação e acentuação;
8. organizou melhor a seção de visualizações obrigatórias;
9. conferiu os resultados experimentais com os arquivos gerados;
10. ajustou comandos de execução para facilitar a reprodução do projeto.

---

## 10. Limites do uso da IA

A IA foi usada como ferramenta de apoio, mas a validação final foi feita manualmente.

A IA pode cometer erros, interpretar arquivos de forma incompleta ou sugerir soluções que precisam ser adaptadas.

Por isso, nenhuma resposta foi aceita sem conferência com:

- enunciado do trabalho;
- materiais da disciplina;
- códigos implementados;
- resultados gerados;
- execuções locais.

---

## 11. Conclusão

O uso de IA generativa contribuiu para organizar o trabalho, revisar conceitos, identificar possíveis inconsistências e melhorar a documentação.

No entanto, os códigos foram executados, os resultados foram conferidos e as análises foram revisadas manualmente.

A IA foi utilizada como apoio ao aprendizado e à validação, não como substituta da compreensão do conteúdo.
