class DataBuffer:
    def __init__(self, max_size=60000):
        self.max_size = max_size  # Maximum size for the buffer (60 seconds of data at 1000Hz)
        self.data = []

    def add_data(self, new_data):
        self.data.append(new_data)
        if len(self.data) > self.max_size:
            self.data.pop(0)  # Remove the oldest data to maintain the buffer size

    def get_data(self):
        return self.data

    def clear(self):
        self.data.clear()  # Clear the buffer data

    def __len__(self):
        return len(self.data)  # Return the current size of the buffer

    def is_empty(self):
        return len(self.data) == 0  # Check if the buffer is empty

    def get_latest(self, count=1):
        return self.data[-count:] if len(self.data) >= count else self.data  # Get the latest 'count' data points