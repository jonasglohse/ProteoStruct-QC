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


def build_metrics_chart(metrics: list[dict]) -> go.Figure | None:
    """
    Bar chart of all scalar numeric metrics.
    Prefers known scan-count accessions; falls back to all scalars (capped at 12).
    """
    scalar = get_scalar_metrics(metrics)
    if not scalar:
        return None

    # Known scan/identification count accessions — show these first if present
    priority = {
        "QC:4000059", "QC:4000060",  # MS1 / MS2 spectra
        "QC:4000053", "QC:4000054",  # identified MS1 / MS2
        "QC:4000023", "QC:4000024",  # mass accuracy mean / variance
    }
    prioritised = [m for m in scalar if m["accession"] in priority]
    display = prioritised if prioritised else scalar[:12]

    fig = go.Figure(
        go.Bar(
            x=[m["name"] for m in display],
            y=[m["value"] for m in display],
            marker_color="#4C72B0",
            text=[f"{m['value']:,.2f}" if isinstance(m["value"], float)
                  else f"{m['value']:,}" for m in display],
            textposition="outside",
        )
    )
    fig.update_layout(
        xaxis_tickangle=-35,
        yaxis_title="Value",
        height=420,
        margin=dict(t=20, b=140),
        template="plotly_white",
    )
    return fig
