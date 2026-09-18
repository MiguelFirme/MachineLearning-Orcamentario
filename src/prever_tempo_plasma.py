"""Prevê o tempo de corte plasma com os dois modelos finais da V2."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import joblib
import pandas as pd

from extract_dxf_geometry import extract_geometry


PASTA_V2 = Path(__file__).resolve().parents[1]
PASTA_PROJETO = PASTA_V2.parent
PASTA_DXFS = PASTA_PROJETO / "PEÇAS" / "DXFs"
CAMINHO_KNN = PASTA_V2 / "modelos" / "modelo_knn_plasma.joblib"
CAMINHO_REGRESSAO = PASTA_V2 / "modelos" / "modelo_regressao_plasma.joblib"
DENSIDADE_ACO_KG_MM3 = 7.85e-6

MAPA_DXF_MODELO = {
    "perimetro_externo_mm": "outer_perimeter",
    "perimetro_interno_mm": "inner_perimeter",
    "area_recortes_internos_mm2": "inner_area",
    "quantidade_contornos": "contour_count",
    "quantidade_entidades_dxf": "entity_count",
    "quantidade_linhas_dxf": "line_entity_count",
    "quantidade_arcos_dxf": "arc_entity_count",
    "quantidade_circulos_dxf": "circle_entity_count",
    "quantidade_splines_dxf": "spline_entity_count",
    "quantidade_segmentos_bulge": "bulge_segment_count",
    "comprimento_reto_mm": "straight_length",
    "comprimento_curvo_mm": "curved_length",
    "menor_perimetro_interno_mm": "min_inner_perimeter",
    "perimetro_interno_medio_mm": "mean_inner_perimeter",
    "recortes_ate_10mm": "small_contour_count_10mm",
    "recortes_ate_25mm": "small_contour_count_25mm",
    "recortes_ate_50mm": "small_contour_count_50mm",
    "razao_perimetro_interno": "inner_perimeter_ratio",
    "ocupacao_retangulo": "bbox_occupancy",
    "compacidade_externa": "outer_compactness",
}


def chave_codigo(texto):
    return re.sub(r"[^A-Z0-9]", "", str(texto).upper())


def localizar_dxf(texto):
    informado = Path(texto.strip().strip('"').strip("'"))
    candidatos = [informado]
    if not informado.is_absolute():
        candidatos.extend([Path.cwd() / informado, PASTA_PROJETO / informado])
    for candidato in candidatos:
        if candidato.is_file() and candidato.suffix.lower() == ".dxf":
            return candidato.resolve()

    # Codigos como 00.BL.1001 possuem pontos, mas nao sao extensoes de arquivo.
    nome_codigo = informado.stem if informado.suffix.lower() == ".dxf" else informado.name
    codigo = chave_codigo(nome_codigo)
    encontrados = [
        arquivo for arquivo in PASTA_DXFS.rglob("*")
        if arquivo.suffix.lower() == ".dxf" and chave_codigo(arquivo.stem) == codigo
    ] if PASTA_DXFS.is_dir() else []
    if len(encontrados) == 1:
        return encontrados[0].resolve()
    if len(encontrados) > 1:
        nomes = "\n".join(f"- {arquivo}" for arquivo in encontrados)
        raise ValueError(f"Mais de um DXF corresponde ao codigo informado:\n{nomes}")
    raise FileNotFoundError(f"DXF nao encontrado: {texto}")


def montar_entrada(material, espessura, geometria, features):
    comprimento = max(geometria["width"], geometria["height"])
    largura = min(geometria["width"], geometria["height"])
    area = geometria["area"]
    dados = {
        "material_aco": material,
        "espessura_mm": espessura,
        "comprimento_total_mm": comprimento,
        "largura_total_mm": largura,
        "perimetro_corte_mm": geometria["perimeter"],
        "area_mm2": area,
        "quantidade_furos": geometria["hole_count"],
        "peso_liquido_kg": area * espessura * DENSIDADE_ACO_KG_MM3,
    }
    for coluna, chave in MAPA_DXF_MODELO.items():
        dados[coluna] = geometria[chave]

    faltantes = [coluna for coluna in features if coluna not in dados]
    if faltantes:
        raise ValueError("Entradas nao calculadas: " + ", ".join(faltantes))
    return pd.DataFrame([{coluna: dados[coluna] for coluna in features}]), dados


def argumentos():
    parser = argparse.ArgumentParser(
        description="Prevê o tempo de corte plasma com KNN e regressao polinomial."
    )
    parser.add_argument("dxf", nargs="?", help="caminho do DXF ou codigo da peca")
    parser.add_argument("--material", help='ex.: "SAE 1020"')
    parser.add_argument("--espessura", type=float, help="espessura da chapa em mm")
    return parser.parse_args()


def main():
    args = argumentos()
    texto_dxf = args.dxf or input("Caminho do DXF ou codigo da peca: ").strip()
    material = args.material or input("Material do aco (ex.: SAE 1020): ").strip()
    espessura = args.espessura
    if espessura is None:
        espessura = float(input("Espessura em mm: ").strip().replace(",", "."))
    if not material:
        raise ValueError("O material deve ser informado.")
    if espessura <= 0:
        raise ValueError("A espessura deve ser positiva.")

    for caminho in [CAMINHO_KNN, CAMINHO_REGRESSAO]:
        if not caminho.is_file():
            raise FileNotFoundError(
                f"Modelo nao encontrado: {caminho}. Execute primeiro o treinamento."
            )

    caminho_dxf = localizar_dxf(texto_dxf)
    geometria = extract_geometry(caminho_dxf)
    if geometria["status"] != "ok":
        raise ValueError(
            "O DXF nao possui contornos fechados validos para gerar as entradas."
        )

    pacote_knn = joblib.load(CAMINHO_KNN)
    pacote_regressao = joblib.load(CAMINHO_REGRESSAO)
    if pacote_knn["features"] != pacote_regressao["features"]:
        raise ValueError("Os dois modelos foram treinados com entradas diferentes.")

    entrada, dados = montar_entrada(
        material, espessura, geometria, pacote_knn["features"]
    )
    previsao_knn = max(0.0, float(pacote_knn["modelo"].predict(entrada)[0]))
    previsao_regressao = max(
        0.0, float(pacote_regressao["modelo"].predict(entrada)[0])
    )

    print("\nDADOS DA PECA")
    print(f"Arquivo:             {caminho_dxf.name}")
    print(f"Material:            {material}")
    print(f"Espessura:           {espessura:.2f} mm")
    print(f"Perimetro de corte:  {dados['perimetro_corte_mm']:.2f} mm")
    print(f"Area liquida:        {dados['area_mm2']:.2f} mm2")
    print(f"Furos internos:      {int(dados['quantidade_furos'])}")
    print("\nPREVISOES DO TEMPO DE CORTE PLASMA")
    print(f"KNN:                 {previsao_knn:.2f} s")
    print(
        f"{pacote_regressao['nome'].replace('_', ' ').title()}: "
        f"{previsao_regressao:.2f} s"
    )
    print(f"Diferenca modelos:   {abs(previsao_knn - previsao_regressao):.2f} s")
    print("\nOs dois resultados sao exibidos separadamente; nao ha media automatica.")


if __name__ == "__main__":
    main()
