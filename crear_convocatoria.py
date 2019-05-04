#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import re
from glob import glob

import requests
import simplekml
import utm
import xlrd
import xlwt

from api import (Descripciones, Jnj2, Organismo, Puesto, dict_from_txt,
                 get_cod_dir_latlon, get_direcciones_txt, money,
                 simplificar_dire, soup_from_file, yaml_from_file)

re_space = re.compile(r"  +")


def parse(cell):
    if not cell:
        return None
    v = cell.value
    if isinstance(v, float):
        return int(v) if v.is_integer() else v
    if isinstance(v, str):
        v = v.strip()
        v = re_space.sub(" ", v)
        if v.isdigit():
            return int(v)
        return v if len(v) else None
    return v


def get_provincia(s):
    if s == "BARCELONA":
        return 8
    elif s == "BIZKAIA":
        return 48
    elif s == "CACERES":
        return 10
    elif s == "CADIZ":
        return 11
    elif s == "CEUTA":
        return 51
    elif s == "CIUDAD REAL":
        return 13
    elif s == "CORDOBA":
        return 14
    elif s == "GRANADA":
        return 18
    elif s == "GUADALAJARA":
        return 19
    elif s == "HUELVA":
        return 21
    elif s == "ILLES BALEARS":
        return 7
    elif s == "JAEN":
        return 23
    elif s == "LAS PALMAS":
        return 35
    elif s == "MADRID":
        return 28
    elif s == "MALAGA":
        return 29
    elif s == "MELILLA":
        return 52
    elif s == "S. C. TENERIFE":
        return 38
    elif s == "SEVILLA":
        return 41
    elif s == "TARRAGONA":
        return 43
    elif s == "TERUEL":
        return 44
    elif s == "TOLEDO":
        return 45
    elif s == "ZAMORA":
        return 49
    return None


def get_puesto(v):
    v = v.replace("OPERADOR / OPERADORA", "OPERADOR/A")
    v = v.replace("PROGRAMADOR / PROGRAMADORA", "PROGRAMADOR/A")
    v = v.replace("TECNICO / TECNICA", "TECNICO/A")
    v = v.replace("INDFORMATICA", "INFORMATICA")
    v = v.replace("INFORMATCA", "INFORMATICA")
    v = v.replace("\n", " ")
    v = re_space.sub(" ", v)
    v = v.strip()
    return v


def get_ministerio(v):
    if v == "AG. ESTATAL DE ADMON. TRIBUTARIA":
        return 44
    elif v == "AGENCIA ESTATAL DE SEGURIDAD FERROVIARIA":
        return (36, 49789)  # MINISTERIO DE FOMENTO
    elif v == "COMISION NAL. MERCADOS Y LA COMPETENCIA":
        return (48, 49572)  # ENTES PUBLICOS
    elif v == "FONDO ESPAÑOL GARANT.AGRARIA, O.A.(FEGA)":
        return (50244, 1129)  # MINISTERIO DE AGRICULTURA, PESCA Y ALIMENTACION
    elif v == "INST.CONTABILIDAD Y AUDITORIA DE CTAS.":
        return (50249, 1210)  # MINISTERIO DE ECONOMIA Y EMPRESA
    elif v == "JEFATURA CENTRAL DE TRAFICO":
        return (38, 1302)  # MINISTERIO DEL INTERIOR
    elif v == "MINISTERIO DE AA.EE., UNION EUR. Y COOP.":
        return 50239
    elif v == "MINISTERIO DE AGRICULT.,PESCA Y ALIMENT.":
        return 50244
    elif v == "MINISTERIO DE CIENCIA, INNOV. Y UNIVERS.":
        return 50251
    elif v == "MINISTERIO DE CULTURA Y DEPORTE":
        return 50248
    elif v == "MINISTERIO DE DEFENSA":
        return 33
    elif v == "MINISTERIO DE ECONOMIA Y EMPRESA":
        return 50249
    elif v == "MINISTERIO DE EDUCACION Y FORMAC. PROF.":
        return 50241
    elif v == "MINISTERIO DE FOMENTO":
        return 36
    elif v == "MINISTERIO DE HACIENDA":
        return 50240
    elif v == "MINISTERIO DE INDUST.,COMERCIO Y TURISMO":
        return 50243
    elif v == "MINISTERIO DE JUSTICIA":
        return 39
    elif v == "MINISTERIO DE POLIT.TERRIT.Y FUNC. PUBL.":
        return 50246
    elif v == "MINISTERIO DE TRAB., MIGRAC.Y SEG.SOCIAL":
        return 50242
    elif v == "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA":
        return 50247
    elif v == "MINISTERIO PRESID.,REL.CORTES E IGUALDAD":
        return 50245
    elif v == "MINISTERIO SANIDAD, CONS. Y BIENEST.SOC.":
        return 50250
    elif v == "SERVICIO PUBLICO DE EMPLEO ESTATAL":
        # MINISTERIO DE TRABAJO, MIGRACIONES Y SEGURIDAD SOCIAL
        return (50242, 1428)
    return None


