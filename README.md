# V2 — previsão do tempo de corte plasma

Esta pasta é a nova linha do projeto. Ela não usa árvores de decisão, Random
Forest, XGBoost ou modelos híbridos baseados em árvores. As dobras foram
retiradas do escopo desta etapa.

## Objetivo atual

Treinar e comparar modelos de regressão para prever `tempo_corte_plasma_s`:

1. KNN Regressor, solicitado pelo professor.
2. Regressão múltipla Ridge ou regressão polinomial Ridge. A escolha é feita
   com previsões fora da amostra e fica registrada no relatório.

KNN é usado como **regressor** porque o tempo é um valor numérico contínuo.

## Estrutura

- `dados/`: cópia do dataset V10 usada pela V2.
- `src/`: treinamento, previsão e extração geométrica de DXF.
- `modelos/`: os dois modelos finais treinados.
- `resultados/`: métricas e previsões de validação cruzada.
- `pesquisa/`: referências de trabalhos semelhantes.
- `ANDAMENTO.md`: diário e ponto exato para retomada.

## Preparar em outro computador

No PowerShell, dentro da pasta `V2`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Treinar novamente

```powershell
.\.venv\Scripts\python.exe .\src\treinar_modelos_plasma.py
```

O treinamento usa validação aninhada. Linhas com entradas geométricas idênticas
permanecem na mesma dobra, reduzindo o risco de uma peça quase duplicada aparecer
simultaneamente no treino e no teste.

Resultado atual: KNN obteve MAE de 17,43 s e R² de 0,722. A regressão polinomial
foi escolhida como segundo modelo por reduzir em 2,54% o MAE da regressão
múltipla. As métricas completas estão em `resultados/relatorio_treinamento.json`.

## Prever uma peça

Modo direto:

```powershell
.\.venv\Scripts\python.exe .\src\prever_tempo_plasma.py 00.BL.1001 --material "SAE 1020" --espessura 6.4
```

Também é possível executar sem argumentos e responder às perguntas na tela. O
programa mostra os resultados de KNN e regressão separadamente.

## Arquivos transferíveis

Transfira a pasta `V2`, exceto `.venv`. O ambiente virtual não é portátil; ele
deve ser recriado com `requirements.txt` em cada computador.
