"""
mzQC parser and chart builder.
Parses the mzQC JSON format directly (no pymzqc dependency).
Spec: https://hupo-psi.github.io/mzQC/
"""
import json
import plotly.graph_objects as go


def parse_mzqc(json_text: str) -> list[dict]:
    """
    Parse an mzQC JSON string and return a flat list of all metrics
    across all runQualities and setQualities.
    Each item: {run, accession, name, value}
    """
    data = json.loads(json_text)
    root = data.get("mzQC", {})
    metrics = []

    for quality_set, label_default in (
        (root.get("runQualities", []), "run"),
        (root.get("setQualities", []), "set"),
    ):
        for quality in quality_set:
            label = quality.get("metadata", {}).get("label", label_default)
            for m in quality.get("qualityMetrics", []):
                metrics.append({
                    "run": label,
                    "accession": m.get("accession", ""),
                    "name": m.get("name", ""),
                    "value": m.get("value"),
                })

    return metrics


def get_scalar_metrics(metrics: list[dict]) -> list[dict]:
    return [m for m in metrics if isinstance(m["value"], (int, float))]


def build_metrics_charts(metrics: list[dict]) -> list[go.Figure]:
    """
    Returns one or two bar charts depending on whether the scalar metrics
    span incompatible scales.

    If the ratio between the largest and smallest value exceeds 100 the
    metrics are split into two groups:
      - counts : large integers (scan / identification counts)
      - ratios : small floats (mass error, rates, percentages)

    Each group gets its own chart with an independent y-axis so that no
    value is visually crushed to zero.
    """
    scalar = get_scalar_metrics(metrics)
    if not scalar:
        return []

    values = [abs(m["value"]) for m in scalar if m["value"] != 0]
    if not values:
        return []

    scale_ratio = max(values) / min(values) if min(values) > 0 else float("inf")

    if scale_ratio > 100:
        counts = [m for m in scalar if abs(m["value"]) >= 1]
        ratios = [m for m in scalar if abs(m["value"]) < 1 or isinstance(m["value"], float) and abs(m["value"]) < 100 and m not in counts]
        # Re-split cleanly: anything >= 100 is a count, anything < 100 is a ratio
        counts = [m for m in scalar if abs(m["value"]) >= 100]
        ratios  = [m for m in scalar if abs(m["value"]) < 100]
        groups = [(counts, "Scan & Identification Counts", "#4C72B0"),
                  (ratios, "Rates & Mass Error Metrics",  "#DD8452")]
    else:
        groups = [(scalar, "QC Metrics", "#4C72B0")]

    figs = []
    for group, title, color in groups:
        if not group:
            continue
        fig = go.Figure(
            go.Bar(
                x=[m["name"] for m in group],
                y=[m["value"] for m in group],
                marker_color=color,
                text=[
                    f"{m['value']:,.2f}" if isinstance(m["value"], float)
                    else f"{m['value']:,}"
                    for m in group
                ],
                textposition="outside",
            )
        )
        fig.update_layout(
            title=title,
            xaxis_tickangle=-35,
            yaxis_title="Value",
            height=380,
            margin=dict(t=50, b=140),
            template="plotly_white",
        )
        figs.append(fig)

    return figs