def get_centro(m, c):
    if m == 44:  # AG. ESTATAL DE ADMON. TRIBUTARIA
        if c == "DEPARTAMENTO DE ADUANAS E II.EE.":
            return 40760
        elif c == "DEPARTAMENTO DE GESTION TRIBUTARIA":
            return 40757
        elif c == "DEPARTAMENTO DE INFORMATICA TRIBUTARIA":
            return 40762
        elif c == "DEPARTAMENTO DE INSPECCION FIN.Y TRIB.":
            return 40758
        elif c == "DEPARTAMENTO DE RECURSOS HUMANOS":
            return 47676
        elif c == "SERVICIO DE GESTION ECONOMICA":
            return 47677
#    elif m==49789: #AGENCIA ESTATAL DE SEGURIDAD FERROVIARIA
#        if c =="DIVISION DE ADMINISTRACION":
#            return 49793
    elif m == 50239:  # MINISTERIO DE AA.EE., UNION EUR. Y COOP.
        if c == "D.G. DEL SERVICIO EXTERIOR":
            return 46098
    elif m == 50244:  # MINISTERIO DE AGRICULT.,PESCA Y ALIMENT.
        if c == "D.G. DE SERVICIOS":
            return 47948
    elif m == 50251:  # MINISTERIO DE CIENCIA, INNOV. Y UNIVERS.
        if c == "SUBSECRETARIA DE CIENCIA, INNOV. Y UNIV.":
            return 50363
    elif m == 50248:  # MINISTERIO DE CULTURA Y DEPORTE
        if c == "SUBSECRETARIA DE CULTURA Y DEPORTE":
            return 50357
    elif m == 33:  # MINISTERIO DE DEFENSA
        if c == "S. DE E. DE DEFENSA":
            return 1160
    elif m == 50249:  # MINISTERIO DE ECONOMIA Y EMPRESA
        if c == "D.G. DE SEGUROS Y FONDOS DE PENSIONES":
            return 1190
        elif c == "SUBSECRETARIA DE ECONOMIA Y EMPRESA":
            return 50359
    elif m == 50241:  # MINISTERIO DE EDUCACION Y FORMAC. PROF.
        if c == "DIRECCION PROVINCIAL":
            return 1233
        elif c == "SUBSECRETARIA DE EDUCACION Y FORM. PROF.":
            return 50342
    elif m == 36:  # MINISTERIO DE FOMENTO
        if c == "C. ESTUDIOS Y EXPERIMENT. O.P.(CEDEX)":
            return 1258
        elif c == "CENTRO NACIONAL INFORMACION GEOGRAFICA":
            return 1259
        elif c == "D.G. DE LA MARINA MERCANTE":
            return 1245
        elif c == "D.G. DE ORGANIZACION E INSPECCION":
            return 49995
        elif c == "D.G. DE TRANSPORTE TERRESTRE":
            return 1244
    elif m == 50240:  # MINISTERIO DE HACIENDA
        if c == "D.G. DE ORDENACION DEL JUEGO":
            return 49126
        elif c == "D.G. DE RACIONALIZ. Y CENTR. CONTRATAC.":
            return 49627
        elif c == "D.G. DEL CATASTRO":
            return 1271
        elif c == "D.G. DEL PATRIMONIO DEL ESTADO":
            return 1266
        elif c == "INTERVENCION GRAL.ADMON. DEL ESTADO":
            return 1274
        elif c == "SECRETARIA GENERAL TECNICA":
            return 49352
        elif c == "SUBSECRETARIA DE HACIENDA":
            return 50340
        elif c == "TRIBUNAL ECONOMICO-ADMTVO.CENTRAL":
            return 1272
    elif m == 50243:  # MINISTERIO DE INDUST.,COMERCIO Y TURISMO
        if c == "D.G. DE INDUSTRIA Y DE LA PEQU. Y M.EMP.":
            return 49346
        elif c == "SUBSECRETARIA DE INDUST., COMERC. Y TUR.":
            return 50347
    elif m == 39:  # MINISTERIO DE JUSTICIA
        if c == "D.G.MOD.JUST.,DES.TEC., REC.Y GEST.ARCT.":
            return 50393
        elif c == "SUBSECRETARIA DE JUSTICIA":
            return 1307
    elif m == 50246:  # MINISTERIO DE POLIT.TERRIT.Y FUNC. PUBL.
        if c == "D.G. DE LA FUNCION PUBLICA":
            return 1051
        elif c == "DEL.GOB. EN ANDALUCIA":
            return 1064
        elif c == "DEL.GOB. EN ARAGON":
            return 1065
        elif c == "DEL.GOB. EN CANARIAS":
            return 1068
        elif c == "DEL.GOB. EN CASTILLA Y LEON":
            return 1071
        elif c == "DEL.GOB. EN CASTILLA-LA MANCHA":
            return 1070
        elif c == "DEL.GOB. EN CATALUÑA":
            return 1072
        elif c == "DEL.GOB. EN EXTREMADURA":
            return 1073
        elif c == "DEL.GOB. EN ILLES BALEARS":
            return 1067
        elif c == "DEL.GOB. EN LA CIUDAD DE MELILLA":
            return 1082
        elif c == "DEL.GOB. EN MADRID":
            return 1076
        elif c == "S.GRAL. DE ADMINISTRACION DIGITAL":
            return 49959
        elif c == "SUBSECRETARIA DE POL.TERRIT.Y FUNC.PUBL.":
            return 50353
    elif m == 50242:  # MINISTERIO DE TRAB., MIGRAC.Y SEG.SOCIAL
        if c == "S. DE E. DE LA SEGURIDAD SOCIAL":
            return 50303
        elif c == "SUBSECRETARIA DE TRAB., MIGR. Y SEG.SOC.":
            return 50344
    elif m == 50247:  # MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA
        if c == "SUBSECRETARIA PARA LA TRANSICION ECOLOG.":
            return 50355
    elif m == 50245:  # MINISTERIO PRESID.,REL.CORTES E IGUALDAD
        if c == "SUBSECRETARIA DE PRES.,R.CORT. E IGUALD.":
            return 50351
        elif c == "VICESECRETARIA GENERAL A.P.":
            return 50382
    elif m == 50250:  # MINISTERIO SANIDAD, CONS. Y BIENEST.SOC.
        if c == "SUBSECRETARIA DE SANIDAD,CONS.Y B.SOCIAL":
            return 50361
    return None


