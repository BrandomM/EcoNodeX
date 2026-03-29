"""Unit tests for analyses_service mathematical correctness."""
import math
import pytest
from backend.app.services.analyses_service import (
    shannon_wiener,
    pielou_evenness,
    simpson_index,
    simpson_dominance,
    richness,
    abundance,
    bray_curtis_matrix,
    jaccard_matrix,
    species_accumulation,
    mean_dissimilarity,
)


def test_shannon_uniform():
    """Equal abundances → maximum H' = ln(S)."""
    counts = [10, 10, 10, 10]
    h = shannon_wiener(counts)
    expected = math.log(4)
    assert abs(h - expected) < 1e-4


def test_shannon_single_species():
    """One species → H' = 0."""
    assert shannon_wiener([100]) == 0.0


def test_shannon_empty():
    assert shannon_wiener([]) == 0.0
    assert shannon_wiener([0, 0]) == 0.0


def test_pielou_uniform():
    """Uniform distribution → J' = 1."""
    h = pielou_evenness([5, 5, 5, 5])
    assert abs(h - 1.0) < 1e-4


def test_simpson_uniform():
    """High diversity → D close to 1 - 1/S."""
    s = 4
    counts = [25] * s
    d = simpson_index(counts)
    expected = 1 - 1 / s
    assert abs(d - expected) < 0.01


def test_simpson_single():
    assert simpson_index([100]) == 0.0


def test_richness():
    assert richness([5, 0, 3, 0, 1]) == 3
    assert richness([]) == 0


def test_abundance():
    assert abundance([5, 0, 3]) == 8


def test_bray_curtis_identical():
    """Identical communities → 0 dissimilarity."""
    a = {1: 10, 2: 5}
    b = {1: 10, 2: 5}
    mat = bray_curtis_matrix([a, b])
    assert mat[0][1] == 0.0


def test_bray_curtis_disjoint():
    """Completely disjoint communities → 1.0."""
    a = {1: 10}
    b = {2: 10}
    mat = bray_curtis_matrix([a, b])
    assert mat[0][1] == 1.0


def test_bray_curtis_diagonal():
    """Diagonal should always be 0."""
    samples = [{1: 5, 2: 3}, {1: 2, 3: 7}]
    mat = bray_curtis_matrix(samples)
    for i in range(len(samples)):
        assert mat[i][i] == 0.0


def test_jaccard_identical():
    a = {1: 5, 2: 3}
    b = {1: 1, 2: 10}
    mat = jaccard_matrix([a, b])
    assert mat[0][1] == 0.0   # same presence


def test_jaccard_disjoint():
    a = {1: 5}
    b = {2: 5}
    mat = jaccard_matrix([a, b])
    assert mat[0][1] == 1.0


def test_jaccard_partial():
    a = {1: 1, 2: 1}
    b = {2: 1, 3: 1}
    mat = jaccard_matrix([a, b])
    # intersection=1, union=3 → 1 - 1/3 = 2/3
    assert abs(mat[0][1] - 2/3) < 1e-4


def test_accumulation_shape():
    samples = [{1: 5, 2: 3}, {2: 1, 3: 7}, {3: 2, 4: 1}]
    labels = ['R1', 'R2', 'R3']
    result = species_accumulation(samples, labels, n_permutations=20)
    assert result['x'] == [1, 2, 3]
    assert len(result['mean']) == 3
    assert len(result['sd']) == 3
    # First sample always has ≥1 species
    assert result['min'][0] >= 1
    # Final mean should equal total richness
    all_taxa = set()
    for s in samples:
        all_taxa |= set(s.keys())
    assert result['max'][-1] == len(all_taxa)


def test_mean_dissimilarity():
    mat = [[0, 0.4, 0.6], [0.4, 0, 0.8], [0.6, 0.8, 0]]
    assert abs(mean_dissimilarity(mat) - (0.4 + 0.6 + 0.8) / 3) < 1e-6


def test_mean_dissimilarity_single():
    assert mean_dissimilarity([[0]]) == 0.0
