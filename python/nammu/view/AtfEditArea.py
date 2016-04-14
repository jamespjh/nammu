from java.awt import Font
from javax.swing import JTextPane, BorderFactory
from java.awt.event import MouseAdapter


class AtfEditArea(JTextPane):
    def __init__(self, parent_component):
        self.parent_component = parent_component
        self.border = BorderFactory.createEmptyBorder(4, 4, 4, 4)
        self.font = Font("Monaco", Font.PLAIN, 14)
        # Tooltip
        self.setToolTipText("Hello")

        listener = CustomMouseListener(self)
        self.addMouseListener(listener)


    def getToolTipText(self, event=None):
        """
        Overrides getToolTipText so that tooltips are only displayed when a
        line contains a validation error.
        """
        if event:
            position = self.viewToModel(event.getPoint())
            line_num = self.get_line_num(position)
            #Check if line_num has an error message assigned
            validation_errors = self.parent_component.validation_errors
            if validation_errors:
                try:
                    return validation_errors[str(line_num)]
                except KeyError:
                    pass


    def get_line_num(self, position):
        """
        Returns line number given mouse position in text area.
        """
        text = self.text[0:position]
        return text.count('\n') + 1


class CustomMouseListener(MouseAdapter):
    """
    Consumes mouse events.
    """
    def __init__(self, panel):
        self.panel = panel
    def mousePressed(self, event):
        offset = self.panel.viewToModel(event.getPoint())
        # Check if tooltip should be displayed for this position
    #     line_num = self.get_line_num(offset)
    #     print offset, line_num
    # def get_line_num(self, offset):
    #     text = self.panel.text[0:offset]
    #     return text.count('\n') + 1