def get_ministerio_centro(m, c):
    m = get_ministerio(m)
    if isinstance(m, tuple):
        return m
    return (m, get_centro(m, c))


def get_unidad(m, c, u):
    if u is None:
        return None
    if (m, c) == (33, 1160):
        if u == "CTRO.SIST.Y TECN. DE INFORM.Y COMUNICAC.":
            return 49060
    elif (m, c) == (36, 1244):
        if u == "S.G. DE GEST., ANAL.E INN.TRANSP. TERR.":
            return 30324
    elif (m, c) == (36, 1245):
        if u == "S.G. DE COORDINACION Y GESTION ADMTVA.":
            return 30331
    elif (m, c) == (36, 1258):
        if u == "SECRETARIA CEDEX":
            return 49031
    elif (m, c) == (36, 1259):
        if u == "C. NAC. DE INF. GEOGRAFICA":
            return 30285
    elif (m, c) == (36, 49995):
        if u == "S.G. DE TECN.DE LA INF. Y ADMON. DIGITAL":
            return 49104
    elif (m, c) == (38, 1302):
        if u == "GERENCIA DE INFORMATICA":
            return 50089
    elif (m, c) == (39, 1307):
        if u == "DIVISION DE TECNOL.DE LA INF.Y LAS COM.":
            return 46136
    elif (m, c) == (39, 50393):
        if u == "S.G.DE NUEVAS TECNOLOGIAS DE LA JUSTICIA":
            return 31398
    elif (m, c) == (44, 40757):
        if u == "OFICINA NACIONAL DE GESTION TRIBUTARIA":
            return 40793
    elif (m, c) == (44, 40758):
        if u == "GERENCIA Y APOYO ADMINISTRATIVO":
            return 41234
    elif (m, c) == (44, 40760):
        if u == "JEFATURA":
            return 40810  # ¿¿ o 41245??
    elif (m, c) == (44, 40762):
        if u == "JEFATURA":
            return 40821
    elif (m, c) == (44, 47676):
        if u == "JEFATURA":
            return 47678
    elif (m, c) == (44, 47677):
        if u == "JEFATURA":
            return 47680
    elif (m, c) == (48, 49572):
        if u == "SUBDIREC. DE SIST. TECNOL. INFORM.Y COM.":
            return 49654
