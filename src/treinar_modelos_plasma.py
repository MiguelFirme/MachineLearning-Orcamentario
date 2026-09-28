"""Treina dois modelos sem arvores para prever o tempo de corte plasma.

Modelos finais:
1. KNN Regressor.
2. Regressao Ridge multipla ou polinomial, escolhida por validacao aninhada.

Todas as escolhas de hiperparametros acontecem apenas dentro das amostras de
treino. Geometrias identicas ficam na mesma dobra para reduzir vazamento.
"""

from __future__ import annotations

import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, make_scorer
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler


PASTA_RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_DATASET = PASTA_RAIZ / "data" / "dataset_plasma_v10.csv"
PASTA_MODELOS = PASTA_RAIZ / "model"
PASTA_RESULTADOS = PASTA_RAIZ / "resultados"

ALVO = "tempo_corte_plasma_s"
CATEGORICAS = ["material_aco"]
NUMERICAS = [
    "espessura_mm",
    "comprimento_total_mm",
    "largura_total_mm",
    "perimetro_corte_mm",
    "area_mm2",
    "quantidade_furos",
    "peso_liquido_kg",
    "perimetro_externo_mm",
    "perimetro_interno_mm",
    "area_recortes_internos_mm2",
    "quantidade_contornos",
    "quantidade_entidades_dxf",
    "quantidade_linhas_dxf",
    "quantidade_arcos_dxf",
    "quantidade_circulos_dxf",
    "quantidade_splines_dxf",
    "quantidade_segmentos_bulge",
    "comprimento_reto_mm",
    "comprimento_curvo_mm",
    "menor_perimetro_interno_mm",
    "perimetro_interno_medio_mm",
    "recortes_ate_10mm",
    "recortes_ate_25mm",
    "recortes_ate_50mm",
    "razao_perimetro_interno",
    "ocupacao_retangulo",
    "compacidade_externa",
]
FEATURES = CATEGORICAS + NUMERICAS
SEMENTE = 42
METRICAS_DISTANCIA_KNN = ["manhattan", "euclidean", "chebyshev"]


def erro_absoluto_com_trava(y_real, y_previsto):
    """MAE usado na selecao, considerando que tempo previsto nao pode ser negativo."""
    return mean_absolute_error(y_real, np.clip(y_previsto, 0.0, None))


SCORER_MAE = make_scorer(erro_absoluto_com_trava, greater_is_better=False)


