# -*- coding: utf-8 -*-
import json
import re

re_informatica = re.compile(
    r"(PROGRAMADORA?|INFORMATIC[AO]|DESARROLLO|SISTEMAS|PROGRAMACION)", re.IGNORECASE)
re_no_informatica = re.compile(
    r"(SUPERVISORA? DE SISTEMAS BASICOS)", re.IGNORECASE)

def parse_key(k):
    if isinstance(k, str) and k.isdigit():
        return int(k)
    return k


class Descripciones:

    def load():
        with open("data/descripciones.json", "r") as f:
            dt = json.load(f)
            return Descripciones(**dt)

    def save(self):
        with open("data/descripciones.json", "w") as f:
            f.write(json.dumps(self.__dict__, indent=4, sort_keys=True))

        for k, v in self.__dict__.items():
            values = set(v.values())
            with open("data/" + k.lower() + ".txt", "w") as f:
                for p in sorted(values):
                    f.write(p + "\n")

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            dt = {_k: _v for _k, _v in kwargs[k].items()}
            k = k[0].lower() + k[1:]
            setattr(self, k, dt)


class Puesto:

    def load():
        desc = Descripciones.load()
        with open("data/destinos.json", "r") as f:
            col = json.load(f, object_hook=Puesto.dict_to_puesto)
            for p in col:
                for k in desc.__dict__.keys():
                    k1 = "id" + k[0].upper() + k[1:]
                    k2 = "de" + k[0].upper() + k[1:]
                    if k1 in p.__dict__:
                        id = str(p.__dict__[k1])
                        dt = desc.__dict__[k]
                        if id is not None:
                            setattr(p, k2, dt.get(id, None))
                if p.provincia is not None:
                    p.deProvincia = desc.provincias[str(p.provincia)]
                else:
                    p.deProvincia = p.calcular_provincia(desc.provincias)
                p.deLocalidad = p.deResidencia.split(
                    "-")[-1] if p.deResidencia else None
            return col

    def save(col):
        with open("data/destinos.json", "w") as f:
            f.write(json.dumps(col, indent=4, sort_keys=True, cls=MyEncoder))

    def dict_to_puesto(obj):
        if not isinstance(obj, dict) or "idPuesto" not in obj:
            return obj
        p = Puesto()
        for k, v in obj.items():
            if isinstance(v, str) and v.isdigit():
                v = int(v)
            setattr(p, k, v)
        for k in Puesto(*range(25)).__dict__.keys():
            if k not in p.__dict__.keys():
                setattr(p, k, None)
        return p

    def __init__(self, *args):
        self.remove = set(("remove",))
        if len(args) == 0:
            return
        self.idMinisterio, \
            self.deMinisterio, \
            self.idCentroDirectivo, \
            self.deCentroDirectivo, \
            self.idUnidad, \
            self.deUnidad, \
            self.idResidencia, \
            self.idPuesto, \
            dePuestoCorta, \
            self.dePuesto, \
            self.nivel, \
            self.complemento, \
            self.idTipoPuesto, \
            self.idProvision, \
            self.idAdscripcionAdministrativa, \
            self.grupo, \
            self.idAdscripcionCuerpo, \
            self.idTitulacionAcademica, \
            self.idFormacionEspecifica, \
            self.pais, \
            self.provincia, \
            self.localidad, \
            self.idObservaciones, \
            self.af, \
            self.estado \
            = args
        if self.idResidencia and isinstance(self.idResidencia, str):
            self.pais, self.provincia, self.localidad = [
                int(i) for i in self.idResidencia.split("-")]
        if self.dePuesto is None:
            self.dePuesto = dePuestoCorta

    def calcular_provincia(self, provincias):
        if self.deCentroDirectivo and "CEUTA Y MELILLA" in self.deCentroDirectivo:
            return "Ceuta y Melilla"
        for prov in provincias.values():
            for v in prov.split("/"):
                v = v.split(",")[0].strip().upper()
                v = v.replace("Á", "A")
                v = v.replace("É", "E")
                v = v.replace("Í", "I")
                v = v.replace("Ó", "O")
                v = v.replace("Ú", "U")
                if (self.deCentroDirectivo and v in self.deCentroDirectivo) or (self.deUnidad and v in self.deUnidad):
                    return prov
                if (self.deResidencia and v in self.deResidencia):
                    return prov

    @property
    def order(self):
        return (self.deCentroDirectivo or "", self.deUnidad or "", self.deResidencia or "", self.dePuesto or "", self.nivel or -1, self.complemento or -1, self.grupo or "", self.pais or -1, self.provincia or -1, self.localidad or "")

    def isTAI(self, resto=None):
        if self.grupo is None or self.nivel is None or self.dePuesto is None:
            return False
        if "C1" not in self.grupo:
            return False
        if self.nivel < 15 or self.nivel > 18: #18 es más realista que 22
            return False
        if self.idProvision == "L":
            return False
        if not re_informatica.search(self.dePuesto) or re_no_informatica.search(self.dePuesto):
            if resto is not None:
                resto.add(self.dePuesto)
            return False
        return True


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if not isinstance(obj, Puesto):
            return super(MyEncoder, self).default(obj)
        cp = obj.__dict__.copy()
        for k in list(cp.keys()):
            if cp[k] is None or k in obj.remove:
                del cp[k]
        return cp


class Info:

    def __init__(self, puestos, descripciones):
        self.descripciones = descripciones
        self.puestos = puestos
        self.cur_ministerio = None
        self.pais = puestos[0].pais
        self.provincia = puestos[0].provincia
        self.deProvincia = puestos[0].deProvincia or "¿?¿?"

    @property
    def puestos_by_ministerio(self):
        puestos = sorted([p for p in self.puestos if p.idMinisterio ==
                          self.cur_ministerio], key=lambda i: i.order)
        return puestos

    @property
    def next_ministerio(self):
        ministerios = set([p.idMinisterio for p in self.puestos])
        for k, v in sorted(self.descripciones.ministerio.items(), key=lambda i: i[1]):
            k = int(k)
            if k in ministerios:
                self.cur_ministerio = k
                yield (k, v)
                
    @property
    def estado_ministerio(self):
        if "V" in set([p.estado for p in self.puestos if p.idMinisterio == self.cur_ministerio]):
            return "V"
        return "NV"
        