#    elif (m, c) == (49789, 49793):
#        if u == "None":
#            return None
    elif (m, c) == (50239, 46098):
        if u == "S.G. INFORMATICA, COMUNICAC. Y REDES":
            return 48535
    elif (m, c) == (50240, 1266):
        if u == "S.G. DE COORDINAC. CONTRATAC. ELECTRON.":
            return 47601
    elif (m, c) == (50240, 1271):
        if u == "S.G. DE ESTUDIOS Y SISTEMAS DE INF.":
            return 30711
    elif (m, c) == (50240, 1272):
        if u == "S.G. DE ORGANIZ. MEDIOS Y PROCEDIMIENTOS":
            return 30716
    elif (m, c) == (50240, 1274):
        if u == "OFICINA DE INFORMATICA PRESUPUESTARIA":
            return 30625
    elif (m, c) == (50240, 49126):
        if u == "S.G. DE GESTION Y RELACIONES INSTITUC.":
            return 49130
    elif (m, c) == (50240, 49352):
        if u == "S.G. DE COORD. INF. ECONOMICO-FINANCIERA":
            return 49633
    elif (m, c) == (50240, 49627):
        if u == "UNIDAD DE APOYO":
            return 49634
    elif (m, c) == (50240, 50340):
        if u == "S.G.TECNOLOG.DE LA INF.Y DE LAS COMUNIC.":
            return "EA0023032"  # ¿¿¿???
    elif (m, c) == (50241, 1233):
        if u == "DIRECCION PROVINCIAL DE CEUTA (D)":
            return 30199
    elif (m, c) == (50241, 50342):
        if u == "S.G. DE TECNOLOG. DE LA INFORM. Y COMUN.":
            return 48578
    elif (m, c) == (50242, 1428):
        if u == "DIRECCION PROVINCIAL DE GRANADA":
            return 36969
        elif u == "S.G. DE TECNOLOG.INFORMACION Y COMUNIC.":
            return 36946
    elif (m, c) == (50242, 50303):
        if u == "GERENCIA DE INFORMATICA DE LA S.S.":
            return 46272
        elif u == "U. PROV. INFORMAT. DE BALEARES":
            return 48061
        elif u == "U. PROV. INFORMAT. DE LAS PALMAS":
            return 48081
        elif u == "U. PROV. INFORMAT. DE SEVILLA":
            return 48096
        elif u == "U. PROV. INFORMAT. DE TARRAGONA":
            return 48098
        elif u == "U. PROV. INFORMAT. DE TENERIFE":
            return 48099
        elif u == "U. PROV. INFORMAT. DE VIZCAYA":
            return 48105
        elif u == "U. PROV. INFORMAT. INSS DE BARCELONA":
            return 48062
        elif u == "U. PROV. INFORMAT. INSS DE MADRID":
            return 48085
        elif u == "U. PROV. INFORMAT. TGSS-ISM DE MADRID":
            return 48086
    elif (m, c) == (50242, 50344):
        if u == "S.G. DE TECNOLOGIAS DE LA INF.Y COMUNIC.":
            return 37211
    elif (m, c) == (50243, 49346):
        if u == "S.G. DE GESTION Y EJECUCION DE PROGRAMAS":
            return 50002  # EA0011271
    elif (m, c) == (50243, 50347):
        if u == "S.G. DE TECNOLOG.DE LA INF.Y DE LAS COM.":
            return 46383
    elif (m, c) == (50244, 1129):
        if u == "SECRETARIA GENERAL":
            return 27436
    elif (m, c) == (50244, 47948):
        if u == "S.G. DE TECNOLOGIAS INFORM. Y COMUNICAC.":
            return 48512
    elif (m, c) == (50245, 50351):
        if u == "S.G. TECNOL. Y SERVICIOS DE INFORMACION":
            return 26685
    elif (m, c) == (50245, 50382):
        if u == "UNIDAD DE INFORMATICA A.P.":
            return 31730
    elif (m, c) == (50246, 1051):
        if u == "S.G. PLANIF. DE RR.HH. Y RETRIBUCIONES":
            return 26666
    elif (m, c) == (50246, 1064):
        if u == "OFIC.COORD. ADM.GRAL.ESTADO C.GIBRALTAR":
            return 47254
        elif u == "SUBDEL.GOB. EN CORDOBA - S.GRAL.":
            return 26707
        elif u == "SUBDEL.GOB. EN HUELVA - S.GRAL.":
            return 26709
        elif u == "SUBDEL.GOB. EN JAEN - S.GRAL.":
            return 26710
        elif u == "SUBDEL.GOB. EN MALAGA - S.GRAL.":
            return 26711
    elif (m, c) == (50246, 1065):
        if u == "SUBDEL.GOB. EN TERUEL - S.GRAL.":
            return 26749
    elif (m, c) == (50246, 1067):
        if u == "D. INS.A.G.E. IBIZA-FORMENTERA - S.GRAL.":
            return 26784
    elif (m, c) == (50246, 1068):
        if u == "D.INS. A.G.E. EL HIERRO - S.GRAL.":
            return 26813
    elif (m, c) == (50246, 1070):
        if u == "DEL.GOB. CASTILLA-LA MANCHA - S.GRAL.":
            return 26824
        elif u == "SUBDEL.GOB. EN CIUDAD REAL - S.GRAL.":
            return 26831
        elif u == "SUBDEL.GOB. GUADALAJARA - S.GRAL.":
            return 26833
    elif (m, c) == (50246, 1071):
        if u == "SUBDEL.GOB. ZAMORA - S.GRAL.":
            return 26867
    elif (m, c) == (50246, 1072):
        if u == "SUBDEL.GOB. EN BARCELONA - SUBDEL.":
            return 26894
        elif u == "SUBDEL.GOB. EN TARRAGONA - S.GRAL.":
            return 26900
    elif (m, c) == (50246, 1073):
        if u == "SUBDEL.GOB. EN CACERES - S.GRAL.":
            return 26926
    elif (m, c) == (50246, 1076):
        if u == "DEL.GOB. EN MADRID - S.GRAL.":
            return 26971
    elif (m, c) == (50246, 1082):
        if u == "DEL.GOB. EN CIUDAD DE MELILLA - S.GRAL.":
            return 27056
    elif (m, c) == (50246, 49959):
        if u == "GABINETE":
            return 49758
    elif (m, c) == (50246, 50353):
        if u == "DIV. DE TECNOLOGIAS DE LA INFORMACION":
            return 50495  # EA0020003
    elif (m, c) == (50247, 50355):
        if u == "DIV. SIST.Y TECNOL.DE LA INF. Y COMUNIC.":
            return "EA0022462"  # ¿¿¿????
    elif (m, c) == (50248, 50357):
        if u == "DIVISION DE TECNOLOGIAS DE LA INFORMAC.":
            return 50454
    elif (m, c) == (50249, 1190):
        if u == "UNIDAD DE APOYO":
            return 29806
    elif (m, c) == (50249, 1210):
        if u == "SECRETARIA GENERAL":
            return 29597
    elif (m, c) == (50249, 50359):
        if u == "S.G. DE TECNOLOG.INFORM.Y LAS COMUNIC.":
            return 48593
    elif (m, c) == (50250, 50361):
        if u == "S.G. DE TECNOLOGIAS DE LA INFORMACION":
            return 31812
    elif (m, c) == (50251, 50363):
        if u == "DIVISION DE TECNOLOG. DE LA INFORMACION":
            return 50475  # EA0020824
    elif (m, c) == (36, 49789):
        if u == "DIVISION DE ADMINISTRACION":
            return 49793
    return None


