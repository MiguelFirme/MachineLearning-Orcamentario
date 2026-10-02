"""Gera os gráficos de diagnóstico e comparação dos modelos de plasma."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_DATASET = RAIZ / "data" / "dataset_plasma_v10.csv"
CAMINHO_PREVISOES = RAIZ / "resultados" / "previsoes_validacao_cruzada.csv"
CAMINHO_RELATORIO = RAIZ / "resultados" / "relatorio_treinamento.json"
PASTA_SAIDA = RAIZ / "graficos_treinamento"

CORES = {
    "KNN": "#1f4e79",
    "Regressão múltipla": "#6b7280",
    "Regressão polinomial": "#d97706",
}


def configurar_estilo():
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#9ca3af",
            "axes.labelcolor": "#111827",
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "font.size": 10,
            "grid.color": "#e5e7eb",
            "grid.linewidth": 0.8,
        }
    )


def salvar(figura, nome):
    figura.tight_layout()
    figura.savefig(PASTA_SAIDA / nome, dpi=300, bbox_inches="tight")
    plt.close(figura)


def grafico_distribuicao(dataset, features):
    mascara = (
        dataset["tempo_corte_plasma_s"].notna()
        & dataset[features].notna().all(axis=1)
        & dataset["status_fontes_v10"].eq("ok")
    )
    tempos = dataset.loc[mascara, "tempo_corte_plasma_s"]
    figura, eixo = plt.subplots(figsize=(8.2, 4.8))
    eixo.hist(tempos, bins=24, color="#1f4e79", edgecolor="white", alpha=0.9)
    eixo.axvline(tempos.median(), color="#d97706", linestyle="--", linewidth=2,
                 label=f"Mediana: {tempos.median():.0f} s")
    eixo.set_title("Distribuição do tempo real de corte plasma")
    eixo.set_xlabel("Tempo de corte (s)")
    eixo.set_ylabel("Quantidade de peças")
    eixo.grid(axis="y")
    eixo.legend(frameon=False)
    salvar(figura, "01_distribuicao_tempo_real.png")


def grafico_metricas(relatorio):
    nomes = ["KNN", "Regressão múltipla", "Regressão polinomial"]
    chaves = ["knn", "regressao_multipla", "regressao_polinomial"]
    comparacao = relatorio["comparacao"]
    metricas = [
        ("MAE (s)", "mae_s", "Menor é melhor"),
        ("RMSE (s)", "rmse_s", "Menor é melhor"),
        ("R²", "r2", "Maior é melhor"),
    ]
    figura, eixos = plt.subplots(1, 3, figsize=(12.2, 4.5))
    cores = [CORES[nome] for nome in nomes]
    for eixo, (titulo, metrica, subtitulo) in zip(eixos, metricas):
        valores = [comparacao[chave][metrica] for chave in chaves]
        barras = eixo.bar(range(3), valores, color=cores, width=0.68)
        eixo.set_title(titulo)
        eixo.set_xlabel(subtitulo)
        eixo.set_xticks(range(3), ["KNN", "Ridge\nmúltipla", "Ridge\npolinomial"])
        eixo.grid(axis="y")
        margem = max(valores) * 0.12
        eixo.set_ylim(0, max(valores) + margem)
        formato = "{:.3f}" if metrica == "r2" else "{:.2f}"
        eixo.bar_label(barras, labels=[formato.format(v) for v in valores], padding=3)
    figura.suptitle("Desempenho fora da amostra por modelo", fontsize=15, fontweight="bold")
    salvar(figura, "02_comparacao_metricas_modelos.png")


def grafico_real_previsto(previsoes, coluna, titulo, cor, nome_arquivo):
    real = previsoes["tempo_corte_plasma_s"].to_numpy(dtype=float)
    previsto = previsoes[coluna].to_numpy(dtype=float)
    limite = float(max(real.max(), previsto.max()))
    figura, eixo = plt.subplots(figsize=(6.2, 5.4))
    eixo.scatter(real, previsto, s=18, alpha=0.42, color=cor, edgecolors="none")
    eixo.plot([0, limite], [0, limite], color="#111827", linestyle="--", linewidth=1.4,
              label="Previsão perfeita")
    eixo.set_xlim(0, limite * 1.03)
    eixo.set_ylim(0, limite * 1.03)
    eixo.set_title(titulo)
    eixo.set_xlabel("Tempo real (s)")
    eixo.set_ylabel("Tempo previsto (s)")
    eixo.grid()
    eixo.legend(frameon=False)
    salvar(figura, nome_arquivo)


def grafico_erros(previsoes):
    colunas = [
        "erro_absoluto_knn_s",
        "erro_absoluto_regressao_multipla_s",
        "erro_absoluto_regressao_polinomial_s",
    ]
    nomes = ["KNN", "Ridge múltipla", "Ridge polinomial"]
    valores = [previsoes[coluna].to_numpy(dtype=float) for coluna in colunas]
    figura, eixo = plt.subplots(figsize=(8.2, 4.8))
    caixas = eixo.boxplot(valores, tick_labels=nomes, patch_artist=True, showfliers=False)
    for caixa, cor in zip(caixas["boxes"], CORES.values()):
        caixa.set_facecolor(cor)
        caixa.set_alpha(0.82)
    eixo.set_title("Distribuição dos erros absolutos fora da amostra")
    eixo.set_ylabel("Erro absoluto (s)")
    eixo.grid(axis="y")
    salvar(figura, "06_distribuicao_erros_absolutos.png")


def grafico_distancias(relatorio):
    dados = relatorio["comparacao"]["knn"]["comparacao_metricas_distancia_validacao_interna"]
    nomes = ["Manhattan", "Euclidiana", "Chebyshev"]
    chaves = ["manhattan", "euclidean", "chebyshev"]
    valores = [dados[chave]["mae_medio_s"] for chave in chaves]
    figura, eixo = plt.subplots(figsize=(7.4, 4.6))
    barras = eixo.bar(nomes, valores, color=["#1f4e79", "#6b7280", "#d97706"], width=0.62)
    eixo.set_title("Comparação das distâncias do KNN")
    eixo.set_ylabel("Melhor MAE interno médio (s)")
    eixo.set_ylim(0, max(valores) * 1.18)
    eixo.grid(axis="y")
    eixo.bar_label(barras, labels=[f"{valor:.2f}" for valor in valores], padding=4)
    salvar(figura, "07_comparacao_distancias_knn.png")


def grafico_faixas_erro(relatorio):
    nomes = ["KNN", "Ridge múltipla", "Ridge polinomial"]
    chaves = ["knn", "regressao_multipla", "regressao_polinomial"]
    faixas = [("Até 10 s", "erro_ate_10_s_pct"), ("Até 20 s", "erro_ate_20_s_pct"),
              ("Até 30 s", "erro_ate_30_s_pct")]
    x = np.arange(len(nomes))
    largura = 0.24
    figura, eixo = plt.subplots(figsize=(8.6, 4.9))
    for indice, (rotulo, chave_metrica) in enumerate(faixas):
        valores = [relatorio["comparacao"][chave][chave_metrica] for chave in chaves]
        eixo.bar(x + (indice - 1) * largura, valores, largura, label=rotulo)
    eixo.set_title("Percentual de previsões por faixa de erro")
    eixo.set_ylabel("Previsões dentro da faixa (%)")
    eixo.set_xticks(x, nomes)
    eixo.set_ylim(0, 100)
    eixo.grid(axis="y")
    eixo.legend(frameon=False, ncols=3, loc="upper center")
    salvar(figura, "08_faixas_de_erro_modelos.png")


def grafico_matriz_faixas_tempo(previsoes):
    """Mostra a migração entre faixas de tempo, sem tratar regressão como classificação."""
    limites = [-np.inf, 30, 60, 120, np.inf]
    rotulos = ["≤30", "30–60", "60–120", ">120"]
    real = pd.cut(previsoes["tempo_corte_plasma_s"], limites, labels=rotulos).to_numpy()
    modelos = [
        ("KNN", "previsao_knn_s"),
        ("Ridge polinomial", "previsao_regressao_polinomial_s"),
    ]
    figura, eixos = plt.subplots(1, 2, figsize=(10.7, 4.5), sharey=True)
    for eixo, (nome, coluna) in zip(eixos, modelos):
        previsto = pd.cut(previsoes[coluna], limites, labels=rotulos).to_numpy()
        matriz = np.array([[np.sum((real == r) & (previsto == p))
                            for p in rotulos] for r in rotulos])
        proporcao = 100 * matriz / matriz.sum(axis=1, keepdims=True)
        imagem = eixo.imshow(proporcao, vmin=0, vmax=100, cmap="Blues")
        eixo.set_title(nome)
        eixo.set_xlabel("Faixa prevista (s)")
        eixo.set_xticks(range(4), rotulos)
        eixo.set_yticks(range(4), rotulos)
        for linha in range(4):
            for coluna_idx in range(4):
                valor = proporcao[linha, coluna_idx]
                eixo.text(coluna_idx, linha, f"{matriz[linha, coluna_idx]}\n({valor:.0f}%)",
                          ha="center", va="center", fontsize=9,
                          color="white" if valor > 55 else "#111827")
    eixos[0].set_ylabel("Faixa real (s)")
    escala = figura.add_axes([0.915, 0.22, 0.018, 0.52])
    figura.colorbar(imagem, cax=escala, label="% da faixa real")
    figura.suptitle("Matriz diagnóstica por faixas de tempo", fontsize=14, fontweight="bold")
    figura.subplots_adjust(left=0.08, right=0.87, top=0.83, bottom=0.14, wspace=0.20)
    figura.savefig(PASTA_SAIDA / "09_matriz_faixas_tempo.png", dpi=300, bbox_inches="tight")
    plt.close(figura)


def grafico_erro_por_tempo_real(previsoes):
    """Compara o MAE dos dois modelos finais em faixas definidas pelo tempo real."""
    faixas = pd.cut(previsoes["tempo_corte_plasma_s"],
                    [-np.inf, 30, 60, 120, np.inf],
                    labels=["Até 30 s", "30–60 s", "60–120 s", "Acima de 120 s"])
    dados = previsoes.assign(faixa=faixas).groupby("faixa", observed=True).agg(
        n=("tempo_corte_plasma_s", "size"),
        knn=("erro_absoluto_knn_s", "mean"),
        ridge=("erro_absoluto_regressao_polinomial_s", "mean"),
    )
    x = np.arange(len(dados))
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    largura = 0.34
    a = ax.bar(x - largura / 2, dados["knn"], largura, color=CORES["KNN"], label="KNN")
    b = ax.bar(x + largura / 2, dados["ridge"], largura,
               color=CORES["Regressão polinomial"], label="Ridge polinomial")
    ax.bar_label(a, fmt="%.1f", padding=3)
    ax.bar_label(b, fmt="%.1f", padding=3)
    ax.set_xticks(x, [f"{faixa}\n(n={n})" for faixa, n in zip(dados.index, dados["n"])])
    ax.set_ylim(0, max(dados["ridge"]) * 1.2)
    ax.set_ylabel("Erro absoluto médio (s)")
    ax.set_title("Erro por faixa de tempo real")
    ax.grid(axis="y")
    ax.legend(frameon=False)
    salvar(fig, "10_erro_por_tempo_real.png")


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    configurar_estilo()
    dataset = pd.read_csv(CAMINHO_DATASET, sep=";", decimal=",", encoding="utf-8-sig")
    previsoes = pd.read_csv(CAMINHO_PREVISOES, sep=";", decimal=",", encoding="utf-8-sig")
    relatorio = json.loads(CAMINHO_RELATORIO.read_text(encoding="utf-8"))

    grafico_distribuicao(dataset, relatorio["ambiente"]["features"])
    grafico_metricas(relatorio)
    grafico_real_previsto(previsoes, "previsao_knn_s", "KNN: tempo real e previsto",
                          CORES["KNN"], "03_real_vs_previsto_knn.png")
    grafico_real_previsto(
        previsoes,
        "previsao_regressao_multipla_s",
        "Regressão Ridge múltipla: tempo real e previsto",
        CORES["Regressão múltipla"],
        "04_real_vs_previsto_regressao_multipla.png",
    )
    grafico_real_previsto(
        previsoes,
        "previsao_regressao_polinomial_s",
        "Regressão Ridge polinomial: tempo real e previsto",
        CORES["Regressão polinomial"],
        "05_real_vs_previsto_regressao_polinomial.png",
    )
    grafico_erros(previsoes)
    grafico_distancias(relatorio)
    grafico_faixas_erro(relatorio)
    grafico_matriz_faixas_tempo(previsoes)
    grafico_erro_por_tempo_real(previsoes)
    print(f"Gráficos salvos em: {PASTA_SAIDA}")


if __name__ == "__main__":
    main()
