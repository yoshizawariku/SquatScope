import tkinter as tk
import sys


class CustomButton(tk.Canvas):
    """Custom button that reliably shows color even on macOS."""
    
    def __init__(self, parent, text="Button", command=None, bg_color="#4CAF50", 
                 fg_color="white", hover_color="#45a049", font=("Arial", 12, "bold"),
                 width=120, height=40):
        # macOS compatibility: get parent's background color
        parent_bg = parent.cget('bg') if hasattr(parent, 'cget') else "#2E2E2E"
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                        bg=parent_bg, relief='flat', borderwidth=0)
        
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.font = font
        self.width = width
        self.height = height
        self.is_hovered = False
        self.is_pressed = False
        self.enabled = True
        
        self.draw_button()
        self.bind_events()
    
    def draw_button(self):
        """Draw the button."""
        self.delete("all")
        
        # Determine the button color based on state
        if not self.enabled:
            color = "#CCCCCC"
            text_color = "#666666"
        elif self.is_pressed:
            color = self.darken_color(self.hover_color, 0.1)
            text_color = self.fg_color
        elif self.is_hovered:
            color = self.hover_color
            text_color = self.fg_color
        else:
            color = self.bg_color
            text_color = self.fg_color
        
        # Draw button background (rounded corners)
        border_radius = 6
        self.create_rounded_rectangle(2, 2, self.width-2, self.height-2, 
                                    border_radius, fill=color, outline=color)
        
        # Draw button border
        self.create_rounded_rectangle(0, 0, self.width, self.height, 
                                    border_radius, fill="", outline="#555555", width=1)
        
        # Draw text (with shadow effect)
        # shadow
        self.create_text(self.width//2 + 1, self.height//2 + 1, text=self.text, 
                       fill="#000000", font=self.font, anchor="center")
        # main text
        self.create_text(self.width//2, self.height//2, text=self.text, 
                       fill=text_color, font=self.font, anchor="center")
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle (approximated using a smooth polygon)."""
        points = []
        for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def darken_color(self, color, factor):
        """Darken a hex color by the given factor (0..1)."""
        try:
            # Convert hex color to RGB
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            # Darken each channel
            darkened = tuple(int(c * (1 - factor)) for c in rgb)
            # Convert back to hex
            return '#' + ''.join(f'{c:02x}' for c in darkened)
        except:
            return color
    
    def bind_events(self):
        """Bind mouse and focus events to the widget."""
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        # Focus-related events for macOS compatibility
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
    
    def on_click(self, event):
        """Handle mouse button press."""
        if self.enabled:
            self.is_pressed = True
            self.draw_button()
            self.focus_set()  # set focus
    
    def on_release(self, event):
        """Handle mouse button release and invoke the command if set."""
        if self.enabled:
            self.is_pressed = False
            self.draw_button()
            if self.command:
                try:
                    self.command()
                except Exception as e:
                    print(f"Button command error: {e}")
    
    def on_enter(self, event):
        """Handle mouse entering the widget (hover start)."""
        if self.enabled:
            self.is_hovered = True
            self.draw_button()
    
    def on_leave(self, event):
        """Handle mouse leaving the widget (hover end)."""
        if self.enabled:
            self.is_hovered = False
            self.draw_button()
    
    def on_focus_in(self, event):
        """Handle focus in (unused placeholder)."""
        pass
    
    def on_focus_out(self, event):
        """Handle focus out: clear pressed state and redraw."""
        self.is_pressed = False
        self.draw_button()
    
    def config(self, **kwargs):
        """Update widget settings. Supported keys: text, bg_color, fg_color,
        hover_color, command, state ('disabled' to disable)."""
        if 'text' in kwargs:
            self.text = kwargs['text']
        if 'bg_color' in kwargs:
            self.bg_color = kwargs['bg_color']
        if 'fg_color' in kwargs:
            self.fg_color = kwargs['fg_color'] 
        if 'hover_color' in kwargs:
            self.hover_color = kwargs['hover_color']
        if 'command' in kwargs:
            self.command = kwargs['command']
        if 'state' in kwargs:
            self.enabled = kwargs['state'] != 'disabled'
        
        self.draw_button()
    
    def configure(self, **kwargs):
        """Alias for config()."""
        self.config(**kwargs)
