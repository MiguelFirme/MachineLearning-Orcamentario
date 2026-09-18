from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import math


Point = tuple[float, float]


@dataclass
class Curve:
    points: list[Point]
    kind: str
    closed: bool = False

    @property
    def length(self) -> float:
        return sum(math.dist(a, b) for a, b in zip(self.points, self.points[1:]))


def dxf_pairs(path: Path):
    lines = path.read_text(encoding="cp1252", errors="replace").splitlines()
    return [(lines[i].strip(), lines[i + 1].strip()) for i in range(0, len(lines) - 1, 2)]


def dxf_entities(path: Path):
    pairs = dxf_pairs(path)
    section = None
    entities = []
    current = None
    for i, (code, value) in enumerate(pairs):
        if code == "0" and value == "SECTION" and i + 1 < len(pairs):
            section = pairs[i + 1][1] if pairs[i + 1][0] == "2" else None
        elif code == "0" and value == "ENDSEC":
            if current:
                entities.append(current)
                current = None
            section = None
        elif section == "ENTITIES" and code == "0":
            if current:
                entities.append(current)
            current = {"type": value, "groups": []}
        elif section == "ENTITIES" and current:
            current["groups"].append((code, value))
    if current:
        entities.append(current)
    return entities


def first(groups, code, default=None):
    for c, value in groups:
        if c == str(code):
            return value
    return default


def floats(groups, code):
    result = []
    for c, value in groups:
        if c == str(code):
            try:
                result.append(float(value))
            except ValueError:
                pass
    return result


def paired_points(groups, xcode, ycode):
    points = []
    pending_x = None
    for code, value in groups:
        if code == str(xcode):
            try:
                pending_x = float(value)
            except ValueError:
                pending_x = None
        elif code == str(ycode) and pending_x is not None:
            try:
                points.append((pending_x, float(value)))
            except ValueError:
                pass
            pending_x = None
    return points


def sample_arc(center, radius, start_deg, end_deg, max_step_deg=2.0):
    sweep = (end_deg - start_deg) % 360.0
    if sweep == 0:
        sweep = 360.0
    steps = max(2, math.ceil(abs(sweep) / max_step_deg))
    return [
        (
            center[0] + radius * math.cos(math.radians(start_deg + sweep * i / steps)),
            center[1] + radius * math.sin(math.radians(start_deg + sweep * i / steps)),
        )
        for i in range(steps + 1)
    ]


def sample_bulge(p1, p2, bulge, max_step_deg=2.0):
    if abs(bulge) < 1e-12:
        return [p1, p2]
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    chord = math.hypot(dx, dy)
    if chord == 0:
        return [p1, p2]
    theta = 4.0 * math.atan(bulge)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    nx, ny = -dy / chord, dx / chord
    offset = chord * (1.0 - bulge * bulge) / (4.0 * bulge)
    cx, cy = mx + nx * offset, my + ny * offset
    radius = math.dist((cx, cy), p1)
    start = math.atan2(p1[1] - cy, p1[0] - cx)
    steps = max(2, math.ceil(abs(math.degrees(theta)) / max_step_deg))
    return [
        (cx + radius * math.cos(start + theta * i / steps), cy + radius * math.sin(start + theta * i / steps))
        for i in range(steps + 1)
    ]


def de_boor(u, degree, knots, control, weights=None):
    n = len(control) - 1
    if u >= knots[n + 1]:
        return control[-1]
    k = degree
    while k < n + 1 and not (knots[k] <= u < knots[k + 1]):
        k += 1
    if k > n:
        k = n
    if weights and len(weights) == len(control):
        d = [[control[j][0] * weights[j], control[j][1] * weights[j], weights[j]] for j in range(k - degree, k + 1)]
    else:
        d = [[control[j][0], control[j][1], 1.0] for j in range(k - degree, k + 1)]
    for r in range(1, degree + 1):
        for j in range(degree, r - 1, -1):
            i = k - degree + j
            denominator = knots[i + degree - r + 1] - knots[i]
            alpha = 0.0 if denominator == 0 else (u - knots[i]) / denominator
            d[j] = [(1 - alpha) * d[j - 1][q] + alpha * d[j][q] for q in range(3)]
    xw, yw, w = d[degree]
    return (xw / w, yw / w) if w else (xw, yw)


