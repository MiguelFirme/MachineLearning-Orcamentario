# Andamento da V2

Este arquivo é o ponto de retomada do projeto. Atualize-o ao concluir cada etapa.

## Estado atual

- Data de início: 18/09/2026.
- Escopo: somente previsão do tempo de corte plasma.
- Dobras: adiadas para uma etapa futura.
- Modelos proibidos nesta versão: árvores de decisão, Random Forest, XGBoost e
  derivados.
- Modelos previstos: KNN Regressor e uma regressão escolhida entre múltipla
  Ridge e polinomial Ridge.

## Etapas

- [x] Mapear o projeto anterior e a pasta V2.
- [x] Identificar o dataset mais recente e o extrator de geometria úteis.
- [x] Copiar para V2 somente o dataset V10 e o extrator de DXF necessários.
- [x] Auditar o dataset: 1.919 linhas totais e 1.141 peças válidas para plasma.
- [x] Criar ambiente e arquivo de dependências portáteis.
- [x] Implementar treinamento sem árvores e com validação aninhada.
- [x] Executar o treinamento completo e registrar as métricas.
- [x] Confirmar empiricamente a escolha entre regressão múltipla e polinomial.
- [x] Implementar o programa de previsão de uma nova peça.
- [x] Validar o programa de previsão em um DXF real conhecido.
- [x] Registrar trabalhos semelhantes e pesquisadores relacionados.

## Decisões técnicas registradas

1. O problema é de regressão, pois o alvo é tempo em segundos. Portanto, será
   usado `KNeighborsRegressor`, e não KNN de classificação.
2. Todas as variáveis são padronizadas dentro do pipeline. Isso é indispensável
   para o cálculo de distância do KNN.
3. Ridge foi adotado para as regressões por causa da correlação forte entre
   medidas como perímetros, área, peso e dimensões.
4. A regressão polinomial usa grau 2 e Ridge para limitar instabilidade e
   sobreajuste.
5. A polinomial só substitui a múltipla se reduzir o MAE fora da amostra em pelo
   menos 2%. Em empate prático, a múltipla é preferida por ser mais simples.
6. A validação é aninhada: a parte externa mede generalização e a interna escolhe
   hiperparâmetros. Entradas idênticas são agrupadas na mesma dobra.
7. O KNN compara as distâncias Manhattan, Euclidiana e Chebyshev pelo MAE da
   validação interna. Manhattan venceu nas cinco dobras externas e no ajuste final.
   Os MAEs internos médios foram 18,92 s (Manhattan), 19,46 s (Euclidiana) e
   20,72 s (Chebyshev).

## Próximo passo ao retomar

As duas etapas solicitadas estão concluídas. A apresentação de 22 slides com
conteúdo ampliado é a versão atual. Antes da defesa, revisar o tempo disponível
e ensaiar as notas. Caso o professor peça mudanças, editar essa versão e
atualizar este registro.

## Etapa 1 do relatório concluída em 30/09/2026

- [x] Ler o modelo `Relatório.docx` e mapear todas as perguntas exigidas.
- [x] Conferir o dataset, as 1.141 previsões externas e as métricas registradas.
- [x] Verificar as referências centrais em páginas da universidade e dos periódicos.
- [x] Gerar em Python nove gráficos em `graficos_treinamento/`, incluindo a matriz
  diagnóstica de faixas de tempo dos dois modelos finais.
- [x] Preencher `Relatório_preenchido.docx` com metodologia, estado da arte,
  resultados, interpretação das métricas e referências.
- [x] Renderizar e conferir visualmente as 17 páginas do relatório; a legenda
  e a escala da matriz foram ajustadas após a primeira conferência.

**Ponto de retomada:** a etapa 1 está pronta. Os arquivos de entrega são
`Relatório_preenchido.docx` e os PNGs em `graficos_treinamento/`. O arquivo
original `Relatório.docx` foi preservado.

**Plano da etapa 2:** definir roteiro de 8 a 12 slides; destacar a diferença
entre os estudos publicados e o alvo deste projeto; mostrar dados e validação;
explicar MAE, RMSE e R² com exemplos; comparar KNN e Ridge; apresentar a matriz
por faixas com a ressalva de que o problema é de regressão; concluir com
limitações e aplicação prática.

## Etapa 2 da apresentação concluída em 30/09/2026

- [x] Organizar 13 slides com foco ampliado no estado da arte e nos dois modelos.
- [x] Explicar MAE, RMSE e R² e a razão de recall, F1 e ROC não serem métricas
  próprias para o alvo contínuo deste projeto.
- [x] Inserir distribuição dos tempos, comparação dos modelos e matriz
  diagnóstica por faixas; o gráfico de MAE no slide 11 é editável no PowerPoint.
- [x] Acrescentar notas do apresentador com explicações e fontes bibliográficas.
- [x] Validar a estrutura do PPTX e renderizar os 13 slides para conferência.
- [x] Corrigir o alinhamento dos valores de RMSE e R² no slide de resultados.

**Arquivo final para apresentar:** `apresentacao/Previsao_tempo_corte_plasma_v2.pptx`.
O arquivo sem o sufixo `_v2` é uma versão anterior, mantida apenas como histórico
de revisão. O relatório da etapa 1 permanece em `Relatório_preenchido.docx`.

## Revisão detalhada da apresentação em 30/09/2026

