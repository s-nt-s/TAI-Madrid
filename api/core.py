# -*- coding: utf-8 -*-
import json
import os
import re

from .util import yaml_from_file

re_informatica = re.compile(
    r"\b(PROGRAMADORA?|INFORMATIC[AO]|DESARROLLO|SISTEMAS|PROGRAMACION|ADMINISTRADORA? DE RED|TECNIC[AO] DE GESTION DE RED|TECNIC[AO] DE REDES INFORMATICAS|OPERADOR/?A? (ESPECIALISTA|DE CONSOLA|PERIFERICO)|ADMINISTRADOR/?A? DEL SARTIDO)\b", re.IGNORECASE)
re_no_informatica = re.compile(
    r"(SUPERVISORA? DE SISTEMAS BASICOS)", re.IGNORECASE)

re_postCode = re.compile(r"\b([0-5]\d{4})\b")

re_guion = re.compile(r"\s*-\s*")
re_paren = re.compile(r"\(.*$")


def parse_key(k):
    if isinstance(k, str) and k.isdigit():
        return int(k)
    return k


def simplificar(s):
    return s.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def simplificar_dire(deDireccion):
    if deDireccion is None:
        return None
    deDireccion = deDireccion.replace("-", " ")
    #deDireccion = deDireccion.split(",")[0]
    deDireccion = deDireccion.lower()
    deDireccion = deDireccion.replace("avda ", "avenida ")
    deDireccion = deDireccion.replace("avda. ", "avenida ")
    deDireccion = deDireccion.replace("av. ", "avenida ")
    deDireccion = deDireccion.replace("pque ", "parque ")

    return deDireccion


class Organismo:

    def load(name="organismos", arregla_direcciones=None):
        fn = name if os.path.isfile(name) else "datos/" + name + ".json"
        with open(fn, "r") as f:
            col = json.load(f, object_hook=Organismo.dict_to_organismo)
            if arregla_direcciones:
                for o in col:
                    info = arregla_direcciones.get(o.deDireccion, None)
                    if info is not None:
                        o.latlon = info[0]
                        o.set_lugar(info[1])
            return col

    def save(col, name="organismos", arregla_direcciones=None):
        fn = name if os.path.isfile(name) else"datos/" + name + ".json"
        if arregla_direcciones:
            for o in col:
                info = arregla_direcciones.get(o.deDireccion, None)
                if info is not None:
                    o.latlon = info[0]
                    o.set_lugar(info[1])
        with open(fn, "w") as f:
            f.write(Organismo.to_json(col))

    def dict_to_organismo(obj):
        if not isinstance(obj, dict) or "idOrganismo" not in obj:
            return obj
        p = Organismo(**obj)
        return p

    def to_json(col):
        if isinstance(col, list) or isinstance(col, set):
            col = sorted(col, key=lambda o: (o.rcp or 999999, o.idOrganismo))
        return json.dumps(col, indent=4, sort_keys=True, cls=MyEncoder)

    def __init__(self, idOrganismo, deOrganismo=None, deDireccion=None, postCode=None, idPadres=None, idRaiz=None, idUnidOrganica=None, latlon=None, codigos=None, isCsic=None, idCsic=None, idProvincia=None, desaparecido=None, **kwargs):
        self.remove = {'remove', 'nombres', 'rcp',
                       'version', 'puestos', 'deProvincia'}
        if isinstance(idPadres, list):
            idPadres = set(idPadres)
        if isinstance(codigos, list):
            codigos = set(codigos)
        if deDireccion and deDireccion.startswith("Otros Aeropuerto Barajas"):
            deDireccion = deDireccion[6:]
        self.idOrganismo = idOrganismo
        self.idUnidOrganica = idUnidOrganica
        self.deOrganismo = deOrganismo
        self.idPadres = idPadres or set()
        self.codigos = codigos or set()
        self.puestos = set()
        self.idRaiz = idRaiz
        self.latlon = latlon
        self.nombres = None
        self.rcp = None
        self.version = None
        self.isCsic = isCsic
        self.idCsic = idCsic
        self.deProvincia = None
        self.desaparecido = desaparecido
        self.set_lugar(deDireccion, postCode, idProvincia)
        if isinstance(self.idOrganismo, str) and self.idOrganismo.startswith("E0"):
            self.rcp, self.version = int(
                self.idOrganismo[2:-2]), int(self.idOrganismo[-2:])
        self.genera_codigos()
        self.genera_nombres()

    def get_rcp(self):
        if self.rcp is not None:
            return self.rcp
        self.genera_codigos()
        for c in self.codigos:
            if isinstance(c, int):
                return c
        return None

    def set_lugar(self, direccion, codigo_postal=None, provincia=None):
        self.deDireccion = direccion
        self.postCode = codigo_postal
        self.idProvincia = provincia
        if self.postCode is None and self.deDireccion:
            m = re_postCode.search(self.deDireccion)
            if m:
                self.postCode = m.group(1)
        if self.idProvincia is None and self.postCode and self.postCode.isdigit():
            self.idProvincia = int(self.postCode[0:2])

    def genera_codigos(self):
        self.codigos.add(self.idOrganismo)
        for c in list(self.codigos):
            if isinstance(c, str) and c.startswith("E0"):
                self.codigos.add(int(c[2:-2]))
        for c in list(self.idPadres):
            if isinstance(c, str) and c.startswith("E0"):
                self.idPadres.add(int(c[2:-2]))

    @property
    def nombre(self):
        nombre = self.deOrganismo
        if self.isCsic:
            nombre = re_paren.sub("", nombre).strip()
        return simplificar(nombre)

    def genera_nombres(self):
        nombre = self.deOrganismo
        if self.isCsic:
            nombre = re_paren.sub("", nombre).strip()
        nombre = simplificar(nombre)
        self.nombres = set()
        self.nombres.add(nombre)
        flag = True
        #self.nombres.add(re_guion.sub(" ", nombre))
        if nombre.startswith("s. g. "):
            nombre = nombre.replace("s. g. ", "subdireccion general ")
            self.nombres.add(nombre)
        if nombre.startswith("s.g. "):
            nombre = nombre.replace("s.g. ", "subdireccion general ")
            self.nombres.add(nombre)
        if nombre.startswith("del.gob. "):
            nombre = nombre.replace("del.gob. ", "delegacion del gobierno ")
            self.nombres.add(nombre)
        if nombre.startswith("subdel.gob. "):
            nombre = nombre.replace(
                "subdel.gob. ", "subdelegacion del gobierno ")
            self.nombres.add(nombre)
        if nombre.startswith("subdelegacion ") and nombre.endswith(" - s.gral."):
            nombre = nombre.replace(" - s.gral.", " - subdelegacion")
            self.nombres.add(nombre)
        if nombre.startswith("subdelegacion ") and nombre.endswith(" s.gral."):
            nombre = nombre.replace(" s.gral.", " - subdelegacion")
            self.nombres.add(nombre)
        if len(self.nombres) == 1 and not nombre.endswith(" - subdelegacion"):
            self.nombres.add(re_guion.sub(" ", nombre))

    @property
    def dire(self):
        return simplificar_dire(self.deDireccion)

    @property
    def url(self):
        if self.idUnidOrganica:
            return "https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm?idUnidOrganica=" + str(self.idUnidOrganica)
        if self.idCsic:
            return "http://www.csic.es/centros-de-investigacion1/-/centro/" + str(self.idCsic)
        return None


