'''
Created on 15 Apr 2015

Creates the ATF area (edit/object) view and handles its actions.

@author: raquel-ucl
'''

from ..view.AtfAreaView import AtfAreaView


class AtfAreaController(object):

    def __init__(self, mainControler):
        # Create view with a reference to its controller to handle events
        self.view = AtfAreaView(self)

        # Will also need delegating to parent presenter
        self.controller = mainControler


    def setAtfAreaText(self, text):
        self.view.editArea.setText(text)
        self.view.syntax_highlight()
        self.update_line_numbers()


    def getAtfAreaText(self):
        return self.view.editArea.getText()


    def clearAtfArea(self):
        self.view.editArea.setText("")


    def update_line_numbers(self):
        # Get how many lines are in the file
        n_lines = self.getAtfAreaText().count('\n')

        # Reload line numbers text panel
        self.view.repaint_line_numbers(n_lines)
