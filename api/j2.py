import os

from jinja2 import Environment, FileSystemLoader


def minus(a, b):
    if a and b in a:
        a = set(a)
        a.remove(b)
    return a


def money(value, rounded=10, dotted=True):
    value = int(value / rounded)*rounded
    if dotted:
        value = "{:,.0f}".format(value).replace(",", ".")
    return value


class Jnj2():

    def __init__(self, origen, destino, pre=None, post=None):
        self.j2_env = Environment(
            loader=FileSystemLoader(origen), trim_blocks=True)
        self.j2_env.globals['minus'] = minus
        self.j2_env.filters['money'] = money
        self.destino = destino
        self.pre = pre
        self.post = post

    def save(self, template, destino=None, parse=None, **kwargs):
        if destino is None:
            destino = template
        out = self.j2_env.get_template(template)
        html = out.render(**kwargs)
        if self.pre:
            html = self.pre(html, **kwargs)
        if parse:
            html = parse(html, **kwargs)
        if self.post:
            html = self.post(html, **kwargs)

        destino = self.destino + destino
        directorio = os.path.dirname(destino)

        if not os.path.exists(directorio):
            os.makedirs(directorio)

        with open(destino, "wb") as fh:
            fh.write(bytes(html, 'UTF-8'))
        return html
