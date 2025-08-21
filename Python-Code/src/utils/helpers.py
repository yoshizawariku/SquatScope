def calculate_moving_average(data, window_size):
    if len(data) < window_size:
        return []
    return [sum(data[i:i + window_size]) / window_size for i in range(len(data) - window_size + 1)]

def format_timestamp(timestamp):
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def normalize_data(data, min_value, max_value):
    return [(x - min_value) / (max_value - min_value) for x in data]

def convert_to_json(data):
    import json
    return json.dumps(data)

def log_data(data, file_path):
    with open(file_path, 'a') as f:
        f.write(data + '\n')