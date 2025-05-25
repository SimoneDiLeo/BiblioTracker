import pytest
from services.bibliometric_utils import calculate_h_index, calculate_i10_index

# Test cases for h-index
@pytest.mark.parametrize("citations, expected_h_index", [
    ([], 0),  # No publications
    ([0, 0, 0], 0), # All publications have 0 citations
    ([10, 8, 5, 4, 3], 4), # Example from Wikipedia/standard definition
    ([25, 8, 5, 3, 3], 3), # Another example
    ([1, 1, 1, 1, 1], 1), # All have 1 citation
    ([5, 5, 5, 5, 5], 5), # All have 5 citations
    ([10, 1, 1, 1, 1], 1),
    ([10, 10, 1, 1], 2),
    ([0], 0),
    ([1], 1),
    ([100], 1),
    ([3, 3, 3], 3),
    ([1, 2, 3, 4, 5], 3), # Sorted internally
])
def test_calculate_h_index(citations, expected_h_index):
    assert calculate_h_index(citations) == expected_h_index

# Test cases for i10-index
@pytest.mark.parametrize("citations, expected_i10_index", [
    ([], 0), # No publications
    ([0, 0, 0], 0), # All publications have 0 citations
    ([5, 8, 9], 0), # No publications with >= 10 citations
    ([10, 15, 20], 3), # All publications have >= 10 citations
    ([10, 8, 12, 5, 30], 3), # Mixed citations
    ([9, 9, 9, 10], 1),
    ([10, 10, 10, 10, 10], 5),
    ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 0),
    ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 1),
])
def test_calculate_i10_index(citations, expected_i10_index):
    assert calculate_i10_index(citations) == expected_i10_index

def test_calculate_h_index_with_unsorted_citations():
    citations = [3, 5, 8, 4, 10] # Should be sorted to [10, 8, 5, 4, 3] internally
    expected_h_index = 4
    assert calculate_h_index(citations) == expected_h_index

def test_calculate_i10_index_with_unsorted_citations():
    citations = [5, 30, 8, 12, 10]
    expected_i10_index = 3
    assert calculate_i10_index(citations) == expected_i10_index