class Descripciones:

    def load(name="descripciones"):
        fn = name if os.path.isfile(name) else"datos/" + name + ".json"
        with open(fn, "r") as f:
            dt = json.load(f)
            return Descripciones(**dt)

    def save(self, name="descripciones"):
        fn = name if os.path.isfile(name) else"datos/" + name + ".json"
        with open(fn, "w") as f:
            f.write(json.dumps(self.__dict__, indent=4, sort_keys=True))

        for k, v in self.__dict__.items():
            values = set(v.values())
            with open("debug/" + k.lower() + ".txt", "w") as f:
                for p in sorted(values):
                    f.write(p + "\n")

    def __init__(self, **kwargs):
        for k in kwargs.keys():
            dt = {_k: _v for _k, _v in kwargs[k].items() if _v is not "None"}
            k = k[0].lower() + k[1:]
            setattr(self, k, dt)


class Puesto:

    def load(name="destinos_tai", descripciones="descripciones"):
        fn = name if os.path.isfile(name) else"datos/" + name + ".json"
        desc = Descripciones.load(name=descripciones)
        with open(fn, "r") as f:
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
        fn = name if os.path.isfile(name) else"datos/" + name + ".json"
        col = sorted(col, key=lambda o: o.idPuesto)
        with open(fn, "w") as f:
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
        self.remove = set("remove direccionSingular turno nota".split())
        self.ranking = None
        self.desaparecido = None
        self.latlon = None
        self.direccion = None
        self.direccionSingular = False
        self.turno = None
        self.nota = None
        self.deObservaciones = None
        self.idObservaciones = None
        self.grupo = None
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
            = args[0:25]

        if self.idResidencia and isinstance(self.idResidencia, str):
            self.pais, self.provincia, self.localidad = [
                int(i) for i in self.idResidencia.split("-")]
        if self.dePuesto is None:
            self.dePuesto = dePuestoCorta

    @property
    def sueldo(self):
        c = 14981.76
        if self.nivel == 16:
            c = 15307.68
        if self.idCentroDirectivo == 50303:
            # revisar
            # c += (53.60 + 211.62) * 12
            # https://github.com/s-nt-s/TAI-Madrid/issues/30
            pass
        return self.complemento + c

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
        if self.nivel < 15 or self.nivel > 22:
            return False
        if not re_informatica.search(self.dePuesto) or re_no_informatica.search(self.dePuesto):
            if puesto_ko is not None:
                puesto_ko.add(self.dePuesto)
            return False
        if puesto_ok is not None:
            puesto_ok.add(self.dePuesto)
        return True

    @property
    def abbr_puesto(self):
        dePuesto = self.dePuesto
        for s1, s2 in (
            ("PROGRAMADOR / PROGRAMADORA", "PROGRAMADOR/A"),
            ("JEFE / JEFA", "JEFE/A"),
            ("ADMINISTRADOR / ADMINISTRADORA", "ADMINISTRADOR/A"),
            ("COORDINADOR / COORDINADORA", "COORDINADOR/A"),
            ("MONITOR / MONITORA", "MONITOR/A"),
            ("SECRETARIO / SECRETARIA", "SECRETARIO/A"),
            ("TECNICO / TECNICA", "TECNICO/A"),
            ("OPERADOR / OPERADORA", "OPERADOR/A"),
        ):
            dePuesto = dePuesto.replace(s1+" ", s2+" ")
        return dePuesto


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            obj = list(sorted(v, key=lambda i: str(i)))
            return super(MyEncoder, self).default(obj)
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
                    cp[k] = list(sorted(v, key=lambda i: str(i)))
        return cp


