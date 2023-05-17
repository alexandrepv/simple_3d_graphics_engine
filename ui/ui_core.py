import json

import bs4
from bs4 import BeautifulSoup
import warnings
from bs4 import GuessedAtParserWarning
warnings.filterwarnings('ignore', category=GuessedAtParserWarning)

from ui.ui_font import UIFont
from ui.widgets.ui_widget import UIWidget
from ui.widgets.ui_window import UIWindow
from ui.widgets.ui_row import UIRow
from ui.widgets.ui_column import UIColumn
from ui.widgets.ui_button import UIButton

import ui.ui_constants as constants

class UICore:

    def __init__(self):

        self.windows = []
        self.font = UIFont()

    def load(self, blueprint_xml_fpath: str, theme_json_fpath: str) -> None:

        """
        Loads current UI described in the ui blueprint
        :param blueprint_xml_fpath:
        :param theme_json_fpath:
        :return: None
        """

        # Load UI theme
        with open(theme_json_fpath, 'r') as file:
            # Load theme
            self.theme = json.load(file)

            # Load font here
            self.font.load(ttf_fpath=self.theme['font']['filepath'])

        # Load UI window blueprint
        with open(blueprint_xml_fpath) as file:
            root_soup = BeautifulSoup(file.read(), features="lxml")

            # Find window root node - there should be only one
            ui_soup = root_soup.find(constants.KEY_ELEMENT_UI)
            if ui_soup is None:
                raise ValueError(f"[ERROR] Could not find UI root '<{constants.KEY_ELEMENT_UI}>'")

            for window_soup in root_soup.find_all(constants.KEY_ELEMENT_WINDOW):
                window_widget = UIWindow(
                    widget_id=window_soup.attrs.get(constants.KEY_ATTRS_ID, 'no_id'),
                    width_str=window_soup.attrs.get(constants.KEY_ATTRS_WIDTH, '100%'),
                    height_str=window_soup.attrs.get(constants.KEY_ATTRS_HEIGHT, '100%'))

                self.windows.append(window_widget)
                self.build_widget_tree(parent_soup=window_soup, parent_widget=window_widget)

    def build_widget_tree(self, parent_soup: BeautifulSoup, parent_widget: UIWidget, level=0):

        level += 1

        for child_soup in parent_soup.findChildren(recursive=False):
            new_widget = None

            if constants.KEY_ATTRS_ID not in child_soup.attrs:
                raise AttributeError(f"[ERROR] Missing widget ID on {child_soup.attrs.name} widget")

            if child_soup.name == constants.KEY_ELEMENT_COLUMN:
                new_widget = self.soup2ui_column(soup=child_soup, level=level)
                parent_widget.add_child_widget(widget=new_widget)

            if child_soup.name == constants.KEY_ELEMENT_ROW:
                new_widget = self.soup2ui_row(soup=child_soup, level=level)
                parent_widget.add_child_widget(widget=new_widget)

            if child_soup.name == constants.KEY_ELEMENT_BUTTON:
                new_widget = self.soup2ui_button(soup=child_soup, level=level)
                parent_widget.add_child_widget(widget=new_widget)

            if new_widget is None:
                raise ValueError(f"[ERROR] Widget type {child_soup.name} is not supported")

            self.build_widget_tree(parent_soup=child_soup, parent_widget=new_widget, level=level)

    @staticmethod
    def soup2ui_column(soup: BeautifulSoup, level: int) -> UIColumn:
        width_str = soup.attrs.get(constants.KEY_ATTRS_WIDTH, '100%')
        height_str = soup.attrs.get(constants.KEY_ATTRS_HEIGHT, '100%')
        spacing = soup.attrs.get(constants.KEY_ATTRS_SPACING, constants.DEFAULT_SPACING_COLUMN)
        return UIColumn(
            widget_id=soup.attrs[constants.KEY_ATTRS_ID],
            width_str=width_str,
            height_str=height_str,
            spacing=float(spacing),
            level=level)

    @staticmethod
    def soup2ui_row(soup: BeautifulSoup, level: int) -> UIRow:
        width_str = soup.attrs.get(constants.KEY_ATTRS_WIDTH, '100%')
        height_str = soup.attrs.get(constants.KEY_ATTRS_HEIGHT, '100%')
        spacing = soup.attrs.get(constants.KEY_ATTRS_SPACING, constants.DEFAULT_SPACING_ROW)
        return UIRow(
            widget_id=soup.attrs[constants.KEY_ATTRS_ID],
            width_str=width_str,
            height_str=height_str,
            spacing=float(spacing),
            level=level)

    @staticmethod
    def soup2ui_button(soup: BeautifulSoup, level: int) -> UIButton:
        width_str = soup.attrs.get(constants.KEY_ATTRS_WIDTH, '100%')
        height_str = soup.attrs.get(constants.KEY_ATTRS_HEIGHT, '100%')
        text = 'No text' if len(soup.text) == 0 else soup.text
        return UIButton(
            widget_id=soup.attrs[constants.KEY_ATTRS_ID],
            width_str=width_str,
            height_str=height_str,
            text=text,
            level=level)

    def update_dimensions(self):
        for window in self.windows:
            window.update_dimensions()

    def update_position(self):
        for window in self.windows:
            window.update_positions()

    def draw(self):
        """
        Generate all render commands and add them to the drawlist. The drawlist will
        group them according to thei scissor requirements.

        IDEA: Maybe create a dicitonary with scissors as tuples

         - render commandas are tuples (fast to generate)
         

        :return:
        """
        pass


    # =======================================================
    #                       DEBUG
    # =======================================================

    def print_widget_tree(self):
        """
        Prints current UI structure on the terminal for debugging purposes

        :return:
        """

        def recursive_print(widget: UIWidget):
            spaces = ' ' * (widget.level * 2)
            print(f'{spaces}> {widget._widget_type} : {widget._id} ({widget.width_pixels}, {widget.height_pixels}) [level {widget.level}]')
            for child_widget in widget.children:
                recursive_print(child_widget)

        for window in self.windows:
            recursive_print(window)