'''
xls_info = {}
url = "https://docs.google.com/spreadsheet/ccc?key=1OW2tyeRYyufqpacr3z3l6Z_5UX8XqyTJvQA7I9-zLCs&output=xls"
r = requests.get(url)
wb = xlrd.open_workbook(file_contents=r.content)
sh = wb.sheet_by_index(0)
data_excel={}
for rx in range(sh.nrows):
    row = [parse(c) for c in sh.row(rx)]
    info, index = row[2], row[4]
    if index is None:
        index = "¿?¿?¿?"
    if info is None:
        info = "¿?¿?¿?"
    print (str(index) + " ---- " +info)
'''

idUnidOrganica = set([int(i[33:-5])
                      for i in glob("fuentes/administracion.gob.es/id_*.html")])

organismos = {}
for o in Organismo.load():
    if o.idUnidOrganica not in idUnidOrganica:
        o.idUnidOrganica = None
    for c in o.codigos:
        organismos[c] = o

cod_dir_latlon = get_cod_dir_latlon()
arreglos = yaml_from_file("arreglos/rpt_dir3.yml")
notas = dict_from_txt("arreglos/notas.txt")

todos_puestos = {p.idPuesto: p for p in Puesto.load(name="destinos_tai")}
vacantes_tai = [p for p in Puesto.load() if p.isTAI() and p.estado == "V"]


