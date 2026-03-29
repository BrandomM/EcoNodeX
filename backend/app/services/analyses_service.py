"""
Community ecology analyses: Shannon, Simpson, species accumulation,
Bray-Curtis, Jaccard.  Pure Python + numpy — no scipy dependency.
"""
from __future__ import annotations

import base64
import io
import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Core indices
# ---------------------------------------------------------------------------

def richness(counts: List[int]) -> int:
    """Species richness: number of taxa with count > 0."""
    return sum(1 for c in counts if c > 0)


def abundance(counts: List[int]) -> int:
    """Total abundance."""
    return sum(c for c in counts if c > 0)


def shannon_wiener(counts: List[int]) -> float:
    """Shannon-Wiener diversity index H'."""
    n = sum(c for c in counts if c > 0)
    if n == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / n
            h -= p * math.log(p)
    return round(h, 6)


def pielou_evenness(counts: List[int]) -> float:
    """Pielou's evenness J' = H' / ln(S)."""
    s = richness(counts)
    if s <= 1:
        return 0.0
    h = shannon_wiener(counts)
    return round(h / math.log(s), 6)


def simpson_index(counts: List[int]) -> float:
    """Simpson diversity index D = 1 - Σ(ni*(ni-1)) / (N*(N-1))."""
    n = sum(c for c in counts if c > 0)
    if n <= 1:
        return 0.0
    d = sum(c * (c - 1) for c in counts if c > 0) / (n * (n - 1))
    return round(1 - d, 6)


def simpson_dominance(counts: List[int]) -> float:
    """Simpson dominance Σ(ni*(ni-1)) / (N*(N-1))."""
    n = sum(c for c in counts if c > 0)
    if n <= 1:
        return 0.0
    return round(sum(c * (c - 1) for c in counts if c > 0) / (n * (n - 1)), 6)


# ---------------------------------------------------------------------------
# Species accumulation curve
# ---------------------------------------------------------------------------

def species_accumulation(
    samples: List[Dict[int, int]],
    sample_labels: List[str],
    n_permutations: int = 100,
    seed: int = 42,
) -> dict:
    """
    Species accumulation curve via random sample-order permutations.

    Parameters
    ----------
    samples : list of {taxon_id: count} dicts, one per sample (replicate)
    sample_labels : label for each sample (same order)
    n_permutations : number of random permutations
    seed : random seed for reproducibility

    Returns
    -------
    dict with keys: x, mean, sd, min, max, samples
    """
    n = len(samples)
    if n == 0:
        return {"x": [], "mean": [], "sd": [], "min": [], "max": [], "samples": []}

    rng = random.Random(seed)
    taxa_per_sample = [set(k for k, v in s.items() if v > 0) for s in samples]

    accumulations: List[List[int]] = []
    for _ in range(n_permutations):
        order = list(range(n))
        rng.shuffle(order)
        seen: set = set()
        acc = []
        for i in order:
            seen |= taxa_per_sample[i]
            acc.append(len(seen))
        accumulations.append(acc)

    arr = np.array(accumulations, dtype=float)
    return {
        "x": list(range(1, n + 1)),
        "mean": arr.mean(axis=0).round(4).tolist(),
        "sd": arr.std(axis=0).round(4).tolist(),
        "min": arr.min(axis=0).astype(int).tolist(),
        "max": arr.max(axis=0).astype(int).tolist(),
        "samples": sample_labels,
    }


# ---------------------------------------------------------------------------
# Beta diversity
# ---------------------------------------------------------------------------

def bray_curtis_matrix(
    samples: List[Dict[int, int]],
) -> List[List[float]]:
    """Bray-Curtis dissimilarity matrix."""
    n = len(samples)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            all_taxa = set(samples[i]) | set(samples[j])
            shared = sum(min(samples[i].get(t, 0), samples[j].get(t, 0)) for t in all_taxa)
            denom = sum(samples[i].values()) + sum(samples[j].values())
            bc = round(1 - 2 * shared / denom, 6) if denom > 0 else 0.0
            matrix[i][j] = matrix[j][i] = bc
    return matrix


def jaccard_matrix(
    samples: List[Dict[int, int]],
) -> List[List[float]]:
    """Jaccard dissimilarity matrix (presence/absence)."""
    n = len(samples)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            si = set(k for k, v in samples[i].items() if v > 0)
            sj = set(k for k, v in samples[j].items() if v > 0)
            inter = len(si & sj)
            union = len(si | sj)
            jac = round(1 - inter / union, 6) if union > 0 else 0.0
            matrix[i][j] = matrix[j][i] = jac
    return matrix


def mean_dissimilarity(matrix: List[List[float]]) -> float:
    """Mean of upper triangle (excluding diagonal)."""
    n = len(matrix)
    if n < 2:
        return 0.0
    vals = [matrix[i][j] for i in range(n) for j in range(i + 1, n)]
    return round(sum(vals) / len(vals), 6)


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _get_plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_accumulation_b64(result: dict) -> str:
    """Return base64-encoded PNG of species accumulation curve."""
    plt = _get_plt()
    fig, ax = plt.subplots(figsize=(7, 4))
    x = result["x"]
    mean = result["mean"]
    sd = result["sd"]
    ax.plot(x, mean, color="#059669", linewidth=2, label="Media")
    ax.fill_between(
        x,
        [m - s for m, s in zip(mean, sd)],
        [m + s for m, s in zip(mean, sd)],
        alpha=0.25,
        color="#059669",
        label="±1 DE",
    )
    ax.set_xlabel("Muestras acumuladas")
    ax.set_ylabel("Riqueza de taxa")
    ax.set_title("Curva de acumulación de especies")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def plot_beta_heatmap_b64(matrix: List[List[float]], labels: List[str], title: str) -> str:
    """Return base64-encoded PNG heatmap of a dissimilarity matrix."""
    plt = _get_plt()
    arr = np.array(matrix)
    fig, ax = plt.subplots(figsize=(max(4, len(labels)), max(3, len(labels))))
    im = ax.imshow(arr, cmap="YlOrRd", vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{arr[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------------
# Helpers to build sample vectors from DB records
# ---------------------------------------------------------------------------

def records_to_sample_dict(records) -> Dict[int, int]:
    """Aggregate OccurrenceRecord rows → {taxon_id: total_count}."""
    d: Dict[int, int] = {}
    for r in records:
        d[r.taxon_id] = d.get(r.taxon_id, 0) + r.individual_count
    return d


def sample_dict_to_counts(d: Dict[int, int]) -> List[int]:
    return list(d.values())
