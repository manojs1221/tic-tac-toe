import os
import re
import random

# --- THE FIX FOR ACER/WINDOWS OPENGL ERRORS ---
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
os.environ['KIVY_GL_CORE'] = '0'
os.environ['KIVY_GRAPHICS'] = 'gles'
os.environ['KIVY_BCKND_OPTS'] = 'angle_renderer=d3d11'

from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '700')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, OptionProperty
from kivy.clock import Clock

# --- UI LAYOUT ---
KV = '''
<TicTacToeRoot>:
    orientation: 'horizontal'
    padding: 15
    spacing: 15
    canvas.before:
        Color:
            rgba: (0.05, 0.05, 0.1, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.7
        spacing: 10
        
        BoxLayout:
            size_hint_y: 0.25
            spacing: 15
            
            BoxLayout:
                orientation: 'vertical'
                spacing: 5
                
                # --- GAME MODE SECTION ---
                Label:
                    text: "GAME MODE"
                    font_size: '14sp'
                    bold: True
                    size_hint_y: None
                    height: '30dp'
                BoxLayout:
                    spacing: 2
                    size_hint_y: None
                    height: '40dp'
                    ToggleButton:
                        text: 'AUTO (CPU)'
                        group: 'mode'
                        state: 'down' if root.auto_mode else 'normal'
                        on_release: root.auto_mode = True
                    ToggleButton:
                        text: 'MANUAL (PVP)'
                        group: 'mode'
                        state: 'down' if not root.auto_mode else 'normal'
                        on_release: root.auto_mode = False
                
                # --- DYNAMIC DIFFICULTY SECTION ---
                # This box appears/disappears based on auto_mode
                BoxLayout:
                    orientation: 'vertical'
                    spacing: 5
                    opacity: 1 if root.auto_mode else 0
                    disabled: not root.auto_mode
                    size_hint_y: 1 if root.auto_mode else 0
                    
                    Label:
                        text: "CPU DIFFICULTY"
                        font_size: '14sp'
                        bold: True
                    BoxLayout:
                        spacing: 2
                        ToggleButton:
                            text: 'Easy'
                            group: 'diff'
                            state: 'down' if root.difficulty == 'Easy' else 'normal'
                            on_release: root.difficulty = 'Easy'
                        ToggleButton:
                            text: 'Med'
                            group: 'diff'
                            state: 'down' if root.difficulty == 'Medium' else 'normal'
                            on_release: root.difficulty = 'Medium'
                        ToggleButton:
                            text: 'Hard'
                            group: 'diff'
                            state: 'down' if root.difficulty == 'Hard' else 'normal'
                            on_release: root.difficulty = 'Hard'
            
            BoxLayout:
                orientation: 'vertical'
                canvas.before:
                    Color:
                        rgba: (0.1, 0.1, 0.2, 1)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [10,]
                Label:
                    text: f"X Score: {root.score_x}"
                    font_size: '20sp'
                    bold: True
                    color: (0.3, 0.6, 1, 1)
                Label:
                    text: f"O Score: {root.score_o}"
                    font_size: '20sp'
                    bold: True
                    color: (1, 0.6, 0.3, 1)

        Label:
            text: root.status_text
            font_size: '28sp'
            bold: True
            size_hint_y: 0.1
            color: (1, 1, 1, 1)

        GridLayout:
            id: board
            cols: 3
            rows: 3
            spacing: 8

        BoxLayout:
            size_hint_y: 0.12
            spacing: 10
            Button:
                text: "NEW ROUND"
                background_normal: ''
                background_color: (0.2, 0.5, 0.2, 1)
                on_release: root.reset_board()
            Button:
                text: "RESET ALL"
                background_normal: ''
                background_color: (0.6, 0.2, 0.2, 1)
                on_release: root.reset_all()

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.3
        canvas.before:
            Color:
                rgba: (0.1, 0.1, 0.15, 1)
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "MOVE LOG"
            size_hint_y: 0.05
            bold: True
        ScrollView:
            Label:
                id: history_label
                text: root.history_text
                size_hint_y: None
                height: self.texture_size[1]
                halign: 'left'
                valign: 'top'
                padding: (10, 10)
                text_size: self.width, None
'''