def preprocessador_linear():
    numerico = Pipeline([
        ("imputacao", SimpleImputer(strategy="median")),
        ("escala", StandardScaler()),
    ])
    categorico = Pipeline([
        ("imputacao", SimpleImputer(strategy="most_frequent")),
        ("codificacao", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numericas", numerico, NUMERICAS),
        ("categoricas", categorico, CATEGORICAS),
    ])


def preprocessador_polinomial():
    numerico = Pipeline([
        ("imputacao", SimpleImputer(strategy="median")),
        ("escala_entrada", StandardScaler()),
        ("polinomios", PolynomialFeatures(degree=2, include_bias=False)),
        ("escala_saida", StandardScaler()),
    ])
    categorico = Pipeline([
        ("imputacao", SimpleImputer(strategy="most_frequent")),
        ("codificacao", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numericas_polinomiais", numerico, NUMERICAS),
        ("categoricas", categorico, CATEGORICAS),
    ])


def candidatos():
    return {
        "knn": (
            Pipeline([
                ("preprocessamento", preprocessador_linear()),
                ("modelo", KNeighborsRegressor()),
            ]),
            {
                "modelo__n_neighbors": [3, 5, 7, 9, 11, 15, 21, 31],
                "modelo__weights": ["uniform", "distance"],
                "modelo__metric": METRICAS_DISTANCIA_KNN,
            },
        ),
        "regressao_multipla": (
            Pipeline([
                ("preprocessamento", preprocessador_linear()),
                ("modelo", Ridge(solver="lsqr")),
            ]),
            {"modelo__alpha": [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]},
        ),
        "regressao_polinomial": (
            Pipeline([
                ("preprocessamento", preprocessador_polinomial()),
                ("modelo", Ridge(solver="lsqr")),
            ]),
            {"modelo__alpha": [0.1, 1.0, 10.0, 100.0, 1000.0]},
        ),
    }


def metricas(y_real, y_previsto):
    previsto = np.clip(np.asarray(y_previsto, dtype=float), 0.0, None)
    real = np.asarray(y_real, dtype=float)
    erro = np.abs(previsto - real)
    return {
        "mae_s": float(mean_absolute_error(real, previsto)),
        "rmse_s": float(mean_squared_error(real, previsto) ** 0.5),
        "r2": float(r2_score(real, previsto)),
        "erro_p90_s": float(np.percentile(erro, 90)),
        "erro_p95_s": float(np.percentile(erro, 95)),
        "erro_ate_10_s_pct": float((erro <= 10).mean() * 100),
        "erro_ate_20_s_pct": float((erro <= 20).mean() * 100),
        "erro_ate_30_s_pct": float((erro <= 30).mean() * 100),
    }


def parametros_serializaveis(parametros):
    return {chave: valor.item() if isinstance(valor, np.generic) else valor for chave, valor in parametros.items()}


def carregar_dados():
    df = pd.read_csv(CAMINHO_DATASET, sep=";", decimal=",", encoding="utf-8-sig")
    obrigatorias = ["codigo_peca", ALVO, "status_fontes_v10", *FEATURES]
    ausentes = [coluna for coluna in obrigatorias if coluna not in df.columns]
    if ausentes:
        raise ValueError("Colunas obrigatorias ausentes: " + ", ".join(ausentes))

    mascara = (
        df[ALVO].notna()
        & df[FEATURES].notna().all(axis=1)
        & df["status_fontes_v10"].eq("ok")
    )
    plasma = df.loc[mascara, ["codigo_peca", ALVO, *FEATURES]].reset_index(drop=True)
    if len(plasma) < 100:
        raise ValueError(f"Somente {len(plasma)} linhas validas; treinamento interrompido.")

    # Pecas com todas as entradas iguais devem permanecer na mesma dobra.
    grupos = pd.util.hash_pandas_object(plasma[FEATURES], index=False).to_numpy()
    return df, plasma, grupos


def avaliar_aninhado(X, y, grupos):
    modelos = candidatos()
    previsoes = {nome: np.zeros(len(X), dtype=float) for nome in modelos}
    parametros = {nome: [] for nome in modelos}
    maes_por_dobra = {nome: [] for nome in modelos}
    maes_internos_por_metrica_knn = {metrica: [] for metrica in METRICAS_DISTANCIA_KNN}

    externa = GroupKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    for numero, (treino, teste) in enumerate(externa.split(X, y, grupos), start=1):
        interna = GroupKFold(n_splits=4, shuffle=True, random_state=SEMENTE + numero)
        for nome, (pipeline, grade) in modelos.items():
            busca = GridSearchCV(
                pipeline,
                grade,
                scoring=SCORER_MAE,
                cv=interna,
                n_jobs=-1,
                refit=True,
            )
            busca.fit(X.iloc[treino], y[treino], groups=grupos[treino])
            if nome == "knn":
                metricas_avaliadas = np.asarray(
                    busca.cv_results_["param_modelo__metric"], dtype=str
                )
                scores_medios = np.asarray(busca.cv_results_["mean_test_score"], dtype=float)
                for metrica in METRICAS_DISTANCIA_KNN:
                    melhor_score = scores_medios[metricas_avaliadas == metrica].max()
                    maes_internos_por_metrica_knn[metrica].append(float(-melhor_score))
            previsto = np.clip(busca.predict(X.iloc[teste]), 0.0, None)
            previsoes[nome][teste] = previsto
            parametros[nome].append(parametros_serializaveis(busca.best_params_))
            maes_por_dobra[nome].append(float(mean_absolute_error(y[teste], previsto)))
            print(
                f"Dobra {numero}/5 | {nome}: "
                f"MAE={maes_por_dobra[nome][-1]:.2f}s | {busca.best_params_}"
            )

    resumo = {}
    for nome in modelos:
        resumo[nome] = {
            **metricas(y, previsoes[nome]),
            "mae_medio_dobras_s": float(np.mean(maes_por_dobra[nome])),
            "mae_desvio_dobras_s": float(np.std(maes_por_dobra[nome], ddof=1)),
            "melhores_parametros_por_dobra": parametros[nome],
        }
    resumo["knn"]["comparacao_metricas_distancia_validacao_interna"] = {
        metrica: {
            "mae_por_dobra_s": valores,
            "mae_medio_s": float(np.mean(valores)),
        }
        for metrica, valores in maes_internos_por_metrica_knn.items()
    }
    return previsoes, resumo


def escolher_regressao(resumo):
    mae_multipla = resumo["regressao_multipla"]["mae_s"]
    mae_polinomial = resumo["regressao_polinomial"]["mae_s"]
    ganho_relativo = (mae_multipla - mae_polinomial) / mae_multipla

    # A polinomial e bem mais complexa. Ela so vence se melhorar pelo menos 2%.
    if mae_polinomial < mae_multipla and ganho_relativo >= 0.02:
        return "regressao_polinomial", float(ganho_relativo * 100)
    return "regressao_multipla", float(ganho_relativo * 100)


def treinar_final(nome, X, y, grupos):
    pipeline, grade = candidatos()[nome]
    validacao = GroupKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    busca = GridSearchCV(
        pipeline,
        grade,
        scoring=SCORER_MAE,
        cv=validacao,
        n_jobs=-1,
        refit=True,
    )
    busca.fit(X, y, groups=grupos)
    return busca.best_estimator_, parametros_serializaveis(busca.best_params_)


def main():
    PASTA_MODELOS.mkdir(parents=True, exist_ok=True)
    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    df, plasma, grupos = carregar_dados()
    X = plasma[FEATURES]
    y = plasma[ALVO].to_numpy(dtype=float)

    print(f"Dataset completo: {df.shape[0]} linhas x {df.shape[1]} colunas")
    print(f"Pecas validas para plasma: {len(plasma)}")
    print(f"Grupos geometricos distintos: {len(np.unique(grupos))}")
    print("Iniciando validacao aninhada sem arvores...")

    previsoes, resumo = avaliar_aninhado(X, y, grupos)
    regressao_escolhida, ganho_pct = escolher_regressao(resumo)

    print(f"\nRegressao escolhida: {regressao_escolhida}")
    print(f"Ganho polinomial contra multipla: {ganho_pct:+.2f}%")
    print("Treinando os dois modelos finais em todas as pecas validas...")

    modelo_knn, parametros_knn = treinar_final("knn", X, y, grupos)
    modelo_regressao, parametros_regressao = treinar_final(regressao_escolhida, X, y, grupos)

    criado_em = datetime.now(timezone.utc).isoformat()
    metadados_base = {
        "alvo": ALVO,
        "features": FEATURES,
        "dataset": CAMINHO_DATASET.name,
        "quantidade_pecas": len(plasma),
        "criado_em_utc": criado_em,
        "python": platform.python_version(),
        "scikit_learn": sklearn.__version__,
    }
    joblib.dump(
        {
            "nome": "knn",
            "modelo": modelo_knn,
            "parametros": parametros_knn,
            "metricas_validacao": resumo["knn"],
            **metadados_base,
        },
        PASTA_MODELOS / "modelo_knn_plasma.joblib",
    )
    joblib.dump(
        {
            "nome": regressao_escolhida,
            "modelo": modelo_regressao,
            "parametros": parametros_regressao,
            "metricas_validacao": resumo[regressao_escolhida],
            **metadados_base,
        },
        PASTA_MODELOS / "modelo_regressao_plasma.joblib",
    )

    analise = plasma[["codigo_peca", ALVO]].copy()
    for nome, previsto in previsoes.items():
        analise[f"previsao_{nome}_s"] = previsto
        analise[f"erro_absoluto_{nome}_s"] = np.abs(previsto - y)
    analise.to_csv(
        PASTA_RESULTADOS / "previsoes_validacao_cruzada.csv",
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        index=False,
    )

    relatorio = {
        "status": "concluido",
        "dataset": {
            "arquivo": str(CAMINHO_DATASET.relative_to(PASTA_RAIZ)),
            "linhas_totais": int(len(df)),
            "linhas_validas_plasma": int(len(plasma)),
            "grupos_geometricos_distintos": int(len(np.unique(grupos))),
            "tempo_minimo_s": float(y.min()),
            "tempo_mediano_s": float(np.median(y)),
            "tempo_maximo_s": float(y.max()),
        },
        "metodologia": {
            "validacao_externa": "GroupKFold 5 dobras",
            "validacao_interna": "GroupKFold 4 dobras",
            "criterio_ajuste": "menor MAE",
            "metricas_distancia_knn_testadas": METRICAS_DISTANCIA_KNN,
            "agrupamento": "linhas com entradas identicas permanecem na mesma dobra",
            "regra_escolha_regressao": (
                "polinomial apenas se reduzir o MAE fora da amostra em pelo menos 2%; "
                "caso contrario, multipla"
            ),
        },
        "comparacao": resumo,
        "decisao": {
            "modelo_1": "knn",
            "modelo_2": regressao_escolhida,
            "ganho_polinomial_contra_multipla_pct": ganho_pct,
            "parametros_finais_knn": parametros_knn,
            "parametros_finais_regressao": parametros_regressao,
        },
        "ambiente": metadados_base,
    }
    (PASTA_RESULTADOS / "relatorio_treinamento.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nResumo fora da amostra:")
    for nome, valores in resumo.items():
        print(
            f"{nome:22s} MAE={valores['mae_s']:.2f}s | "
            f"RMSE={valores['rmse_s']:.2f}s | R2={valores['r2']:.3f}"
        )
    print(f"\nModelos salvos em: {PASTA_MODELOS}")
    print(f"Relatorio salvo em: {PASTA_RESULTADOS / 'relatorio_treinamento.json'}")


if __name__ == "__main__":
    main()

