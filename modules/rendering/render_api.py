class TextRenderer:
    """Class để render text lên image"""

    def initialize(self, config: dict = {}):
        pass

    def __init__(self, config: dict):
        self.config = config
        self.font_size = config.get("font_size", 12)
        self.font_color = config.get("font_color", "#000000")
        self.background_color = config.get("background_color", "#FFFFFF")
        self.line_spacing = config.get("line_spacing", 1.2)

    def render_text(self, image, text_blocks):
        """Render text lên image"""
        # Implementation sẽ được thêm sau
        return image
