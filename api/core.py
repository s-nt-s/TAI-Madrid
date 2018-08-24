# -*- coding: utf-8 -*-
import json
import re

from .util import yaml_from_file

re_informatica = re.compile(
    r"\b(PROGRAMADORA?|INFORMATIC[AO]|DESARROLLO|SISTEMAS|PROGRAMACION|ADMINISTRADORA? DE RED|TECNIC[AO] DE GESTION DE RED|TECNIC[AO] DE REDES INFORMATICAS)\b", re.IGNORECASE)
re_no_informatica = re.compile(
    r"(SUPERVISORA? DE SISTEMAS BASICOS)", re.IGNORECASE)


def parse_key(k):
    if isinstance(k, str) and k.isdigit():
        return int(k)
    return k


class Organismo:

    def load(name="organismos"):
        with open("data/" + name + ".json", "r") as f:
            col = json.load(f, object_hook=Organismo.dict_to_organismo)
            return col

    def save(col, name="organismos"):
        col = sorted(col, key=lambda o: (o.rcp or 999999, o.idOrganismo))
        with open("data/" + name + ".json", "w") as f:
            f.write(json.dumps(col, indent=4, sort_keys=True, cls=MyEncoder))

    def dict_to_organismo(obj):
        if not isinstance(obj, dict) or "idOrganismo" not in obj:
            return obj
        p = Organismo(**obj)
        return p

    def __init__(self, idOrganismo, deOrganismo=None, deDireccion=None, idPadres=None, idRaiz=None, idUnidOrganica=None, latlon=None, **kwargs):
        self.remove = {'remove', 'rcpPadres', 'rcp', 'rcpPadres', 'version'}
        self.idOrganismo = idOrganismo
        self.deOrganismo = deOrganismo
        self.deDireccion = deDireccion
        self.idPadres = idPadres or set()
        self.idRaiz = idRaiz
        self.rcp = None
        self.rcpPadres = set()
        self.idUnidOrganica = idUnidOrganica
        self.latlon = latlon
        if isinstance(self.idPadres, list):
            self.idPadres = set(self.idPadres)
        if self.idOrganismo and self.idOrganismo.startswith("E0"):
            self.rcp = int(self.idOrganismo[2:-2])
            self.version = int(self.idOrganismo[-2:])
        if self.idPadres:
            self.rcpPadres = set([int(i[2:-2])
                                  for i in self.idPadres if i.startswith("E0")])

    @property
    def nombre(self):
        return self.deOrganismo.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


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

    def load(name="destinos_tai"):
        desc = Descripciones.load()
        with open("data/" + name + ".json", "r") as f:
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
                if p.provincia is not None and str(p.provincia) in desc.provincias:
                    p.deProvincia = desc.provincias[str(p.provincia)]
                else:
                    p.deProvincia = p.calcular_provincia(desc.provincias)
                p.deLocalidad = p.deResidencia.split(
                    "-")[-1] if p.deResidencia else None
            return col

    def save(col, name="destinos_tai"):
        col = sorted(col, key=lambda o: o.idPuesto)
        with open("data/" + name + ".json", "w") as f:
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
        self.ranking = None

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

    def isTAI(self, puesto_ok=None, puesto_ko=None):
        if self.grupo is None or self.nivel is None or self.dePuesto is None:
            return False
        if "C1" not in self.grupo:
            return False
        if self.nivel < 15 or self.nivel > 18:  # 18 es más realista que 22
            return False
        if not re_informatica.search(self.dePuesto) or re_no_informatica.search(self.dePuesto):
            if puesto_ko is not None:
                puesto_ko.add(self.dePuesto)
            return False
        if puesto_ok is not None:
            puesto_ok.add(self.dePuesto)
        return True


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return super(MyEncoder, self).default(list(sorted(obj)))
        if not isinstance(obj, Puesto) and not isinstance(obj, Organismo):
            return super(MyEncoder, self).default(obj)
        cp = obj.__dict__.copy()
        _remove = cp.get("remove", set())
        for k in list(cp.keys()):
            v = cp[k]
            if k in _remove or v is None:
                del cp[k]
            elif isinstance(v, set):
                if len(v) == 0:
                    del cp[k]
                else:
                    cp[k] = list(sorted(v))
        return cp