class Info:

    def __init__(self, puestos, descripciones, organismos):
        self.descripciones = descripciones
        self.puestos = puestos
        self.pais = puestos[0].pais
        self.provincia = puestos[0].provincia
        self.deProvincia = puestos[0].deProvincia or "¿?¿?"
        self.organismos = organismos
        for o in self.organismos.values():
            if o.idProvincia is not None:
                o.deProvincia = self.descripciones.provincias.get(
                    str(o.idProvincia), None)
        self.cur_ministerio = None
        self.cur_centrodirectivo = None
        self.cur_unidad = None
        self.org_ministerio = None
        self.org_centrodirectivo = None
        self.org_unidad = None

    @property
    def puestos_by_ministerio(self):
        puestos = sorted([p for p in self.puestos if p.idMinisterio ==
                          self.cur_ministerio], key=lambda i: i.order)
        return puestos

    @property
    def next_ministerio(self):
        ministerios = set([p.idMinisterio for p in self.puestos])
        for k, v in sorted(self.descripciones.ministerio.items(), key=lambda i: (i[1], i[0])):
            k = int(k)
            if k in ministerios:
                self.cur_ministerio = k
                self.org_ministerio = self.organismos.get(k, None)
                yield (k, v, self.org_ministerio, None)

    @property
    def next_centrodirectivo(self):
        centrodirectivos = set(
            [p.idCentroDirectivo for p in self.puestos if p.idMinisterio == self.cur_ministerio])
        for k, v in sorted(self.descripciones.centroDirectivo.items(), key=lambda i: (i[1], i[0])):
            k = int(k)
            if k in centrodirectivos:
                self.cur_centrodirectivo = k
                self.org_centrodirectivo = self.organismos.get(k, None)
                yield (k, v, self.org_centrodirectivo, self.org_ministerio)
        self.cur_centrodirectivo = None
        self.org_centrodirectivo
        if next(self.next_unidad, None):
            yield (-1, "Sin centro directivo", None, self.org_ministerio)

    @property
    def next_unidad(self):
        unidades = set([p.idUnidad for p in self.puestos if p.idMinisterio ==
                        self.cur_ministerio and p.idCentroDirectivo == self.cur_centrodirectivo])
        for k, v in sorted(self.descripciones.unidad.items(), key=lambda i: (i[1], i[0])):
            k = int(k)
            if k in unidades:
                if k == self.cur_centrodirectivo:
                    continue
                self.cur_unidad = k
                self.org_unidad = self.organismos.get(k, None)
                yield (k, v, self.org_unidad, self.org_centrodirectivo or self.org_ministerio)

    @property
    def estado_ministerio(self):
        if "V" in set([p.estado for p in self.puestos if p.idMinisterio == self.cur_ministerio]):
            return "V"
        return "NV"
