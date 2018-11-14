def blue(txt):
    return '[color=#000088]%s[/color]' % txt

def green(txt):
    return '[color=#009c00]%s[/color]' % txt

def red(txt):
    return '[color=#ff0000]%s[/color]' % txt

def purple(txt):
    return '[color=#a500a5]%s[/color]' % txt

def cyan(txt):
    return '[color=#009c9c]%s[/color]' % txt

def grey(txt):
    return '[color=#555555]%s[/color]' % txt

def bold(txt):
    return '[b]%s[/b]' % txt

def italic(txt):
    return '[i]%s[/i]' % txt

def under(txt):
    return '[u]%s[/u]' % txt

def url(txt):
    return '[ref=%s]%s[/ref]' % (txt, under(blue(txt)))

def mute(txt):
    return italic(grey(txt))
