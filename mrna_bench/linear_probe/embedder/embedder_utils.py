def get_output_filename(
    output_dir: str,
    model_name: str,
    dataset_name: str,
    sequence_chunk_overlap: int,
    d_chunk_ind: int = 0,
    d_chunk_max_ind: int = 0
) -> str:
    """Get standardized embedding file name.

    NOTE: Model and dataset names should not have underscores.

    Args:
        output_dir: Directory to store embeddings.
        model_name: Name of embedding model.
        dataset_name: Dataset which is embedded.
        sequence_chunk_overlap: Number of tokens overlapped in sequence chunks.
        d_chunk_ind: Index of current dataset chunk.
        d_chunk_max_ind: Maximum number of dataset chunks.
    """
    out_path = "{}/{}_{}_o{}".format(
        output_dir,
        dataset_name,
        model_name,
        sequence_chunk_overlap
    )

    if d_chunk_max_ind != 0:
        out_path += "_{}-{}".format(d_chunk_ind, d_chunk_max_ind)

    return out_path
