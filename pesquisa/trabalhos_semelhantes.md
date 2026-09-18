# Trabalhos semelhantes e pesquisadores

Pesquisa inicial realizada em 18/09/2026. O projeto atual é mais específico que
a maior parte da literatura encontrada: ele prevê o tempo de corte de uma peça a
partir da geometria do DXF, material e espessura. Muitos estudos de plasma
preveem qualidade, velocidade, kerf ou remoção de material, e não o tempo total
da peça. Essa diferença deve ser declarada no trabalho acadêmico.

## Referências mais próximas

### Mirjam Bakker — previsão de carga na máquina plasma V310 (2023)

Trabalho de conclusão na University of Twente, desenvolvido com a Voortman Steel
Machinery. Combina regressão linear e estudo de tempos para prever horas de mão
de obra no corte de chapas com uma máquina plasma V310. É a referência mais
próxima em processo e objetivo de planejamento, embora estime carga operacional
e quantidade de nestings, não o tempo individual de cada peça por DXF.

Fonte: https://essay.utwente.nl/97072/

### Anas Ma'ruf, Dimas Ahmad Thoriq e Kresna Surya Buwana — tempo de usinagem MTO (2024)

O artigo compara regressão linear múltipla, árvores de gradient boosting e rede
neural para estimar tempo de usinagem CNC em produção sob encomenda. Mostra a
importância de variáveis geométricas e de CAM, como comprimento de corte e
espessura, para estimar tempo cedo no processo. É diretamente útil para
justificar as entradas geométricas desta V2 e o uso da regressão múltipla como
baseline acadêmico.

DOI: https://doi.org/10.1016/j.procir.2024.10.063

### Konstantinos Salonitis e S. Vatousianos — investigação do corte plasma (2012)

O estudo usa análise estatística e modelos de regressão para relacionar corrente,
velocidade, altura de corte e pressão do gás à qualidade do corte plasma. Os
autores também relatam perda de validade ao aplicar o modelo a outro material,
reforçando a necessidade de representar o material e evitar extrapolações.

DOI: https://doi.org/10.1016/j.procir.2012.07.050

### Deepak Kumar Naik e Kalipada Maity — regressão múltipla em PAC (2020)

Os autores desenvolveram modelos de regressão múltipla para prever remoção de
material, kerf e rugosidade no corte plasma de Hardox 400 e Abrex 400. O alvo é
diferente do tempo, mas o trabalho demonstra o uso de regressão múltipla como
modelo empírico para respostas do processo PAC.

Referência: https://doi.org/10.1142/S0218625X19502065

### Estudo de otimização da velocidade de corte plasma (2022)

O artigo compara regressão e rede neural para prever/otimizar velocidade de corte
a partir da largura do kerf, corrente e espessura. Ele sustenta que modelos de
regressão são adequados para relações empíricas do plasma e que espessura e
parâmetros do corte devem ser considerados.

DOI: https://doi.org/10.1016/j.cirpj.2022.07.003

### Predição de tempo de usinagem com KNN ponderado (2026)

O método propõe recuperar peças historicamente semelhantes e estimar o tempo por
vizinhos mais próximos ponderados, usando características geométricas, de
material e de processo. A ideia é muito próxima da lógica do KNN desta V2, na
qual a previsão de uma nova peça vem dos tempos de peças semelhantes.

Patente CN122694168A: https://patents.google.com/patent/CN122694168A/en

## Como posicionar este projeto

Uma formulação adequada para o relatório é:

> O projeto adapta métodos supervisionados sem árvores à previsão do tempo de
> corte plasma por peça. Diferentemente de estudos focados apenas em qualidade do
> kerf ou velocidade, utiliza atributos geométricos extraídos do DXF, material e
> espessura, comparando KNN Regressor com uma regressão regularizada sob a mesma
> validação fora da amostra.

## Cuidados para a revisão bibliográfica

- Não afirmar que os trabalhos de qualidade do corte preveem tempo; eles são
  semelhantes pelo processo e pela modelagem, mas têm outros alvos.
- Separar tempo de máquina, tempo de corte efetivo e horas de operador.
- Registrar máquina, consumíveis, material e faixa de espessura, pois os modelos
  empíricos podem perder validade fora do domínio de treinamento.
- Comparar modelos com MAE, RMSE e R² na mesma divisão de validação.