class TicTacToeRoot(BoxLayout):
    status_text = StringProperty("X's Turn")
    history_text = StringProperty("")
    score_x = NumericProperty(0)
    score_o = NumericProperty(0)
    auto_mode = BooleanProperty(True)
    difficulty = OptionProperty('Hard', options=['Easy', 'Medium', 'Hard'])
    current_player = "X"
    game_over = False
    move_count = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.create_board)

    def create_board(self, dt=None):
        self.ids.board.clear_widgets()
        for i in range(9):
            btn = Button(
                text="", font_size='40sp', bold=True,
                background_normal='', background_color=(0.12, 0.12, 0.18, 1),
                on_release=self.on_click
            )
            btn.idx = i
            self.ids.board.add_widget(btn)

    def on_click(self, button):
        if button.text != "" or self.game_over: return
        # Prevent manual clicking for 'O' if it's CPU's turn
        if self.auto_mode and self.current_player == "O": return
        self.perform_move(button)

    def perform_move(self, button):
        self.move_count += 1
        button.text = self.current_player
        button.background_color = (0.3, 0.6, 1, 1) if self.current_player == "X" else (1, 0.6, 0.3, 1)
        
        # Log using Regex
        raw_log = f"M{self.move_count}: {self.current_player} @ Sq {button.idx}"
        formatted_log = re.sub(r'M(\d):', r'M0\1:', raw_log)
        self.history_text = formatted_log + "\n" + self.history_text

        btns = list(reversed(self.ids.board.children))
        board_state = [b.text for b in btns]
        win_path = self.get_win_path(board_state)
        
        if win_path:
            self.status_text = f"{self.current_player} is the Winner!"
            for index in win_path: btns[index].background_color = (0.2, 0.8, 0.2, 1)
            if self.current_player == "X": self.score_x += 1
            else: self.score_o += 1
            self.game_over = True
        elif "" not in board_state:
            self.status_text = "It's a Draw!"
            self.game_over = True
        else:
            self.current_player = "O" if self.current_player == "X" else "X"
            if self.auto_mode and self.current_player == "O":
                self.status_text = "CPU is thinking..."
                Clock.schedule_once(self.cpu_move, 0.5)
            else:
                self.status_text = f"{self.current_player}'s Turn"

    def cpu_move(self, dt):
        if self.game_over: return
        btns = list(reversed(self.ids.board.children))
        empty_indices = [i for i, b in enumerate(btns) if b.text == ""]
        if not empty_indices: return

        idx = None
        if self.difficulty == 'Easy':
            idx = random.choice(empty_indices)
        elif self.difficulty == 'Medium':
            idx = self.find_winning_move(btns, "O")
            if idx is None: idx = random.choice(empty_indices)
        else: # Hard
            idx = self.find_winning_move(btns, "O") or self.find_winning_move(btns, "X")
            if idx is None: idx = random.choice(empty_indices)

        if idx is not None: self.perform_move(btns[idx])

    def find_winning_move(self, btns, char):
        paths = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for p in paths:
            line = [btns[p[0]].text, btns[p[1]].text, btns[p[2]].text]
            if line.count(char) == 2 and line.count("") == 1:
                return p[line.index("")]
        return None

    def get_win_path(self, b):
        paths = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for p in paths:
            if b[p[0]] == b[p[1]] == b[p[2]] != "": return p
        return None

    def reset_board(self):
        self.game_over = False
        self.current_player = "X"
        self.move_count = 0
        self.status_text = "X's Turn"
        for child in self.ids.board.children:
            child.text = ""
            child.background_color = (0.12, 0.12, 0.18, 1)

    def reset_all(self):
        self.score_x = 0
        self.score_o = 0
        self.history_text = ""
        self.reset_board()

class TicTacToeApp(App):
    def build(self):
        Builder.load_string(KV)
        return TicTacToeRoot()

if __name__ == '__main__':
    TicTacToeApp().run()
