from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.lang import Builder


class ChatLabel(Label):
    pass


class ScreenConversation(Screen):
    Builder.load_string('''
#:import webbrowser webbrowser

<Spinner>:
  font_size: sp(14)

<SpinnerOption>:
  font_size: sp(14)
  background_color: (0.8, 0.8, 0.8, 1)

<ChatScroll@ScrollView>:
  canvas.before:
    Color:
      rgba: (0.9, 0.9, 0.9, 1)
    Rectangle:
      pos: self.pos
      size: self.size

<ChatLabel>:
  color: (0.1, 0.1, 0.1, 1)
  opacity: 0.2
  font_size: sp(12)
  text_size: (self.width, None)
  height: self.texture_size[1]
  size_hint_y: None
  markup: True
  on_ref_press: webbrowser.open(args[1])


<ScreenConversation>:
  name: 'ScreenConversation'

  BoxLayout:
    orientation: 'vertical'
    canvas.before:
      Color:
        rgba: (0.6, 0.6, 0.6, 1)
      Rectangle:
        size: self.size
        pos: self.pos

    ActionBar:
      pos_hint: {'top': 1}

      ActionView:

        ActionPrevious:
          title: root.name
          app_icon: 'data/icon.png'
          on_release: app.go_back()

        ActionButton:
          text: 'Disconnect'
          icon: 'data/power-8x.png'
          on_release: app.close_connection(root.name)

        ActionOverflow:
          ActionButton:
            text: 'Clear logs'
            on_release: chatlog.clear_widgets()

    Spinner:
      id: channel
      text: 'No channel'
      values: ['No channel']
      height: dp(45)
      size_hint_y: None
      on_text:
        app.change_channel(root.name, \
                           str(self.text) if self.text != 'No channel' else '')

    ChatScroll:
      id: chatscroll

      GridLayout:
        id: chatlog
        cols: 1
        spacing: dp(2)
        padding: dp(5)
        height: self.minimum_height
        size_hint_y: None

    BoxLayout:
      height: dp(30)
      size_hint_y: None

      Label:
        id: nick
        text: 'jrandom'
        font_size: sp(15)
        padding: (dp(5), 0)
        width: self.texture_size[0]
        size_hint_x: None

      TextInput:
        id: message
        font_size: sp(15)
        padding: (dp(5), 0.5 * (self.height - self.line_height))
        hint_text: 'Type text or /join, /part, /msg'
        multiline: False
        on_text_validate:
          app.send_msg(root.name, str(self.text))
          self.text = ''

      Button:
        text: 'SEND'
        font_size: sp(15)
        size_hint_x: 0.3
        on_release:
          app.send_msg(root.name, str(message.text))
          message.text = ''
''')

