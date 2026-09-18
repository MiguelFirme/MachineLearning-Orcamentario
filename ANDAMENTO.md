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

## Próximo passo ao retomar

Revisar com o professor a escolha das métricas e decidir se o relatório final
deve priorizar MAE (mantendo a polinomial) ou RMSE/R² (o que favorece a múltipla).

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
  distância; polinomial de grau 2 com Ridge alpha 100.
- Teste funcional: peça `00.BL.1001`, SAE 1020, 6,4 mm. Tempo registrado no
  dataset: 90 s. Saídas: KNN 89,98 s e polinomial 90,65 s. Este teste confirma o
  fluxo DXF → entradas → modelos, mas não mede generalização, porque os modelos
  finais foram ajustados com todo o dataset. As métricas válidas de generalização
  são as da validação cruzada acima.
