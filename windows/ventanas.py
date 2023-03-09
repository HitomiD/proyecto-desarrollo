from PySide6.QtWidgets import QMainWindow, QDialog, QPushButton,QMessageBox
from PySide6.QtCore import Signal,Slot, QLocale
from PySide6.QtGui import QDoubleValidator,QIntValidator
from windows.ui_datosInvalidos import Ui_popupDatosInvalidos
from windows.ui_main import Ui_MenuPrincipal
from windows.ui_newproducto import Ui_newProducto
from windows.ui_confirmElimProd import Ui_confirmElimProducto

from dbModel import Productos,Proveedores
import crud

#Este archivo contiene las definiciones de todas las ventanas (y sus funciones) del sistema

#Las funciones asociadas a eventos deben estar definidas dentro de la misma definicion de la ventana, sino no funcionan.


#Ventana formulario para modificar/añadir producto
class formularioProducto(QDialog) :
    #La señal de guardado se emite en un guardado exitoso para disparar la actualizacion de la tabla.
    guardado = Signal()
    
    def __init__(self):
        super(formularioProducto,self).__init__()
        self.ui = Ui_newProducto()
        self.ui.setupUi(self)
        #Validadores para campos:
        self.floatValidator = QDoubleValidator()
        self.floatValidator.setBottom(0)
        self.floatValidator.setDecimals(2)
        self.floatValidator.setLocale(QLocale.Language.Spanish)
        self.floatValidator.setNotation(QDoubleValidator.StandardNotation)
        self.ui.lnEditPrecio.setValidator(self.floatValidator)
        self.intValidator = QIntValidator()
        self.intValidator.setBottom(0)
        self.intValidator.setLocale(QLocale.Language.Spanish)
        self.ui.lnEditStockMinimo.setValidator(self.intValidator)
        #Fin Validadores
        self.comboBoxSetup()

    def comboBoxSetup(self):
        listaProveedores = crud.listaProveedores()
        for index,proveedor in enumerate(listaProveedores):
            self.ui.comboxDistr.addItem(proveedor.razonsocial) 
    
    #Validacion de datos en los campos
    def fieldCheckProducto(self):
        if self.ui.lnEditPrecio.hasAcceptableInput():
            print ("el precio es valido")
            if self.ui.lnEditNombre.text() != "":
                print ("la descripción es válida")
                if self.ui.lnEditStockMinimo.text() != "":
                    print("El stock mínimo es válido")
                    if self.ui.comboxDistr.currentText() != "":
                        print("El distribuidor es válido. Todos los datos son válidos.")
                        return "ok"
        #Si alguno de los datos es incorrecto se falla el check
        self.popupDatosInv = popupDatosInvalidos()
        self.popupDatosInv.exec_()

#Popup nuevo producto
class VentanaNewProducto(formularioProducto):
    def __init__(self):
        super(VentanaNewProducto,self).__init__()
        self.ui.buttonBox.accepted.connect(self.guardarProducto)
    
    #Guardar producto
    def guardarProducto(self):
        if self.fieldCheckProducto() == "ok":
            nuevoProducto = Productos() #"Productos" es el nombre del modelo de la tabla
            
            #Se extraen los datos de los campos de la ventana
            nuevoProducto.descripcion = self.ui.lnEditNombre.text()
            precio = self.ui.lnEditPrecio.text().replace(",",".") #se reemplaza la coma por el punto para que el interprete lo reconozca como float
            nuevoProducto.precio_venta = precio
            nuevoProducto.stock_minimo = int(self.ui.lnEditStockMinimo.text())
            cuil_cuit_proveedor = Proveedores.select(Proveedores.cuil_cuit).where(self.ui.comboxDistr.currentText() == Proveedores.razonsocial).get()
            nuevoProducto.cuil_cuit_proveedor = cuil_cuit_proveedor
            
            nuevoProducto.save()
            
            self.guardado.emit()
            self.accept()
        
class VentanaEditProducto(formularioProducto):
    def __init__(self):
        super(VentanaEditProducto,self).__init__()
        self.ui.buttonBox.accepted.connect(self.comprobarCampos)

    def comprobarCampos(self):
        if self.fieldCheckProducto() == "ok":
            #print (self.fieldCheckProducto())
            self.guardado.emit()
            self.accept()
      
        