class Info:

    def __init__(self, puestos, descripciones, organismos):
        self.descripciones = descripciones
        self.puestos = puestos
        self.pais = puestos[0].pais
        self.provincia = puestos[0].provincia
        self.deProvincia = puestos[0].deProvincia or "¿?¿?"
        self.organismos = organismos
        self.arreglos = yaml_from_file("data/arreglos.yml")

        self.cur_ministerio = None
        self.cur_centrodirectivo = None
        self.cur_unidad = None

    def _find_org(self, codigo, nombre=None, padre=None):
        if codigo in self.arreglos:
            print (codigo, end=" -> ")
            codigo = self.arreglos[codigo]
            print (codigo)
            if isinstance(codigo,str):
                return self.organismos[codigo]
        org = self.organismos.get(codigo, None)
        if org is None and nombre is not None and padre is not None:
            codigos = set()
            nombre = nombre.lower()
            for o in self.organismos.values():
                if o.rcpPadres:
                    for rcp in o.rcpPadres:
                        if padre == rcp and nombre in (o.deOrganismo.lower(), o.nombre):
                            codigos.add(o.rcp)
            if len(codigos) == 1:
                print (codigo, end=" --> ")
                codigo = codigos.pop()
                print (codigo)
                return self.organismos[codigo]
        return org

    def find_org(self, codigo, nombre=None, padre=None):
        org = self._find_org(codigo, nombre=nombre, padre=padre)
        if not org or org.idUnidOrganica:
            return org

        deDireccion = None
        if org.deDireccion:
            deDireccion = org.deDireccion.replace("Avda ", "Avenida").split(",")[0].lower()
        orgs = set()
        for o in self.organismos.values():
            if o != org and o.nombre == org.nombre:
                orgs.add(o)
        if deDireccion and len(orgs)>1:
            for o in list(orgs):
                if not o.deDireccion or not o.deDireccion.lower().startswith(deDireccion):
                    orgs.remove(o)
        if len(orgs)==1:
            o = orgs.pop()
            if o.idUnidOrganica:
                print (str(codigo) + " ---> "+ str(o.idOrganismo))
                print (org.deDireccion)
                print (o.deDireccion)
                return o
        return org

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
                org = self.find_org(self.cur_ministerio, v)
                yield (k, v, org)

    @property
    def next_centrodirectivo(self):
        centrodirectivos = set(
            [p.idCentroDirectivo for p in self.puestos if p.idMinisterio == self.cur_ministerio])
        for k, v in sorted(self.descripciones.centroDirectivo.items(), key=lambda i: i[1]):
            k = int(k)
            if k in centrodirectivos:
                self.cur_centrodirectivo = k
                org = self.find_org(self.cur_centrodirectivo,
                                    v, self.cur_ministerio)
                yield (k, v, org)
        self.cur_centrodirectivo = None
        if next(self.next_unidad, None):
            yield (-1, "Sin centro directivo", None)

    @property
    def next_unidad(self):
        unidades = set([p.idUnidad for p in self.puestos if p.idMinisterio ==
                        self.cur_ministerio and p.idCentroDirectivo == self.cur_centrodirectivo])
        for k, v in sorted(self.descripciones.unidad.items(), key=lambda i: i[1]):
            k = int(k)
            if k in unidades:
                self.cur_unidad = k
                org = self.find_org(
                    self.cur_unidad, v, self.cur_centrodirectivo or self.cur_ministerio)
                yield (k, v, org)

    @property
    def estado_ministerio(self):
        if "V" in set([p.estado for p in self.puestos if p.idMinisterio == self.cur_ministerio]):
            return "V"
        return "NV"