class Org:

    def __init__(self, codigo, descripcion):
        ll = cod_dir_latlon.get(codigo, None)
        self.nota = notas.get(codigo, None)
        self.clave = codigo
        self.codigo = codigo
        self.descripcion = descripcion
        self.hijos = set()
        self.puestos = []
        self.rpt = None
        self.deDireccion = None
        self.organismo = organismos.get(codigo, None)
        if self.organismo is None:
            codigo = arreglos.get(codigo, None)
            if codigo:
                self.organismo = organismos.get(codigo, None)

        if self.organismo:
            self.latlon = self.organismo.latlon
            self.deDireccion = self.organismo.deDireccion

        if ll:
            self.latlon, self.deDireccion = ll

        if self.deDireccion:
            self.deDireccion = self.deDireccion.replace(" (MADRID)", "")

        if isinstance(self.codigo, str):
            self.codigo = "¿?"

    def get_hijos(self):
        return sorted(self.hijos, key=lambda o: (o.descripcion, o.codigo))

    def __eq__(self, o):
        self.codigo == o.codigo

    def __hash__(self):
        return self.codigo.__hash__()

    @property
    def nombre(self):
        if self.codigo == 48:
            return "ENTES PÚBLICOS"
        if not self.organismo or not self.organismo.deOrganismo:
            return self.descripcion
        return self.organismo.deOrganismo

    @property
    def vacantes(self):
        if len(self.puestos) == 0:
            return []
        nv = max([p.nivel for p in self.puestos])
        vacantes = {}
        for p in vacantes_tai:
            if p.idUnidad == self.codigo and p.nivel > nv:
                v = vacantes.get(p.nivel, 0) + 1
                vacantes[p.nivel] = v
        vacantes = sorted([v for v in vacantes.items()])
        return vacantes


