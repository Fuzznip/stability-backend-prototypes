def parse_time_to_seconds(time_str):
    """
    Convert a time string in the format 'H:MM:SS.S' to seconds.
    Examples: '1:05:00.0', '0:24:00.0', '0:22:30.0'
    
    Args:
        time_str (str): Time string in format 'H:MM:SS.S' or 'MM:SS.S'
        
    Returns:
        float: Total number of seconds represented by the time string
        
    Raises:
        ValueError: If the time format is invalid
    """
    if not time_str:
        return None
        
    parts = time_str.split(':')
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")