def entity_to_curve(entity):
    kind = entity["type"]
    g = entity["groups"]
    try:
        if kind == "LINE":
            return Curve([
                (float(first(g, 10)), float(first(g, 20))),
                (float(first(g, 11)), float(first(g, 21))),
            ], kind)
        if kind == "CIRCLE":
            center = (float(first(g, 10)), float(first(g, 20)))
            radius = float(first(g, 40))
            points = sample_arc(center, radius, 0, 360)
            points[-1] = points[0]
            return Curve(points, kind, True)
        if kind == "ARC":
            center = (float(first(g, 10)), float(first(g, 20)))
            return Curve(sample_arc(center, float(first(g, 40)), float(first(g, 50)), float(first(g, 51))), kind)
        if kind == "ELLIPSE":
            center = (float(first(g, 10)), float(first(g, 20)))
            major = (float(first(g, 11)), float(first(g, 21)))
            ratio = float(first(g, 40))
            start = float(first(g, 41, 0.0))
            end = float(first(g, 42, 2 * math.pi))
            delta = end - start
            while delta <= 0:
                delta += 2 * math.pi
            closed = abs(delta - 2 * math.pi) < 1e-5
            major_len = math.hypot(*major)
            ux, uy = major[0] / major_len, major[1] / major_len
            vx, vy = -uy * major_len * ratio, ux * major_len * ratio
            steps = max(18, math.ceil(abs(math.degrees(delta)) / 2.0))
            points = [
                (center[0] + major[0] * math.cos(start + delta * i / steps) + vx * math.sin(start + delta * i / steps),
                 center[1] + major[1] * math.cos(start + delta * i / steps) + vy * math.sin(start + delta * i / steps))
                for i in range(steps + 1)
            ]
            if closed:
                points[-1] = points[0]
            return Curve(points, kind, closed)
        if kind == "LWPOLYLINE":
            vertices = []
            current = None
            for code, value in g:
                if code == "10":
                    if current is not None:
                        vertices.append(current)
                    current = [float(value), None, 0.0]
                elif code == "20" and current is not None:
                    current[1] = float(value)
                elif code == "42" and current is not None:
                    current[2] = float(value)
            if current is not None:
                vertices.append(current)
            vertices = [v for v in vertices if v[1] is not None]
            closed = int(first(g, 70, 0)) & 1 == 1
            points = []
            count = len(vertices) if closed else len(vertices) - 1
            for i in range(count):
                a = vertices[i]
                b = vertices[(i + 1) % len(vertices)]
                segment = sample_bulge((a[0], a[1]), (b[0], b[1]), a[2])
                points.extend(segment if not points else segment[1:])
            if closed and points:
                points[-1] = points[0]
            return Curve(points, kind, closed)
        if kind == "SPLINE":
            control = paired_points(g, 10, 20)
            fit = paired_points(g, 11, 21)
            flags = int(first(g, 70, 0))
            closed = flags & 1 == 1
            degree = int(first(g, 71, 3))
            knots = floats(g, 40)
            weights = floats(g, 41)
            if control and len(knots) >= len(control) + degree + 1:
                start, end = knots[degree], knots[len(control)]
                steps = max(40, len(control) * 20)
                points = [de_boor(start + (end - start) * i / steps, degree, knots, control, weights) for i in range(steps + 1)]
            elif len(fit) >= 2:
                points = fit
            else:
                points = control
            if closed and points:
                if math.dist(points[0], points[-1]) > 1e-6:
                    points.append(points[0])
                else:
                    points[-1] = points[0]
            return Curve(points, kind, closed)
    except (TypeError, ValueError, ZeroDivisionError, IndexError):
        return None
    return None


def point_key(point, tolerance=1e-2):
    return (round(point[0] / tolerance), round(point[1] / tolerance))


