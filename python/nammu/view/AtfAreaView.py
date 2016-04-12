'''
Created on 15 Apr 2015

Initializes the ATF (edit/model) view and sets its layout.

@author: raquel-ucl
'''

from java.awt import Font, BorderLayout, Dimension, Color
from java.awt.event import KeyListener
from javax.swing import JTextPane, JScrollPane, JPanel, BorderFactory
from javax.swing.text import DefaultHighlighter, StyleContext, StyleConstants
from javax.swing.text import SimpleAttributeSet
from pyoracc.atf.atflex import AtfLexer


class AtfAreaView(JPanel):

    def __init__(self, controller):
        '''
        Creates default empty text area in a panel for ATF edition.
        It has syntax highlighting based on the ATF parser (pyoracc).
        It also highlights line numbers where there are validations errors
        returned by the ORACC server.
        '''
        # Give reference to controller to delegate action response
        self.controller = controller

        # Make text area occupy all available space and resize with parent
        # window
        self.setLayout(BorderLayout())

        # Create text edition area
        self.editArea = self.setup_edit_area()

        # Create text panel to display the line numbers
        self.line_numbers_area = self.setup_line_numbers_area()

        # Needed by syntax highlighter
        self.edit_area_styledoc = self.editArea.getStyledDocument()
        self.line_numbers_styledoc = self.line_numbers_area.getStyledDocument()

        # Create panel that'll contain the ScrollPane and the line numbers
        container = JPanel(BorderLayout())
        container.add(self.editArea, BorderLayout.CENTER)
        container.add(self.line_numbers_area, BorderLayout.WEST)

        # Will need scrolling controls that scroll line numbers and text lines
        # simultaneously
        scrollingText = JScrollPane(container)
        scrollingText.setPreferredSize(Dimension(1, 500))

        # Add to parent panel
        self.add(scrollingText, BorderLayout.CENTER)

        # Syntax highlight setup
        sc = StyleContext.getDefaultStyleContext()
        self.setup_syntax_highlight_colours()
        self.colors = {}
        for color in self.colorlut:
            self.colors[color] = sc.addAttribute(
                                           SimpleAttributeSet.EMPTY,
                                           StyleConstants.Foreground,
                                           Color(*self.colorlut[color]))
        self.editArea.addKeyListener(AtfAreaKeyListener(self))
        self.setup_syntax_highlight_tokens()


    def syntax_highlight(self):
        """
        Implements syntax highlighting based on pyoracc.
        """
        lexer = AtfLexer(skipinvalid=True).lexer
        text = self.editArea.text
        splittext = text.split('\n')
        lexer.input(text)
        # Reset all styling
        defaultcolor = self.tokencolorlu['default'][0]
        self.edit_area_styledoc.setCharacterAttributes(0, len(text),
                                                    self.colors[defaultcolor],
                                                    True)
        for tok in lexer:
            if tok.type in self.tokencolorlu:
                if type(self.tokencolorlu[tok.type]) is dict:
                    # the token should be styled differently depending
                    # on state
                    try:
                        state = lexer.current_state()
                        color = self.tokencolorlu[tok.type][state][0]
                        styleline = self.tokencolorlu[tok.type][state][1]
                    except KeyError:
                        color = self.tokencolorlu['default'][0]
                        styleline = self.tokencolorlu['default'][1]
                else:
                    color = self.tokencolorlu[tok.type][0]
                    styleline = self.tokencolorlu[tok.type][1]
                if styleline:
                    mylength = len(splittext[tok.lineno-1])
                else:
                    mylength = len(tok.value)
                self.edit_area_styledoc.setCharacterAttributes(tok.lexpos, mylength,
                                                     self.colors[color],
                                                     True)


    def setup_edit_area(self):
        """
        Creates a JTextPane where the ATF text will be displayed, allowing text
        edition.
        """
        edit_area = JTextPane()
        edit_area.border = BorderFactory.createEmptyBorder(4, 4, 4, 4)
        edit_area.font = Font("Monaco", Font.PLAIN, 14)

        return edit_area


    def setup_line_numbers_area(self):
        """
        Line numbers need to be displayed in a separate panel with different
        styling.
        """
        line_numbers_area = JTextPane()
        border = BorderFactory.createEmptyBorder(4, 4, 4, 4)
        line_numbers_area.border = border
        line_numbers_area.setText("1: \n")
        line_numbers_area.setEditable(False)

        # Align right
        para_attribs = SimpleAttributeSet()
        StyleConstants.setAlignment(para_attribs, StyleConstants.ALIGN_RIGHT)
        line_numbers_area.setParagraphAttributes(para_attribs, True)

        # Use default style
        char_attribs = SimpleAttributeSet()
        StyleConstants.setFontFamily(char_attribs, "Monaco")
        StyleConstants.setFontSize(char_attribs, 14)
        StyleConstants.setForeground(char_attribs, Color.gray)
        line_numbers_area.setCharacterAttributes(char_attribs, True)

        return line_numbers_area


    def setup_syntax_highlight_colours(self):
        # Syntax highlighting colors based on SOLARIZED
        self.colorlut = {}

        # Black backgroud tones
        self.colorlut['base03'] = (0, 43, 54)
        self.colorlut['base02'] = (7, 54, 66)

        # Content tones
        self.colorlut['base01'] = (88, 110, 117)
        self.colorlut['base00'] = (101, 123, 131)
        self.colorlut['base0'] = (131, 148, 150)
        self.colorlut['base1'] = (147, 161, 161)

        # White background tones
        self.colorlut['base2'] = (238, 232, 213)
        self.colorlut['base3'] = (253, 246, 227)

        # Accent Colors
        self.colorlut['yellow'] = (181, 137, 0)
        self.colorlut['orange'] = (203, 75, 22)
        self.colorlut['red'] = (220,  50, 47)
        self.colorlut['magenta'] = (211,  54, 130)
        self.colorlut['violet'] = (108, 113, 196)
        self.colorlut['blue'] = (38, 139, 210)
        self.colorlut['cyan'] = (42, 161, 152)
        self.colorlut['green'] = (133, 153, 0)
        self.colorlut['black'] = (0, 0, 0)


    def setup_syntax_highlight_tokens(self):
        self.tokencolorlu = {}
        self.tokencolorlu['AMPERSAND'] = ('green', True)
        for i in AtfLexer.protocols:
            self.tokencolorlu[i] = ('magenta', False)
        for i in AtfLexer.protocol_keywords:
            self.tokencolorlu[i] = ('magenta', False)
        for i in AtfLexer.structures:
            self.tokencolorlu[i] = ('violet', False)
        for i in AtfLexer.long_argument_structures:
            self.tokencolorlu[i] = ('violet', False)
        self.tokencolorlu['DOLLAR'] = ('orange', False)
        for i in AtfLexer.dollar_keywords:
            self.tokencolorlu[i] = ('orange', False)
        self.tokencolorlu['REFERENCE'] = ('base01', False)
        self.tokencolorlu['COMMENT'] = ('base1', True)
        for i in AtfLexer.translation_keywords:
            self.tokencolorlu[i] = ('green', False)
        self.tokencolorlu['LINELABEL'] = ('yellow', False)
        self.tokencolorlu['LEM'] = ('red', False)
        self.tokencolorlu['SEMICOLON'] = ('red', False)
        self.tokencolorlu['HAT'] = ('cyan', False)

        self.tokencolorlu['NOTE'] = {}
        self.tokencolorlu['NOTE']['flagged'] = ('violet', False)
        self.tokencolorlu['NOTE']['para'] = ('magenta', False)

        self.tokencolorlu['PROJECT'] = {}
        self.tokencolorlu['PROJECT']['flagged'] = ('magenta', False)
        self.tokencolorlu['PROJECT']['transctrl'] = ('green', False)
        self.tokencolorlu['default'] = ('black', False)

    def repaint_line_numbers(self, n_lines):
        """
        Draws line numbers in corresponding panel.
        """
        # Create line numbers
        numbers = ""
        for line in range(n_lines + 1):
            numbers += str(line + 1) + ": \n"

        # Print in line numbers' area
        self.line_numbers_area.setText(numbers)


class AtfAreaKeyListener(KeyListener):
    """
    Listens for user releasing keys to reload the syntax highlighting and the
    line numbers (they'll need to be redrawn when a new line or block is added
    or removed).
    """
    def __init__(self, atfareaview):
        self.atfareaview = atfareaview

    def keyReleased(self, ke):
        self.atfareaview.syntax_highlight()
        # Check length hasn't changed, otherwise repaint line numbers
        number_lines = self.atfareaview.line_numbers_area.text.count('\n')
        text_lines = self.atfareaview.editArea.text.count('\n')
        if number_lines - 1 != text_lines:
            self.atfareaview.repaint_line_numbers(text_lines)

    # We have to implement these since the baseclass versions
    # raise non implemented errors when called by the event.
    def keyPressed(self, ke):
        pass

    def keyTyped(self, ke):
        # It would be more natural to use this event. However
        # this gives the string before typing
        pass
#
