# -*- coding: utf-8 -*-
import pytest
import codecs
import time
import os

import yaml
from java.awt import Color
from javax.swing import JSplitPane, JFileChooser, JScrollPane
from javax.swing.undo import CompoundEdit
from javax.swing import JOptionPane

from python.nammu.controller.NammuController import NammuController
from python.nammu.utils import ConfigDict, NammuException, save_yaml_config


@pytest.yield_fixture(scope="class", autouse=True)
def nammu():
    yield NammuController()


@pytest.fixture
def simpletext():
    return u'this is a simple test line'


@pytest.fixture
def english():
    return codecs.open('resources/test/english.atf',
                       encoding='utf-8').read()


@pytest.fixture
def english_no_lem():
    return codecs.open('resources/test/english_no_lem.atf',
                       encoding='utf-8').read()


@pytest.fixture
def broken_atf():
    return codecs.open('resources/test/english_broken.atf',
                       encoding='utf-8').read()


@pytest.fixture
def arabic():
    return codecs.open('resources/test/arabic.atf',
                       encoding='utf-8').read()


@pytest.fixture
def arabic_no_lem():
    return codecs.open('resources/test/arabic_no_lem.atf',
                       encoding='utf-8').read()


@pytest.fixture
def black():
    return Color(0, 0, 0)


@pytest.fixture
def green():
    return Color(133, 153, 0)


@pytest.fixture
def yellow():
    return Color(181, 137, 0)


@pytest.fixture
def red():
    return Color(220, 50, 47)


@pytest.fixture
def blue():
    return Color(108, 113, 196)


@pytest.fixture
def pink():
    return Color(211, 54, 130)


@pytest.fixture
def empty_compound():
    return CompoundEdit()


def show_diag_patch(a, b, c):
    '''
    Monkeypatch the clicking of the ok button on the file load dialog.
    '''
    return 0


def selected_file_patch_english(a):
    return mockFile('resources/test/english.atf')


def selected_file_patch_arabic(a):
    return mockFile('resources/test/arabic.atf')


def show_message_dialog(*args):
    '''
    This will be used to replace `JOptionPane().showMessageDialog`.
    '''
    return 0


def unsaved_patch():
    return True


def generic_loader(filename):
    return codecs.open(filename, encoding='utf-8').read()


class mockFile(object):
    '''
    A class used to monkeypatch the Java file object
    '''
    def __init__(self, filename):
        self.filename = filename

    def getCanonicalPath(self):
        return self.filename

    def getName(self):
        return os.path.basename(self.filename)


