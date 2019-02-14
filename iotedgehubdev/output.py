# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import click


class Output:

    def info(self, text, suppress=False):
        if not suppress:
            self.echo(text, color='yellow')

    def status(self, text):
        self.info(text)
        self.line()

    def prompt(self, text):
        self.echo(text, color='white')

    def warning(self, text):
        self.echo("WARNING: " + text, color='yellow')

    def error(self, text):
        self.echo("ERROR: " + text, color='red', err=True)

    def header(self, text, suppress=False):

        if not suppress:
            self.line()
            s = "======== {0} ========".format(text).upper()
            m = "=" * len(s)
            self.echo(m, color='white')
            self.echo(s, color='white')
            self.echo(m, color='white')
            self.line()

    def param(self, text, value, status, suppress):
        if value and not suppress:
            self.header("SETTING " + text)
            self.status(status)

    def footer(self, text, suppress=False):
        if not suppress:
            self.info(text.upper())
            self.line()

    def procout(self, text):
        self.echo(text, dim=True)

    def line(self):
        self.echo(text="")

    def echo(self, text, color="", dim=False, err=False):
        try:
            click.secho(text, fg=color, dim=dim, err=err)
        except Exception:
            print(text)