#Ventana principal
class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super(VentanaPrincipal, self).__init__()
        self.ui = Ui_MenuPrincipal()    
        self.ui.setupUi(self)

        #Conectar botones
        self.ui.btnNuevoProducto.clicked.connect(self.showNewProd)
        self.ui.btnElimProducto.clicked.connect(self.showEliminarProd)
        self.ui.btnModProducto.clicked.connect(self.showEditProd)
        
    def showNewProd(self):
        self.w = VentanaNewProducto()
        self.w.guardado.connect(self.updateTablaInventario)
        #self.w.guardado.connect(crud.poblarQTableIngresos(self.ui.tablaIngresos))
        self.w.show()
    
    def showEliminarProd(self):
        self.popupConfirmacion = popupConfirmElim()
        self.popupConfirmacion.accepted.connect(self.eliminarProducto)
        self.popupConfirmacion.exec_()
    
    #Elimina el producto si el proceso se confirma
    def eliminarProducto(self):
        row = self.ui.tablaInventario.currentRow()
        idProducto = int(self.ui.tablaInventario.item(row,0).text())
        crud.eliminarProducto(idProducto)
        self.updateTablaInventario()
    
    #Editar producto
    def showEditProd(self):
        self.modWindow = VentanaEditProducto()
        self.modWindow.setWindowTitle("Editar producto")
        self.modWindow.guardado.connect(self.updateTablaInventario)
        row = self.ui.tablaInventario.currentRow()
        descActual = self.ui.tablaInventario.item(row,1).text()
        #stockNuevo = int(self.ui.tablaInventario.item(row,2).text())
        stockMinActual = int(self.ui.tablaInventario.item(row,3).text())
        precio = self.ui.tablaInventario.item(row,4).text()
        nombreProveedorActual = self.ui.tablaInventario.item(row,5).text()
        
        self.modWindow.ui.lnEditNombre.setText(descActual)
        self.modWindow.ui.lnEditPrecio.setText(precio.replace(".",","))
        self.modWindow.ui.lnEditStockMinimo.setText(str(stockMinActual))
        self.modWindow.ui.comboxDistr.setCurrentText(nombreProveedorActual)
        self.modWindow.accepted.connect(self.editProducto)
        self.modWindow.exec_()
    
    def editProducto(self):
        #Id del producto seleccionado
        row = self.ui.tablaInventario.currentRow()
        idActual = int(self.ui.tablaInventario.item(row,0).text())
        #Obtener datos nuevos
        print("Se ejecuto editConfirmado")
        descNueva = self.modWindow.ui.lnEditNombre.text()
        stockMinNuevo = int(self.modWindow.ui.lnEditStockMinimo.text())
        precioNuevo = float(self.modWindow.ui.lnEditPrecio.text().replace(",","."))
        proveedorNuevo = (Proveedores
                            .select(Proveedores.cuil_cuit)
                            .where(Proveedores.razonsocial == self.modWindow.ui.comboxDistr.currentText())
                            .get())
        #Update query
        qry =(Productos
         .update(descripcion = descNueva,stock_minimo = stockMinNuevo,precio_venta = precioNuevo, cuil_cuit_proveedor = proveedorNuevo)
         .where(Productos.id == idActual))
        qry.execute()
        
        self.updateTablaInventario()
    
    #Actualiza tabla
    def updateTablaInventario(self):
        crud.poblarQTableInventario(self.ui.tablaInventario)
  
#Popup datos ingresados inválidos
class popupDatosInvalidos(QDialog) :
        
    def __init__(self):
        super(popupDatosInvalidos,self).__init__()
        self.ui = Ui_popupDatosInvalidos()
        self.ui.setupUi(self)
        
#Popup confirmacion eliminar producto
class popupConfirmElim(QDialog) :
        
    def __init__(self):
        super(popupConfirmElim,self).__init__()
        self.ui = Ui_confirmElimProducto()
        self.ui.setupUi(self)