class TestNammu(object):

    @pytest.mark.parametrize('text', [simpletext(), english(), arabic(),
                                      english_no_lem(), arabic_no_lem(),
                                      broken_atf()])
    def test_set_text(self, text, nammu):
        nammu.atfAreaController.edit_area.setText(text)
        assert nammu.atfAreaController.edit_area.getText() == text

    @pytest.mark.parametrize('text, caret, color', [(simpletext(), 5, black()),
                                                    (english(), 137, red()),
                                                    (arabic(), 46, pink()),
                                                    (arabic_no_lem(), 113,
                                                     blue()),
                                                    (english_no_lem(), 166,
                                                     yellow()),
                                                    (broken_atf(), 3,
                                                     green())])
    def test_syntax_highlight(self, text, caret, color, nammu):
        nammu.atfAreaController.edit_area.setText(text)
        # Wait here so the highlight completes before getting the styledoc
        time.sleep(2)
        doc = nammu.atfAreaController.edit_area.getStyledDocument()

        # Get the colour of a given character that should be highlighted
        c = doc.getForeground(doc.getCharacterElement(caret).getAttributes())
        assert c.equals(color)

    @pytest.mark.parametrize('text', [english_no_lem(), arabic_no_lem()])
    def test_successful_lem_no_existing_lem(self, text, nammu):
        nammu.currentFilename = 'pytest.atf'  # bypass saving the file
        arabic_idx = nammu.atfAreaController.findArabic(text)
        if arabic_idx:
            nammu.atf_body = text[0:arabic_idx]
            nammu.atf_translation = text[arabic_idx:]
            nammu.arabic(force=True)
        else:
            nammu.atfAreaController.edit_area.setText(text)
        nammu.lemmatise()
        text_with_lemmas = nammu.atfAreaController.edit_area.getText()
        assert text != text_with_lemmas
        # Make sure Arabic translation is not appended to the edit area.
        assert not nammu.atfAreaController.findArabic(text_with_lemmas)

    @pytest.mark.parametrize('text', [english(), arabic()])
    def test_successful_lem_existing_lem(self, text, nammu):
        nammu.currentFilename = 'pytest.atf'  # bypass saving the file
        nammu.atfAreaController.edit_area.setText(text)
        nammu.lemmatise()
        assert text == nammu.atfAreaController.edit_area.getText()

    def test_unsuccsessful_lem(self, broken_atf, nammu):
        nammu.currentFilename = 'pytest.atf'  # bypass saving the file
        nammu.atfAreaController.edit_area.setText(broken_atf)
        nammu.lemmatise()

        # An empty dictionary means no validation errors
        assert nammu.atfAreaController.validation_errors

    @pytest.mark.parametrize('text', [english(), arabic(), english_no_lem(),
                                      arabic_no_lem()])
    def test_successful_validation(self, text, nammu):
        nammu.currentFilename = 'pytest.atf'  # bypass saving the file
        nammu.atfAreaController.edit_area.setText(text)
        nammu.validate()

        # An empty dictionary means no validation errors
        assert not nammu.atfAreaController.validation_errors

    def test_unsuccessful_validation(self, broken_atf, nammu):
        nammu.currentFilename = 'pytest.atf'  # bypass saving the file
        nammu.atfAreaController.edit_area.setText(broken_atf)
        nammu.validate()

        # An empty dictionary means no validation errors
        assert nammu.atfAreaController.validation_errors

    def test_syntax_highlight_add_text(self, monkeypatch, nammu):
        """
        Test that syntax highlighting works correctly when adding lines to a
        document with an Arabic translation.
        """
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_arabic)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)
        nammu.openFile()
        edit_area = nammu.atfAreaController.edit_area
        atf_body = edit_area.getText()
        edit_area.setText(atf_body + '\n@obverse')

        # Wait here so the highlight completes before getting the styledoc
        time.sleep(2)
        doc = edit_area.getStyledDocument()
        caret = doc.getLength() - 2
        # Get the colour of a given character that should be highlighted
        c = doc.getForeground(doc.getCharacterElement(caret).getAttributes())
        assert c.equals(blue())

    def test_file_load(self, monkeypatch, nammu):
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_english)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)

        nammu.openFile()
        assert len(nammu.atfAreaController.edit_area.getText()) > 1

    def test_saving_split_pane(self, monkeypatch, tmpdir, arabic, nammu):
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_arabic)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)

        nammu.openFile()
        nammu.currentFilename = str(tmpdir.join('pytest.atf'))

        nammu.saveFile()

        assert os.path.isfile(nammu.currentFilename)
        assert generic_loader(nammu.currentFilename) == arabic

    def test_saving_single_pane(self, monkeypatch, tmpdir, english, nammu):
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_english)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)

        nammu.openFile()
        nammu.currentFilename = str(tmpdir.join('pytest.atf'))

        nammu.saveFile()

        assert os.path.isfile(nammu.currentFilename)
        assert generic_loader(nammu.currentFilename) == english

    def test_arabic_split_pane(self, monkeypatch, nammu):
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_arabic)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)

        assert nammu.arabic_edition_on is False
        nammu.openFile()
        assert nammu.arabic_edition_on is True

        assert isinstance(nammu.atfAreaController.view.container,
                          JSplitPane)

    def test_close_file(self, monkeypatch, nammu):
        """
        Test that closing a document leaves the editor in a proper state.
        """
        atfAreaController = nammu.atfAreaController
        view = atfAreaController.view
        menuView = nammu.menuController.view
        toggleVertical = menuView.get_menu_item_by_name(
            "Window", "Toggle Vertical Split Editor")
        toggleHorizontal = menuView.get_menu_item_by_name(
            "Window", "Toggle Horizontal Split Editor")
        toggleArabic = menuView.get_menu_item_by_name(
            "Window", "Toggle Arabic Translation Editor")
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_arabic)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)
        nammu.openFile()
        nammu.closeFile()
        assert isinstance(view.container, JSplitPane)
        assert atfAreaController.arabic_area.getText() == ""
        assert not toggleVertical.isEnabled()
        assert not toggleHorizontal.isEnabled()
        assert toggleArabic.isEnabled()
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_english)
        nammu.openFile()
        nammu.closeFile()
        assert isinstance(view.container, JScrollPane)
        assert toggleVertical.isEnabled()
        assert toggleHorizontal.isEnabled()
        assert toggleArabic.isEnabled()

    def test_edit_compound(self, nammu):
        '''
        Adding a character should trigger several edit events (insert and
        update colouring), added to the undo manager as a single edit compound
        so they are all undone/redone at once.
        '''
        controller = nammu.atfAreaController
        controller.edit_area.setText("a")
        listener = controller.view.edit_listener
        # Edits list within the undo_manager is not accessible and toString()
        # is the only way I found to inspect it.
        # TODO: I could do some of this stuff in Java, where I can access the
        # edits, but that's a bit overcomplicated at this stage.
        assert ("edits: []" not in controller.undo_manager.toString())

    def test_undo_empty_pane(self, nammu):
        '''
        Undo when empty pane should not do anything and the undo stackpile
        should remain empty.
        This test is needed because undoing empty panels is unstable and
        sometimes raises exceptions.
        '''
        controller = nammu.atfAreaController
        controller.clearAtfArea()
        controller.undo()
        assert ("edits: []" in controller.undo_manager.toString())

    def test_redo_empty_pane(self, nammu):
        '''
        Redo when empty pane should not do anything and the undo stackpile
        should remain empty.
        This test is needed because undoing empty panels is unstable and
        sometimes raises exceptions.
        '''
        controller = nammu.atfAreaController
        controller.clearAtfArea()
        controller.redo()
        assert ("edits: []" in controller.undo_manager.toString())

    def test_undo_after_opening_file(self, monkeypatch, nammu):
        '''
        Undo after opening a new file should not bring back the old file.
        '''
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_english)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)
        nammu.openFile()
        controller = nammu.atfAreaController
        controller.undo()
        assert ("edits: []" in controller.undo_manager.toString())

    def test_undo_after_closing_file(self, monkeypatch, nammu):
        '''
        Undo after closing a file should not bring back the old file.
        '''
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_english)
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)
        nammu.openFile()
        nammu.closeFile()
        controller = nammu.atfAreaController
        controller.undo()
        assert ("edits: []" in controller.undo_manager.toString())

    def test_undo_edit_pane(self, empty_compound, nammu):
        '''
        Check adding a simple text and undoing last edit compound works.
        '''
        controller = nammu.atfAreaController
        undo_manager = controller.undo_manager
        # Clear all possible edits from previous tests
        undo_manager.discardAllEdits()
        # Write something to undo
        controller.edit_area.setText("Hello Nammu!")
        controller.undo()
        assert (controller.edit_area.getText() == "" and
                "edits: []" not in undo_manager.toString())

    def test_undo_split_primary_pane(self, simpletext, nammu):
        '''
        Using Nammu's split pane mode, check undoing something on the primary
        pane is reflected also in secondary pane and vice versa.
        Undo action is not linked to an edit area but to the controller, so
        this test checks for undoing in both primary and secondary.
        '''
        controller = nammu.atfAreaController
        nammu.splitEditorV()
        controller.edit_area.setText("Hello primary edit area!")
        controller.undo()
        assert (controller.edit_area.getText() ==
                controller.secondary_area.getText())

    def test_redo_split_primary_pane(self, simpletext, nammu):
        '''
        Using Nammu's split pane mode, check redoing something on the primary
        pane is reflected also in secondary pane and vice versa.
        Redo action is not linked to an edit area but to the controller, so
        this test checks for redoing in both primary and secondary.
        '''
        controller = nammu.atfAreaController
        nammu.splitEditorV()
        controller.edit_area.setText("Hello primary edit area!")
        controller.undo()
        controller.redo()
        assert (controller.edit_area.getText() ==
                controller.secondary_area.getText())

    def test_undo_arabic_primary(self, arabic, nammu):
        '''
        Using Nammu's arabic mode, check undoing something on the primary
        pane works and arabic pane's content remains intact.
        '''
        edit_area = nammu.atfAreaController.edit_area
        arabic_area = nammu.atfAreaController.arabic_area
        nammu.arabic()
        edit_area.setText("Hello primary edit area!")
        arabic_area.setText("في شتة")
        nammu.atfAreaController.undo()
        assert (edit_area.getText() == "Hello primary edit area!" and
                arabic_area.getText() == "")

    def test_redo_arabic_primary(self, arabic, nammu):
        '''
        Using Nammu's arabic mode, check redoing something on the primary
        pane works and arabic pane's content remains intact.
        '''
        edit_area = nammu.atfAreaController.edit_area
        arabic_area = nammu.atfAreaController.arabic_area
        nammu.arabic()
        edit_area.setText("Hello primary edit area!")
        arabic_area.setText("في شتة")
        nammu.atfAreaController.undo()
        nammu.atfAreaController.redo()
        assert (edit_area.getText() == "Hello primary edit area!" and
                arabic_area.getText() == "في شتة")

    def test_undo_arabic_pane(self, arabic, nammu):
        '''
        Using Nammu's arabic mode, check undoing something on the arabic
        pane works and primary pane's content remains intact.
        '''
        edit_area = nammu.atfAreaController.edit_area
        arabic_area = nammu.atfAreaController.arabic_area
        nammu.arabic()
        arabic_area.setText("في شتة")
        edit_area.setText("Hello primary edit area!")
        nammu.atfAreaController.undo()
        assert (edit_area.getText() == "" and
                arabic_area.getText() == "في شتة")

    def test_redo_arabic_pane(self, arabic, nammu):
        '''
        Using Nammu's arabic mode, check redoing something on the arabic
        pane works and primary pane's content remains intact.
        '''
        edit_area = nammu.atfAreaController.edit_area
        arabic_area = nammu.atfAreaController.arabic_area
        nammu.arabic()
        arabic_area.setText("في شتة")
        edit_area.setText("Hello primary edit area!")
        nammu.atfAreaController.undo()
        nammu.atfAreaController.redo()
        assert (edit_area.getText() == "Hello primary edit area!" and
                arabic_area.getText() == "في شتة")

    @pytest.mark.parametrize("this, orthogonal",
                             [("Vertical", "Horizontal"),
                              ("Horizontal", "Vertical")])
    def test_toggling_split(self, this, orthogonal):
        """
        Test toggling vertical and horizontal split view.
        """
        nammu = NammuController()
        view = nammu.atfAreaController.view
        view.setup_edit_area_no_split()
        menuView = nammu.menuController.view
        orientation = getattr(JSplitPane,
                              "{}_SPLIT".format(this.upper()))
        toggleThis = menuView.get_menu_item_by_name(
            "Window", "Toggle {} Split Editor".format(this))
        toggleOrthogonal = menuView.get_menu_item_by_name(
            "Window", "Toggle {} Split Editor".format(orthogonal))
        toggleArabic = menuView.get_menu_item_by_name(
            "Window", "Toggle Arabic Translation Editor")
        # Split: only toggling in the same direction should be enabled.
        view.toggle_split(orientation)
        assert view.container.getOrientation() == orientation
        assert toggleThis.isEnabled()
        assert not toggleOrthogonal.isEnabled()
        assert not toggleArabic.isEnabled()
        # Try toggling orthogonal split: nothing should happen.
        view.toggle_split(getattr(JSplitPane,
                                  "{}_SPLIT".format(orthogonal.upper())))
        assert view.container.getOrientation() == orientation
        assert toggleThis.isEnabled()
        assert not toggleOrthogonal.isEnabled()
        assert not toggleArabic.isEnabled()
        # Toggle again: no split view.
        view.toggle_split(orientation)
        assert isinstance(view.container, JScrollPane)
        assert toggleThis.isEnabled()
        assert toggleOrthogonal.isEnabled()
        assert toggleArabic.isEnabled()

    def test_toggling_arabic_split(self):
        """
        Test toggling split views in Arabic file.
        """
        nammu = NammuController()
        view = nammu.atfAreaController.view
        view.setup_edit_area_no_split()
        menuView = nammu.menuController.view
        toggleVertical = menuView.get_menu_item_by_name(
            "Window", "Toggle Vertical Split Editor")
        toggleHorizontal = menuView.get_menu_item_by_name(
            "Window", "Toggle Horizontal Split Editor")
        toggleArabic = menuView.get_menu_item_by_name(
            "Window", "Toggle Arabic Translation Editor")
        # Split with Arabic pane but with no Arabic text: it creates the
        # vertical split view.  Only toggling Arabic should be enabled.
        view.toggle_split_arabic(JSplitPane.VERTICAL_SPLIT, "", "")
        assert view.container.getOrientation() == JSplitPane.VERTICAL_SPLIT
        assert not toggleVertical.isEnabled()
        assert not toggleHorizontal.isEnabled()
        assert toggleArabic.isEnabled()
        # Try toggling horizontally: nothing should happen.
        view.toggle_split(JSplitPane.HORIZONTAL_SPLIT)
        assert view.container.getOrientation() == JSplitPane.VERTICAL_SPLIT
        assert not toggleVertical.isEnabled()
        assert not toggleHorizontal.isEnabled()
        assert toggleArabic.isEnabled()
        # Toggle Arabic pane: restore view with no split.
        view.toggle_split_arabic(JSplitPane.VERTICAL_SPLIT, "", "")
        assert isinstance(view.container, JScrollPane)
        assert toggleVertical.isEnabled()
        assert toggleHorizontal.isEnabled()
        assert toggleArabic.isEnabled()
        # Before entering Arabic mode, activate horizontal split.
        view.toggle_split(JSplitPane.HORIZONTAL_SPLIT)
        # Force full Arabic mode: it shouldn't be possible to toggle anything,
        # we want to always keep the Arabic pane.
        nammu.arabic(force=True)
        assert view.container.getOrientation() == JSplitPane.VERTICAL_SPLIT
        assert not toggleVertical.isEnabled()
        assert not toggleHorizontal.isEnabled()
        assert not toggleArabic.isEnabled()
        # Try adding text to the arabic area and toggling
        # horizontally/vertically while in an Arabic file.  Nothing should
        # happen and the text in the the arabic pane should be retained.
        for orientation in [JSplitPane.HORIZONTAL_SPLIT,
                            JSplitPane.VERTICAL_SPLIT]:
            arabic_area = nammu.atfAreaController.arabic_area
            arabic_text = u"في شتة"
            arabic_area.setText(arabic_text)
            view.toggle_split(orientation)
            assert view.container.getOrientation() == JSplitPane.VERTICAL_SPLIT
            assert not toggleVertical.isEnabled()
            assert not toggleHorizontal.isEnabled()
            assert not toggleArabic.isEnabled()
            assert view.arabic_area.getText() == arabic_text

    def test_title_bar(self, monkeypatch, nammu):
        """
        Test the content of the title bar.
        """
        monkeypatch.setattr(nammu, 'handleUnsaved', unsaved_patch)
        nammu.closeFile()
        assert nammu.view.getTitle() == "<New File> - Nammu"
        nammu.atfAreaController.edit_area.setText("Hello Mesopotamia")
        assert nammu.view.getTitle() == "(*) <New File> - Nammu"
        monkeypatch.setattr(JFileChooser, 'showDialog',
                            show_diag_patch)
        monkeypatch.setattr(JFileChooser, 'getSelectedFile',
                            selected_file_patch_arabic)
        nammu.openFile()
        assert (nammu.view.getTitle() ==
                "{} - Nammu".format(selected_file_patch_arabic(None)
                                    .getName()))
        nammu.atfAreaController.arabic_area.setText("Hello Mesopotamia")
        assert (nammu.view.getTitle() ==
                "(*) {} - Nammu".format(selected_file_patch_arabic(None)
                                        .getName()))
        nammu.closeFile()

    def test_config_dict(self, monkeypatch):
        """
        Test that `ConfigDict` throws an error if a key is not present.
        """
        monkeypatch.setattr(JOptionPane, 'showMessageDialog',
                            show_message_dialog)
        conf = ConfigDict('config.yaml', {'version': '0.2'})
        assert conf['version'] == '0.2'
        with pytest.raises(NammuException):
            conf['foo']

    def test_save_config_dict(self, tmpdir):
        """
        Test round-trip of saving a `ConfigDict` to disk and reading it back
        from file.
        """
        config_file = str(tmpdir.join('settings.yaml'))
        config = {'nammu': 1, 'author': "anu-belsunu"}
        config_dict = ConfigDict(config_file, config)
        save_yaml_config(config_dict, config_file)
        with open(config_file) as io:
            # We can't use the high level `get_yaml_config` function because it
            # prepends `resources/config/` to the path given in input.
            new_config_dict = yaml.safe_load(io)
        assert new_config_dict == config_dict
