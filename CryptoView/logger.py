from termcolor import colored, cprint


class Logger:
    def __init__(self, filename=None):
        self.filename = filename

    def standard(self, message):
        cprint("[-] " + message, 'white')
        if self.filename is not None:
            cprint("[-] " + message, 'white', file=self.filename)

    def alert(self, message):
        cprint("[x] " + message, 'red')
        if self.filename is not None:
            cprint("[x] " + message, 'red', file=self.filename)

    def info(self, message):
        cprint("[?] " + message, 'cyan')
        if self.filename is not None:
            cprint("[?] " + message, 'cyan', file=self.filename)

    def success(self, message):
        cprint("[*] " + message, 'green')
        if self.filename is not None:
            cprint("[*] " + message, 'green', file=self.filename)

    def warning(self, message):
        cprint("[!]" + message, 'yellow')
        if self.filename is not None:
            cprint("[!] " + message, 'yellow', file=self.filename)