- [x] Ampliar a seção de estado da arte para um slide por artigo, com pergunta,
  método ou entradas, resultado e relação com o projeto.
- [x] Acrescentar slides sobre diagnóstico da base, preparação das entradas,
  escolha da distância do KNN e interpretação concreta de MAE, RMSE e R².
- [x] Gerar em Python o gráfico `graficos_treinamento/10_erro_por_tempo_real.png`
  e acrescentar uma análise das peças com tempo real acima de 120 s.
- [x] Mostrar os gráficos de tempo real versus previsto e incluir um slide
  de referências centrais.
- [x] Validar e renderizar a nova apresentação de 22 slides; conferir os
  slides alterados e as notas de fontes.

**Versão atual para a defesa:**
`apresentacao/Previsao_tempo_corte_plasma_detalhada_v2.pptx`. As versões
anteriores permanecem na pasta somente como histórico. O relatório da etapa 1
não precisou de alteração nesta revisão.

## Revisão do conteúdo visível nos slides em 30/09/2026

- [x] Manter os 22 slides, gráficos e ordem da apresentação detalhada.
- [x] Ampliar o texto dos quatro slides de estado da arte com pergunta, método,
  resposta ou resultado e relação concreta com o projeto.
- [x] Detalhar o diagnóstico da base, a validação aninhada, o pré processamento,
  o funcionamento dos modelos e a interpretação das métricas.
- [x] Tornar a explicação de acurácia, precisão, recall e F1 visível no slide,
  junto à ressalva sobre o alvo contínuo.
- [x] Conferir a renderização das 22 páginas e inspecionar em tamanho integral
  os slides com mais texto.

**Versão atual após esta revisão:**
`apresentacao/Previsao_tempo_corte_plasma_conteudo_ampliado.pptx`. As versões
anteriores são histórico; este é o arquivo a usar na apresentação.

## Revisão com apresentação de referência em 01/10/2026

- [x] Inspecionar os 24 slides de `exemploSlide.pptx` e a apresentação recente de 9 slides `apresentacao_ml_corte_plasma.pptx`.
- [x] Reorganizar o conteúdo em 24 slides, com contexto, base, geometria, estado da arte, validação, modelos, métricas, resultados, matriz por faixas, limites e referências.
- [x] Conferir números e ressalvas com `Relatório_preenchido.docx`, `resultados/relatorio_treinamento.json` e gráficos do projeto.
- [x] Verificar as fontes externas citadas e incluí-las nas notas dos slides correspondentes.
- [x] Criar capa ilustrativa para corte plasma e salvar o recurso em `apresentacao/assets/plasma_capa.png`.
- [x] Renderizar os 24 slides e conferir visualmente a sequência, especialmente literatura e resultados.

**Versão atual para apresentação:** `apresentacao/Previsao_tempo_corte_plasma_enriquecida_2026_v2.pptx`.
Os arquivos anteriores permanecem como histórico. As notas do apresentador trazem orientações de fala e fontes.

**Ao retomar:** ensaiar a exposição para medir duração e, se necessário, selecionar os slides essenciais. Conferir qualquer alteração futura contra os resultados do treinamento antes de atualizar números.

## Identidade visual própria em 01/10/2026

- [x] Preservar o conteúdo, os gráficos e as notas da versão enriquecida de 24 slides.
- [x] Redesenhar a apresentação com identidade independente do `exemploSlide.pptx`: grafite, laranja industrial, fundo quente, tipografia sem serifa e composições assimétricas.
- [x] Ajustar a capa para mostrar a tocha de plasma e conferir contraste, leitura e renderização das 24 páginas.
- [x] Validar a estrutura do PPTX e confirmar 24 slides com 24 páginas de notas.

**Versão atual para a defesa:** `apresentacao/Previsao_tempo_corte_plasma_identidade_original_v2.pptx`.
As versões anteriores foram preservadas como histórico. Se a apresentação for interrompida, retomar a partir deste arquivo e do relatório final; nenhum dado de treinamento precisou ser alterado nesta revisão visual.

## Resultados finais

- KNN: MAE 17,43 s; RMSE 27,51 s; R² 0,722; 70,46% dos erros até 20 s.
- Regressão múltipla Ridge: MAE 22,91 s; RMSE 32,55 s; R² 0,612.
- Regressão polinomial Ridge: MAE 22,33 s; RMSE 32,96 s; R² 0,602;
  59,86% dos erros até 20 s.
- Segundo modelo escolhido: regressão polinomial. Ela reduziu o MAE em 2,54%
  contra a múltipla e superou o limite de 2% definido antes do teste.
- Ressalva: a regressão múltipla teve RMSE e R² ligeiramente melhores. A escolha
  da polinomial prioriza MAE, métrica principal registrada no método.
- Hiperparâmetros finais: KNN com 7 vizinhos, distância Manhattan e pesos por
  distância (após comparação também com Euclidiana e Chebyshev); polinomial de
  grau 2 com Ridge alpha 100.
- Teste funcional: peça `00.BL.1001`, SAE 1020, 6,4 mm. Tempo registrado no
  dataset: 90 s. Saídas: KNN 89,98 s e polinomial 90,65 s. Este teste confirma o
  fluxo DXF → entradas → modelos, mas não mede generalização, porque os modelos
  finais foram ajustados com todo o dataset. As métricas válidas de generalização
  são as da validação cruzada acima.