def closed_contours(curves):
    contours = [curve for curve in curves if curve.closed and len(curve.points) >= 4]
    open_curves = [curve for curve in curves if not curve.closed and len(curve.points) >= 2]
    endpoint_map = {}
    for index, curve in enumerate(open_curves):
        for endpoint in (curve.points[0], curve.points[-1]):
            endpoint_map.setdefault(point_key(endpoint), []).append(index)
    unused = set(range(len(open_curves)))
    while unused:
        seed = next(iter(unused))
        component = set()
        stack = [seed]
        while stack:
            index = stack.pop()
            if index in component:
                continue
            component.add(index)
            curve = open_curves[index]
            for endpoint in (curve.points[0], curve.points[-1]):
                stack.extend(endpoint_map.get(point_key(endpoint), []))
        unused -= component
        # Remove ramificações abertas (linhas de dobra/auxiliares) até restar
        # somente o núcleo cíclico. Isso recupera contornos mesmo quando uma
        # entidade extra compartilha um vértice com o perfil de corte.
        core = set(component)
        changed = True
        while changed and core:
            changed = False
            degrees = {}
            for index in core:
                curve = open_curves[index]
                for endpoint in (curve.points[0], curve.points[-1]):
                    key = point_key(endpoint)
                    degrees[key] = degrees.get(key, 0) + 1
            removable = {
                index
                for index in core
                if any(
                    degrees.get(point_key(endpoint), 0) <= 1
                    for endpoint in (open_curves[index].points[0], open_curves[index].points[-1])
                )
            }
            if removable:
                core -= removable
                changed = True
        if not core:
            continue

        # O núcleo pode se separar em mais de um ciclo depois da poda.
        core_unused = set(core)
        cycle_components = []
        while core_unused:
            seed_index = next(iter(core_unused))
            cycle_component = set()
            cycle_stack = [seed_index]
            while cycle_stack:
                index = cycle_stack.pop()
                if index in cycle_component:
                    continue
                cycle_component.add(index)
                curve = open_curves[index]
                for endpoint in (curve.points[0], curve.points[-1]):
                    cycle_stack.extend(
                        candidate
                        for candidate in endpoint_map.get(point_key(endpoint), [])
                        if candidate in core
                    )
            core_unused -= cycle_component
            cycle_components.append(cycle_component)

        for cycle_component in cycle_components:
            degrees = {}
            for index in cycle_component:
                curve = open_curves[index]
                for endpoint in (curve.points[0], curve.points[-1]):
                    key = point_key(endpoint)
                    degrees[key] = degrees.get(key, 0) + 1
            if any(degree != 2 for degree in degrees.values()):
                continue

            remaining = set(cycle_component)
            first_index = next(iter(remaining))
            first_curve = open_curves[first_index]
            ordered = list(first_curve.points)
            remaining.remove(first_index)
            current_key = point_key(ordered[-1])
            start_key = point_key(ordered[0])
            while remaining:
                candidates = [index for index in endpoint_map.get(current_key, []) if index in remaining]
                if not candidates:
                    break
                index = candidates[0]
                curve = open_curves[index]
                points = curve.points if point_key(curve.points[0]) == current_key else list(reversed(curve.points))
                ordered.extend(points[1:])
                current_key = point_key(ordered[-1])
                remaining.remove(index)
            if not remaining and current_key == start_key:
                ordered[-1] = ordered[0]
                contours.append(Curve(ordered, "CONNECTED", True))
    return contours


def signed_area(points):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:]))