dict_organ = {}


def get_org(i, d):
    k = (i or d)
    o = dict_organ.get(k, None)
    if o is None:
        o = Org(i, d)
        dict_organ[k] = o
    return o


descripciones = Descripciones.load()
'''
wb_out = xlwt.Workbook()
ws_out = wb_out.add_sheet('Oferta normalizada')
row = ws_out.row(0)
for i, v in enumerate(["PUESTO\nNÚMERO", "ID MINISTERIO", "MINISTERIO", "ID CENTRO", "CENTRO", "ID UNIDAD", "UNIDAD"]):
    row.write(i, v)
'''

org_convocatoria = Org(None, None)
puestos = []
unidades = []
wb = xlrd.open_workbook("fuentes/2017_L.xls", logfile=open(os.devnull, 'w'))
sh = wb.sheet_by_index(0)
for rx in range(1, sh.nrows):
    r = [parse(c) for c in sh.row(rx)]
    if len(r) == 10:
        p = todos_puestos.get(r[-3], Puesto())
        p.ranking = r[0]
        p.idPuesto = r[-3]
        p.dePuesto = get_puesto(r[-4])
        p.nivel = r[-2]
        p.complemento = r[-1]
        p.provincia = get_provincia(r[4])
        p.localidad = r[5]
        p.deMinisterio = r[1]
        p.deCentroDirectivo = r[2]
        p.deUnidad = r[3]
        p.idMinisterio, p.idCentroDirectivo = get_ministerio_centro(
            p.deMinisterio, p.deCentroDirectivo)
        if p.deUnidad:
            p.idUnidad = get_unidad(
                p.idMinisterio, p.idCentroDirectivo, p.deUnidad)
        else:
            p.idUnidad = get_unidad(
                p.idMinisterio, p.idCentroDirectivo, p.deCentroDirectivo)
            if p.idUnidad:
                p.deUnidad = p.deCentroDirectivo

        if p.deObservaciones in ("PUESTOS CON DEST. EN SS.CC O AMB. TERRIT. DELG. HAC. ESP. O", "OFERTA DE EMPLEO PUBLICO PARA CUERPOS GENERALES", "P.TRABAJO RESERVADO PARA OCUPACION PERSONAL DE NUEVO INGRESO"):
            p.idObservaciones = None
            p.deObservaciones = None
        if p.idObservaciones == "H.T, OCG":
            p.idObservaciones = None
            p.deObservaciones = None
            p.turno = "TARDE"
        if p.deObservaciones is None:
            p.deObservaciones = p.idObservaciones

        if p.idPuesto in (5465059, 5465060):
            p.turno = "NOCHE"
        if p.idPuesto in (5465061,):
            p.turno = "TARDE"

        puestos.append(p)

        oM = get_org(p.idMinisterio, p.deMinisterio)
        oM.rpt = descripciones.ministerio.get(str(p.idMinisterio), None)
        oC = get_org(p.idCentroDirectivo, p.deCentroDirectivo)
        oC.rpt = descripciones.centroDirectivo.get(
            str(p.idCentroDirectivo), None)
        oU = get_org(p.idUnidad, p.deUnidad)
        oU.rpt = descripciones.unidad.get(str(p.idUnidad), None)

        ll = cod_dir_latlon.get(p.idPuesto, None)
        if ll:
            p.latlon, p.deDireccion = ll
            p.direccionSingular = True
        else:
            p.latlon = oU.latlon or oC.latlon
            p.deDireccion = oU.deDireccion or oC.deDireccion

        p.nota = notas.get(p.idPuesto, None)
        if p.grupo != "C1":
            if p.nota is None:
                p.nota = p.grupo
            else:
                p.nota = "("+p.grupo+") " + p.nota

        org_convocatoria.hijos.add(oM)
        oM.hijos.add(oC)
        oC.hijos.add(oU)
        oU.puestos.append(p)
        unidades.append(oU)

        '''
        row = ws_out.row(p.ranking)
        for i, v in enumerate([p.ranking, p.idMinisterio, p.deMinisterio, p.idCentroDirectivo, p.deCentroDirectivo, p.idUnidad, p.deUnidad]):
            row.write(i, v)
        '''

