from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, BooleanProperty, StringProperty, DictProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder


class ServerPopup(Popup):
    name = StringProperty('')
    data = DictProperty({'host': '', 'port': 6667, 'nick': 'jrandom',
                         'password': '', 'auth_nickserv': False,
                         'scripts': '', 'autojoin': []})


class ServerBox(BoxLayout):
    name = StringProperty('')


class NameButton(Button):
    __events__ = ('on_long_press', )

    long_press_delay = NumericProperty(2)
    long_pressed = BooleanProperty(False)

    def on_state(self, instance, value):
        if value == 'down':
            self._clockev = Clock.schedule_once(self._do_long_press,
                                                self.long_press_delay)
        else:
            self._clockev.cancel()

    def _do_long_press(self, dt):
        self.dispatch('on_long_press')
        self.long_pressed = True

    def on_long_press(self, *args):
        pass


class ConfirmButton(Button):
    is_sure = BooleanProperty(False)

    def on_state(self, instance, value):
        if value == 'normal' and not self.is_sure:
            Animation(background_color=(1, 0.2, 0.2, 1),
                      duration=0.2).start(self)
            Clock.schedule_once(self._restore, 5)
            self.is_sure = True

    def _restore(self, dt):
        Animation(background_color=(1, 1, 1, 1)).start(self)
        self.is_sure = False


class ScreenMain(Screen):
    Builder.load_string('''
#:import Factory kivy.factory.Factory

<ServerScroll@ScrollView>:
  canvas.before:
    Color:
      rgba: (0.5, 0.5, 0.5, 1)
    Rectangle:
      pos: self.pos
      size: self.size

<ServerBox>:
  spacing: dp(5)

  NameButton:
    id: servername
    text: root.name
    font_size: sp(12)
    on_long_press:
      Factory.ServerPopup(name=root.name, \
                          data=app.servers.get(root.name)).open()
    on_release:
      not self.long_pressed and app.init_connection(root.name)
      self.long_pressed = False

  Button:
    text: 'Stop'
    font_size: sp(12)
    width: dp(50)
    size_hint_x: None
    on_release: app.close_connection(root.name)

  ConfirmButton:
    text: 'Delete'
    font_size: sp(12)
    width: dp(50)
    size_hint_x: None
    on_release:
      self.is_sure and (app.close_connection(root.name), \
                        app.del_server(root))


<ScreenMain>:
  name: 'ScreenMain'

  BoxLayout:
    orientation: 'vertical'

    ActionBar:
      pos_hint: {'top': 1}

      ActionView:
        ActionPrevious:
          app_icon: 'data/icon.png'
          title: 'irc1'
          on_release: app.go_back()

        ActionButton:
          text: 'Add server'
          icon: 'data/plus-8x.png'
          on_release: Factory.ServerPopup().open()

        ActionOverflow:
          ActionButton:
            text: 'Disconnect all'
            on_release: app.disconnect_all()

    ServerScroll:
      id: serverscroll

      GridLayout:
        id: servers
        cols: 1
        padding: dp(10)
        spacing: dp(10)
        row_default_height: dp(45)
        height: self.minimum_height
        size_hint_y: None


<LineInput@TextInput>:
  multiline: False

<ServerPopup>:
  title: 'Add an IRC server'
  size_hint_y: 0.8

  BoxLayout:
    orientation: 'vertical'

    GridLayout:
      cols: 2
      padding: dp(5)
      spacing: dp(5)
      row_default_height: dp(30)

      Label:
        text: 'Address'
      LineInput:
        id: host
        text: root.data['host']
        disabled: True if root.name else False

      Label:
        text: 'Port'
      LineInput:
        id: port
        text: str(root.data['port'])
        disabled: True if root.name else False

      Label:
        text: 'Nickname'
      LineInput:
        id: nick
        text: root.data['nick']

      Label:
        text: 'Password'
      LineInput:
        id: password
        text: root.data['password']
        password: True

      Label:
        text: 'Use NickServ'
      CheckBox:
        id: auth_nickserv
        active: root.data['auth_nickserv']

      Label:
        text: 'Scripts to send'
      LineInput:
        id: scripts
        text: root.data['scripts']

      Label:
        text: 'Join channels'
      LineInput:
        id: autojoin
        text: ','.join(root.data['autojoin'])

    BoxLayout:

      Button:
        text: 'Cancel'
        height: dp(45)
        size_hint_y: None
        on_release: root.dismiss()

      Button:
        text: 'OK'
        height: dp(45)
        size_hint_y: None
        on_release:
          app.update_or_add_server(root, root.name)
          root.dismiss()
''')