def entity_complexity(entities, entity_curves):
    """Resume a complexidade do caminho sem depender da amostragem visual."""
    counts = Counter(entity["type"] for entity in entities)
    polyline_vertices = 0
    spline_control_points = 0
    spline_fit_points = 0
    bulge_segments = 0
    straight_length = 0.0
    curved_length = 0.0
    closed_primitives = 0
    open_primitives = 0

    for entity, curve in entity_curves:
        if curve is None:
            continue
        if curve.closed:
            closed_primitives += 1
        else:
            open_primitives += 1

        kind = entity["type"]
        groups = entity["groups"]
        if kind == "LINE":
            straight_length += curve.length
        elif kind == "LWPOLYLINE":
            vertices = []
            current = None
            for code, value in groups:
                if code == "10":
                    if current is not None:
                        vertices.append(current)
                    current = [float(value), None, 0.0]
                elif code == "20" and current is not None:
                    current[1] = float(value)
                elif code == "42" and current is not None:
                    current[2] = float(value)
            if current is not None:
                vertices.append(current)
            vertices = [v for v in vertices if v[1] is not None]
            polyline_vertices += len(vertices)
            closed = int(first(groups, 70, 0)) & 1 == 1
            segment_count = len(vertices) if closed else max(0, len(vertices) - 1)
            for index in range(segment_count):
                a = vertices[index]
                b = vertices[(index + 1) % len(vertices)]
                sampled = sample_bulge((a[0], a[1]), (b[0], b[1]), a[2])
                length = sum(math.dist(p, q) for p, q in zip(sampled, sampled[1:]))
                if abs(a[2]) > 1e-12:
                    bulge_segments += 1
                    curved_length += length
                else:
                    straight_length += length
        else:
            curved_length += curve.length
            if kind == "SPLINE":
                spline_control_points += len(paired_points(groups, 10, 20))
                spline_fit_points += len(paired_points(groups, 11, 21))

    return {
        "line_entity_count": counts["LINE"],
        "arc_entity_count": counts["ARC"],
        "circle_entity_count": counts["CIRCLE"],
        "ellipse_entity_count": counts["ELLIPSE"],
        "spline_entity_count": counts["SPLINE"],
        "polyline_entity_count": counts["LWPOLYLINE"],
        "polyline_vertex_count": polyline_vertices,
        "spline_control_point_count": spline_control_points,
        "spline_fit_point_count": spline_fit_points,
        "bulge_segment_count": bulge_segments,
        "closed_primitive_count": closed_primitives,
        "open_primitive_count": open_primitives,
        "straight_length": straight_length,
        "curved_length": curved_length,
    }


def extract_geometry(path: Path):
    entities = dxf_entities(path)
    entity_curves = [(entity, entity_to_curve(entity)) for entity in entities]
    complexity = entity_complexity(entities, entity_curves)
    curves = [curve for _, curve in entity_curves]
    curves = [curve for curve in curves if curve and len(curve.points) >= 2 and curve.length > 1e-6]
    contours = closed_contours(curves)
    if not contours:
        return {
            "status": "no_closed_contours",
            "entity_count": len(entities),
            "curve_count": len(curves),
            **complexity,
        }
    info = [{"curve": c, "area": abs(signed_area(c.points)), "perimeter": c.length} for c in contours]
    info.sort(key=lambda item: item["area"], reverse=True)
    outer = info[0]
    inner = info[1:]
    xs = [p[0] for p in outer["curve"].points]
    ys = [p[1] for p in outer["curve"].points]
    total_perimeter = sum(item["perimeter"] for item in info)
    inner_perimeter = sum(item["perimeter"] for item in inner)
    inner_area = sum(item["area"] for item in inner)
    net_area = outer["area"] - inner_area
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    equivalent_diameters = [2.0 * math.sqrt(item["area"] / math.pi) for item in inner]
    return {
        "status": "ok",
        "width": width,
        "height": height,
        "perimeter": total_perimeter,
        "outer_perimeter": outer["perimeter"],
        "inner_perimeter": inner_perimeter,
        "area": net_area,
        "outer_area": outer["area"],
        "inner_area": inner_area,
        "hole_count": len(inner),
        "contour_count": len(info),
        "pierce_count": len(info),
        "entity_count": len(entities),
        "curve_count": len(curves),
        "min_inner_perimeter": min((item["perimeter"] for item in inner), default=0.0),
        "max_inner_perimeter": max((item["perimeter"] for item in inner), default=0.0),
        "mean_inner_perimeter": inner_perimeter / len(inner) if inner else 0.0,
        "small_contour_count_10mm": sum(value <= 10.0 for value in equivalent_diameters),
        "small_contour_count_25mm": sum(value <= 25.0 for value in equivalent_diameters),
        "small_contour_count_50mm": sum(value <= 50.0 for value in equivalent_diameters),
        "inner_perimeter_ratio": inner_perimeter / total_perimeter if total_perimeter else 0.0,
        "bbox_occupancy": net_area / (width * height) if width > 0 and height > 0 else None,
        "outer_compactness": (
            4.0 * math.pi * outer["area"] / (outer["perimeter"] ** 2)
            if outer["perimeter"] > 0
            else None
        ),
        **complexity,
    }


if __name__ == "__main__":
    import json
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Peças Adicionais/DXFs/00.BL.1552.DXF")
    print(json.dumps(extract_geometry(path), indent=2, ensure_ascii=False))
