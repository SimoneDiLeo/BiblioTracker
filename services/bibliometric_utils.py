from typing import List

def calculate_h_index(citation_counts: List[int]) -> int:
    """
    Calculates the h-index from a list of citation counts.
    """
    if not citation_counts:
        return 0
    
    # Sort citations in descending order
    sorted_citations = sorted(citation_counts, reverse=True)
    
    h = 0
    for i, count in enumerate(sorted_citations):
        # The h-index is the largest number h such that h publications have at least h citations.
        # i+1 is the number of publications with 'count' or more citations.
        if count >= i + 1:
            h = i + 1
        else:
            break # Since counts are sorted, further publications won't meet the criteria
    return h

def calculate_i10_index(citation_counts: List[int]) -> int:
    """
    Calculates the i10-index from a list of citation counts.
    The i10-index is the number of publications with at least 10 citations.
    """
    if not citation_counts:
        return 0
    
    i10_count = 0
    for count in citation_counts:
        if count >= 10:
            i10_count += 1
    return i10_count
