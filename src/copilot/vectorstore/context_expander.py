# expands retrieved chunks with nearby chunks
# helps add intro and explanation context

def expand_with_neighbors(retrieved_chunks, metadata, window=1):
    """
    adds previous and next chunks
    """

    expanded_chunks = []
    used_indexes = []

    total_chunks = len(metadata)

    for chunk in retrieved_chunks:
        idx = chunk["chunk_index"]

        start = idx - window
        end = idx + window

        for i in range(start, end + 1):
            if i >= 0 and i < total_chunks:
                if i not in used_indexes:
                    expanded_chunks.append(metadata[i])
                    used_indexes.append(i)

    return expanded_chunks