from kivy.app import App


def pause_app():
    '''
    '''
    from kivy.utils import platform
    if platform == 'android':
        from jnius import cast
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        currentActivity.moveTaskToBack(True)
    else:
        app = App.get_running_app()
        app.stop()


def _hook_keyboard(window, key, *largs):
    app = App.get_running_app()
    if key == 27:
        # do what you want,
        # return True for stopping the propagation to widgets.
        # indicating we consumed the event.
        app.go_back()
        return True


def hook_keyboard(*args):
    from kivy.base import EventLoop
    EventLoop.window.bind(on_keyboard=_hook_keyboard)