'''
for u in unidades:
    if len(u.puestos)==1:
        p = u.puestos[0]
        if p.latlon:
            u.latlon = p.latlon
            u.deDireccion = p.deDireccion
'''


Puesto.save(puestos, name="2017_L")

# wb_out.save("datos/2017_L_normalizado.xls")

j2 = Jnj2("j2/", "docs/")
j2.save("convocatoria.html", organismos=org_convocatoria)


def get_txt(idOrg):
    org = dict_organ.get(idOrg)
    descripcion = ""
    '''
    descripcion += str(org.codigo) + " - "
    if org.organismo:
        descripcion += org.organismo.idOrganismo + " - "
    '''
    descripcion += org.nombre
    if org.nota:
        descripcion += "\n("+org.nota+")"
    return descripcion


kml = simplekml.Kml()
kml.document.name = "TAI 2017"


folder1 = kml.newfolder(name="Solo 1 o 2 puestos")
folder3 = kml.newfolder(name="De 3 a 10 puestos")
folder11 = kml.newfolder(name="De 11 a 20 puestos")
folder21 = kml.newfolder(name="Más de 20 puestos")

style_azul = simplekml.Style()
style_azul.iconstyle.color = simplekml.Color.blue
style_azul.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/blue.png'

kml.document.style = style_azul

style_verde = simplekml.Style()
style_verde.iconstyle.color = simplekml.Color.green
style_verde.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/green.png'

kml.document.style = style_verde

style_rojo = simplekml.Style()
style_rojo.iconstyle.color = simplekml.Color.red
style_rojo.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/red.png'

kml.document.style = style_rojo

style_gris = simplekml.Style()
style_gris.iconstyle.color = simplekml.Color.blue
style_gris.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/grey.png'

kml.document.style = style_gris

coordenadas = set([p.latlon for p in puestos])

for c in coordenadas:
    pts = [p for p in puestos if p.latlon == c]
    n_pts = len(pts)
    name = "[%s] %s " % (n_pts, pts[0].deDireccion)
    utm_split = c.split(",")
    latlon = (float(utm_split[1]), float(utm_split[0]))
    descripcion = ""
    for m in sorted(set([p.idMinisterio for p in pts])):
        descripcion += "\n\n# " + get_txt(m)
        for c in sorted(set([p.idCentroDirectivo for p in pts if p.idMinisterio == m])):
            descripcion += "\n## " + get_txt(c)
            for u in sorted(set([p.idUnidad for p in pts if p.idMinisterio == m and p.idCentroDirectivo == c])):
                descripcion += "\n### " + get_txt(u)
                for p in [p for p in pts if p.idMinisterio == m and p.idCentroDirectivo == c and p.idUnidad == u]:
                    descripcion += "\n> %s (%s) %s € %s" % (p.ranking,
                                                            p.idPuesto, money(p.sueldo), p.turno or "")
                    if p.nota:
                        descripcion += " ("+p.nota+")"
    if n_pts < 3:
        pnt = folder1.newpoint(name=name, coords=[latlon])
        pnt.style = style_rojo
    elif n_pts < 11:
        pnt = folder3.newpoint(name=name, coords=[latlon])
        pnt.style = style_gris
    elif n_pts < 21:
        pnt = folder11.newpoint(name=name, coords=[latlon])
        pnt.style = style_azul
    else:
        pnt = folder21.newpoint(name=name, coords=[latlon])
        pnt.style = style_verde

    pnt.description = descripcion.strip()

kml.save("docs/mapa/2017.kml")
