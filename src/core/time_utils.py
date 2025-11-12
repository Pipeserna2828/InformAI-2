def duration_ms_from_timestamps(timestamps: list[int]) -> int:
    if not timestamps:
        return 0
    return max(timestamps) - min(timestamps)