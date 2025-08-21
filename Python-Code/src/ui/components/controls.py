from tkinter import Frame, Button, Scale, Label, HORIZONTAL

class ControlPanel(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        self.start_button = Button(self, text="Start", command=self.start_data_stream)
        self.start_button.pack(side="left")

        self.stop_button = Button(self, text="Stop", command=self.stop_data_stream)
        self.stop_button.pack(side="left")

        self.slider = Scale(self, from_=1, to=100, orient=HORIZONTAL, label="Sampling Rate (Hz)")
        self.slider.set(50)  # Default value
        self.slider.pack(side="left")

        self.label = Label(self, text="Control Panel")
        self.label.pack(side="left")

    def start_data_stream(self):
        # Logic to start data streaming
        print("Data streaming started.")

    def stop_data_stream(self):
        # Logic to stop data streaming
        print("Data streaming stopped.")