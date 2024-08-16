import os
import sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion.settings")
django.setup()
from centro.models import *
from convivencia.models import *

import csv
csv.register_dialect(
    'mydialect',
    delimiter = ',',
    quotechar = '"',
    doublequote = True,
    skipinitialspace = True,
    lineterminator = '\r\n',
    quoting = csv.QUOTE_MINIMAL)#


print "Debe existir un fichero alumnos.csv, con el siguiente contenido:Nombre,DNI,Direccion,CodPostal,Localidad,Fecha_nacimiento,Provincia,Unidad,Ap1tutor,Ap2tutor,Nomtutor,Telefono1,Telefono2,correoelectrónico"
print 'El fichero debe estar codificado con UTF-8. Con la siguiente cabecera: "Nombre","DNI","Direccion","CodPostal","Localidad","Fecha_nacimiento""Provincia","Unidad","Ap1tutor","Ap2tutor","Nomtutor","Telefono1","Telefono2","email"'
print "Se va a proceder a borrar los datos de Cursos, Alumnos, amonestaciones y Sanciones del curso actual"
resp=raw_input("Estas seguro? (s)")
if resp!='s':
    sys.exit(-1)

Cursos.objects.all().delete()
Alumnos.objects.all().delete()
Amonestaciones.objects.all().delete()
Sanciones.objects.all().delete()



cursos=[]
with open('alumnos.csv', 'rb') as mycsvfile:
    dictofdata = csv.DictReader(mycsvfile, dialect='mydialect')
    for row in dictofdata:
        cursos.append(row['Unidad'])##
cursos=list(set(cursos))
cursos.sort()
cursos.pop(0)

cont=0
for c in cursos:
    c=Cursos(Curso=c)
    cont=cont+1
    c.save()###



###Alumnos
campos=["id","Nombre","DNI","Direccion","CodPostal","Localidad","Fecha_nacimiento","Provincia","Unidad","Ap1tutor","Ap2tutor","Nomtutor","Telefono1","Telefono2","email"]

with open('alumnos.csv', 'rb') as mycsvfile:
    dictofdata = csv.DictReader(mycsvfile, dialect='mydialect')
    cont=1
    for row in dictofdata:
        print(row)
        row["id"]=cont
        if row["Unidad"]=="":
            del row["Unidad"]
        else:
            row["Unidad"]=Cursos.objects.get(Curso=row["Unidad"])
        cont=cont+1
        print(row)
        row["Fecha_nacimiento"]=row["Fecha_nacimiento"].split("/")[2]+"-"+row["Fecha_nacimiento"].split("/")[1]+"-"+row["Fecha_nacimiento"].split("/")[0]
        row["Obs"]=""
        print(row)
        a=Alumnos(**row)
        a.save()
        



