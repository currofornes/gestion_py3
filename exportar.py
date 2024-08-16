
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion.settings")
django.setup()
from centro.models import *
from convivencia.models import *
import os
import csv
csv.register_dialect(
    'mydialect',
    delimiter = ',',
    quotechar = '"',
    doublequote = True,
    skipinitialspace = True,
    lineterminator = '\r\n',
    quoting = csv.QUOTE_MINIMAL)#

#Procedencia.objects.all().delete()
#file=open("datos/datos/Procedencia.csv","r")
#lineas=file.readlines()
#for linea in lineas[1:]:
#	print linea
#	lista=linea.split(",")
#	d=Procedencia(id=lista[0],Procedencia=lista[1])
#	d.save()#
#

#Remitente.objects.all().delete()
#file=open("datos/datos/Remitente.csv","r")
#lineas=file.readlines()
#for linea in lineas[1:]:
#	print linea
#	lista=linea.split(",")
#	d=Remitente(id=lista[0],Remitente=lista[1])
#	d.save()#

#ClaseDocumento.objects.all().delete()
#file=open("datos/datos/ClaseDocumento.csv","r")
#lineas=file.readlines()
#for linea in lineas[1:]:
#	print linea
#	lista=linea.split(",")
#	d=ClaseDocumento(id=lista[0],ClaseDocumento=lista[1])
#	d.save()#
#

#Registro.objects.all().delete()
#campos=["Curso","Fecha","N","Tipo","Idp","Idr","Idc","Contenido"]#
#

#file=open("datos/datos/Registro.csv","r")#

#lista=file.readlines()
#for linea in lista[1:]:
#	dato={}	
#	lista2=linea.split(",")
#	for c,v in zip(campos,lista2):
#	
#		if c=="Idp":
#			try:
#				dato[c]=Procedencia.objects.filter(id=v.strip())[0]
#			except:
#				dato[c]=None
#		elif c=="Idr":
#			try:
#				dato[c]=Remitente.objects.filter(id=v.strip())[0]
#			except:
#				dato[c]=None
#		elif c=="Idc":
#			try:
#				dato[c]=ClaseDocumento.objects.filter(id=v.strip())[0]
#			except:
#				dato[c]=None
#		elif c=="Fecha" or c=="Tipo" or c=="Contenido" or c=="Curso":
#			try:
#				dato[c]=v.strip()
#				dato[c]=dato[c]
#			except:
#				pass
#		else:
#			dato[c]="%s"% v.strip()
#		
#	print dato
#	a=Registro(**dato)
#	a.save()
#	



#Cursos.objects.all().delete()
#Alumnos.objects.all().delete()
#Departamentos.objects.all().delete()
#Profesores.objects.all().delete()#

#file=open("datos/datos/Departamentos.csv","r")
#lineas=file.readlines()
#for linea in lineas[1:]:
#	print linea
#	lista=linea.split(",")
#	d=Departamentos(id=lista[0],Abr=lista[1],Nombre=lista[1])
#	d.save()##
#
#
#

#tutores={}
#with open('datos/datos/Profesores.csv', 'rb') as mycsvfile:
#    dictofdata = csv.DictReader(mycsvfile, dialect='mydialect')
#    for lista in dictofdata:
#		print lista
#		p=Profesores(id=lista["Id"],Nombre=lista["Nombre"],Apellidos=lista["Apellidos"],Telefono=lista["Telefono"],Movil=lista["Movil"],Email=lista["Email"],Departamento = Departamentos.objects.get(id=lista["Departamento"]),Baja=lista["Baja"],Ce=lista["Ce"],Etcp=lista["Etcp"],Tic=lista["Tic"],Bil=lista["Bil"])
#		if lista["Tutor"]!="":
#			tutores[lista["Tutor"]]=lista["Id"]
#		p.save()####
#

#print tutores
#cursos=[]
#with open('datos/datos/Alumnos.csv', 'rb') as mycsvfile:
#    dictofdata = csv.DictReader(mycsvfile, dialect='mydialect')
#    for row in dictofdata:
#        cursos.append(row['Unidad'])##
#cursos=list(set(cursos))
#cursos.sort()
#cursos.pop(0)###

#cont=0
#for c in cursos:
#	print c
#	if tutores.has_key(c):
#		c=Cursos(Curso=c,Tutor=Profesores.objects.get(id=tutores[c]))
#	else:
#		c=Cursos(Curso=c)
#	cont=cont+1
#	c.save()###
#
#

###Alumnos
#campos=["Nombre","DNI","Direccion","CodPostal","Localidad","Fecha_nacimiento","Provincia","Unidad","Ap1tutor","Ap2tutor","Nomtutor","Telefono1","Telefono2"]#

#with open('datos/datos/Alumnos.csv', 'rb') as mycsvfile:
#    dictofdata = csv.DictReader(mycsvfile, dialect='mydialect')
#    for row in dictofdata:
#    	row["id"]=row["Id"]
#    	del row["Id"]
#    	print row
#    	if row["Unidad"]=="":
#    		del row["Unidad"]
#    	else:
#    	    row["Unidad"]=Cursos.objects.get(Curso=row["Unidad"])
#    	
#    	a=Alumnos(**row)
#    	a.save()
#		



Amonestaciones.objects.all().delete()
Sanciones.objects.all().delete()


with open('datos/datos/Partes.csv', 'rb') as mycsvfile:
    dictofdata = csv.DictReader(mycsvfile, dialect='mydialect')
    for row in dictofdata:
    	print row
    	row["id"]=row["Id"]
    	del row["Id"]
    	row["IdAlumno"]=Alumnos.objects.get(id=row["Ida"])
    	
    	del row["Ida"]
    	if row["Tipo"]=="a":
    		del row["Tipo"]
	    	
	    	
    		
    		if row["Id_prof"]=="-1":
    			row["Profesor"]=Profesores.objects.get(id=147)
    		else:
    			row["Profesor"]=Profesores.objects.get(id=row["Id_prof"])
    		
    		del row["Sancion"]
    		del row["Fecha_fin"]
    		del row["Id_prof"]
    		
    		a=Amonestaciones(**row)
    		a.save()
    	else:
    		del row["Tipo"]
    		del row["Hora"]
    		del row["Id_prof"]
    		a=Sanciones(**row)
    		a.save()

