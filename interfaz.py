# Interfaz gráfica del programa
from tkinter import Tk, filedialog, messagebox, ttk,Label, LabelFrame, Button, Entry, Frame
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from os import path


class Interfaz:
    # Construcctor
    def __init__(self, root):
        self.root = root
        self.root.title("Interfaz")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        # Estilo de la ventana
        self.style = ttk.Style()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestañas
        self.tab_usuario = Frame(self.notebook)
        self.tab_gestion = Frame(self.notebook)
        self.tab_benchmarks = Frame(self.notebook)
        self.notebook.add(self.tab_usuario, text="Usuario ")
        self.notebook.add(self.tab_gestion, text="Gestión BD ")
        self.notebook.add(self.tab_benchmarks, text="Benchmarks ")

        # Memoria de las rutas al inicializar
        self.img_auth = None
        self.img_reg = None
        self.img_tiempo = None
        self.img_stats = None
        self.img_reg_carpeta = None

        # Panel Global de mensajes
        self.panel_mensajes = LabelFrame(self.root, text=" Notificaciones del Sistema ", height=70)
        self.panel_mensajes.pack_propagate(False)
        self.panel_mensajes.pack(fill="x", padx=10, pady=5, side="bottom")
        
        self.lbl_status = Label(self.panel_mensajes, text="Sistema iniciado. Esperando acción...", 
                                   font=("Helvetica", 10, "italic"), fg="gray")
        self.lbl_status.pack(expand=True)

        self.SetupTabUsuario()
        self.SetupTabGestionBD()
        self.SetupTabBenchmarks()

    # Enviar mensajes al panel global
    def EnviarMensajePanel(self, msg, color="blue"):
        self.lbl_status.config(text=msg, fg=color)
        self.root.update()
    
    # Abrir explorador de archivos
    def SeleccionarArchivo(self, mode):
        ruta = filedialog.askopenfilename(filetypes=[("Iris Images", "*.jpg *.png *.jpeg *.bmp")])
        if ruta:
            if mode == "auth":
                self.img_auth = ruta
                self.lbl_ruta_auth.config(text=path.basename(ruta), fg="black")
                self.btn_run_auth.config(state="normal")
            else:
                self.img_reg = ruta
                self.lbl_ruta_reg.config(text=path.basename(ruta), fg="black")
                self.btn_run_reg.config(state="normal")

     # Abrir explorador de carpetas
    def SeleccionarCarpeta(self, mode):
        ruta_carpeta = filedialog.askdirectory(title="Selecciona una carpeta")
        if ruta_carpeta:
            if mode == "tiempo":
                self.img_tiempo = ruta_carpeta
                self.lbl_ruta_tiempo.config(text=path.basename(ruta_carpeta), fg="black")
                self.btn_run_tiempo.config(state="normal")
            elif mode == "stats":
                self.img_stats = ruta_carpeta
                self.lbl_ruta_stats.config(text=path.basename(ruta_carpeta), fg="black")
                self.lbl_ruta_stats.config(state="normal")
            elif mode == "reg_carpeta":
                self.img_reg_carpeta = ruta_carpeta
                self.lbl_ruta_reg_carpeta.config(text=path.basename(ruta_carpeta), fg="black")
                self.lbl_ruta_reg_carpeta.config(state="normal")
    
    # Vista de Usuario
    def SetupTabUsuario(self):
        #------------------------------------------------------------
        subnotebook = ttk.Notebook(self.tab_usuario)
        subnotebook.pack(fill="both", expand=True, padx=10, pady=10) 

        tab_auth = Frame(subnotebook)
        tab_reg = Frame(subnotebook)

        subnotebook.add(tab_auth, text="Autenticar ")
        subnotebook.add(tab_reg, text="Registrar ")
        #------------------------------------------------------------

        # Sub-Pestaña: Autenticar-------------------------------------
        lbl = Label(tab_auth, text="Acceder al sistema", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=15)

        btn_sel = Button(tab_auth, text="Seleccionar ojo", command=lambda: self.SeleccionarArchivo(mode="auth"))
        btn_sel.pack(pady=5)

        self.lbl_ruta_auth = Label(tab_auth, text="No hay imagen seleccionada", fg="gray", wraplength=500)
        self.lbl_ruta_auth.pack()

        self.btn_run_auth = Button(tab_auth, text="Autenticar", command=self.EjecutarAutenticacion,
                              bg="#2196F3", fg="black", disabledforeground="#FFFFFF", 
                              font=("Helvetica", 11, "bold"), state="disabled")
        self.btn_run_auth.pack(pady=20, fill="x", padx=50)
        #------------------------------------------------------------

        # Sub-Pestaña: Registrar--------------------------------------
        lbl = Label(tab_reg, text="Registrar nuevo usuario", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=15)

        frame_id = Frame(tab_reg)
        frame_id.pack(pady=5)
        Label(frame_id, text="ID Usuario:").pack(side="left", padx=5)
        self.ent_id_reg = Entry(frame_id, width=20)
        self.ent_id_reg.pack(side="left", padx=5)

        btn_sel = Button(tab_reg, text="Seleccionar ojo", command=lambda: self.SeleccionarArchivo(mode="reg"))
        btn_sel.pack(pady=5)

        self.lbl_ruta_reg = Label(tab_reg, text="No hay imagen seleccionada", fg="gray", wraplength=500)
        self.lbl_ruta_reg.pack()

        self.btn_run_reg = Button(tab_reg, text="Registrar", command=self.EjecutarRegistro,
                              bg="#2196F3", fg="white", disabledforeground="#FFFFFF", 
                              font=("Helvetica", 11, "bold"), state="disabled")
        self.btn_run_reg.pack(pady=20, fill="x", padx=50)
        #------------------------------------------------------------
    def SetupTabGestionBD(self):
        #------------------------------------------------------------
        subnotebook = ttk.Notebook(self.tab_gestion)
        subnotebook.pack(fill="both", expand=True, padx=10, pady=10) 

        tab_reg_carpeta = Frame(subnotebook)
        tab_eliminar_usuario = Frame(subnotebook)
        tab_eliminarBD = Frame(subnotebook)

        subnotebook.add(tab_reg_carpeta, text="Registrar carpeta")
        subnotebook.add(tab_eliminar_usuario, text="Eliminar usuario")
        subnotebook.add(tab_eliminarBD, text="Eliminar BD")
        #------------------------------------------------------------

        # Sub-Pestaña: Registrar Carpeta-------------------------------------
        lbl = Label(tab_reg_carpeta, text="Registrar carpeta CASIA", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=15)

        btn_reg_carpeta = Button(tab_reg_carpeta, text="Seleccionar carpeta CASIA", command=lambda: self.SeleccionarCarpeta(mode="reg_carpeta"))
        btn_reg_carpeta.pack(pady=10)

        self.lbl_ruta_reg_carpeta = Label(tab_reg_carpeta, text="No hay carpeta seleccionada", fg="gray", wraplength=500)
        self.lbl_ruta_reg_carpeta.pack()

        self.btn_run_reg_carpeta = Button(tab_reg_carpeta, text="Registrar", command=self.EjecutarRegistroMasivo,
                              bg="#2196F3", fg="white", font=("Helvetica", 11, "bold"))
        self.btn_run_reg_carpeta.pack(pady=20, fill="x", padx=50)
        #------------------------------------------------------------

        # Sub-Pestaña: Eliminar Usuario-------------------------------------
        lbl = Label(tab_eliminar_usuario, text="Eliminar Usuario", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=15)

        frame_id_elim = Frame(tab_eliminar_usuario)
        frame_id_elim.pack(pady=5)
        Label(frame_id_elim, text="ID Usuario:").pack(side="left", padx=5)
        self.ent_id_elim = Entry(frame_id_elim, width=20)
        self.ent_id_elim.pack(side="left", padx=5,pady=15)        

        self.btn_run_eliminar_usuario = Button(tab_eliminar_usuario, text="Eliminar", command=self.EjecutarEliminarUsuario,
                              bg="#D40D0D", fg="white", font=("Helvetica", 11, "bold"))
        self.btn_run_eliminar_usuario.pack(pady=28, fill="x", padx=50)
        #------------------------------------------------------------

        # Sub-Pestaña: Eliminar BD-------------------------------------
        lbl = Label(tab_eliminarBD, text="Vaciar Base de Datos", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=15)

        self.btn_run_eliminarBD = Button(tab_eliminarBD, text="Vaciar", command=self.EjecutarEliminarBD,
                              bg="#D40D0D", fg="white", font=("Helvetica", 11, "bold"))
        self.btn_run_eliminarBD.pack(pady=87, fill="x", padx=50)
        #------------------------------------------------------------


    def SetupTabBenchmarks(self):

        #------------------------------------------------------------
        subnotebook = ttk.Notebook(self.tab_benchmarks)
        subnotebook.pack(fill="both", expand=True, padx=10, pady=10) 

        tab_stats =Frame(subnotebook)
        tab_tiempo = Frame(subnotebook)

        subnotebook.add(tab_stats, text="Estadísticas ")
        subnotebook.add(tab_tiempo, text="Tiempo ")
        #------------------------------------------------------------

        # Sub-Pestaña: Estadísticas-------------------------------------
        lbl = Label(tab_stats, text="Realizar test de precisión", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=15)

        frame_muestras = Frame(tab_stats)
        frame_muestras.pack(pady=5)
        Label(frame_muestras, text="Número de muestras:").pack(side="left", padx=5)

        self.ent_muestras = Entry(frame_muestras, width=15)
        self.ent_muestras.insert(0, "100") # Valor por defecto
        self.ent_muestras.pack(side="left", padx=5)

        btn_sel_stats = Button(tab_stats, text="Seleccionar carpeta CASIA", command=lambda: self.SeleccionarCarpeta(mode="stats"))
        btn_sel_stats.pack(pady=10)

        self.lbl_ruta_stats = Label(tab_stats, text="No hay carpeta seleccionada", fg="gray", wraplength=500)
        self.lbl_ruta_stats.pack()

        # Nueva variable única para el botón
        self.btn_run_stats = Button(tab_stats, text="Iniciar", command=self.EjecutarBenchmarkEstadisticas,
                              bg="#2196F3", fg="white", font=("Helvetica", 11, "bold"))
        self.btn_run_stats.pack(pady=20, fill="x", padx=50)
        #------------------------------------------------------------

        # Sub-Pestaña: Tiempo--------------------------------------
        lbl = Label(tab_tiempo, text="Realizar test de rendimiento", font=("Helvetica", 14, "bold"))
        lbl.pack(pady=15)

        frame_id = Frame(tab_tiempo)
        frame_id.pack(pady=5)
        Label(frame_id, text="Iteraciones:").pack(side="left", padx=5)
        self.ent_iter = Entry(frame_id, width=15)
        self.ent_iter.insert(0, "100") # Valor por defecto
        self.ent_iter.pack(side="left", padx=5)

        # Botón y etiqueta para seleccionar carpeta de tiempos
        btn_sel_tiempo = Button(tab_tiempo, text="Seleccionar carpeta CASIA", command=lambda: self.SeleccionarCarpeta(mode="tiempo"))
        btn_sel_tiempo.pack(pady=10)

        self.lbl_ruta_tiempo = Label(tab_tiempo, text="No hay carpeta seleccionada", fg="gray", wraplength=500)
        self.lbl_ruta_tiempo.pack()

        self.btn_run_tiempo = Button(tab_tiempo, text="Iniciar", command=self.EjecutarBenchmarkTiempo,
                              bg="#2196F3", fg="white", font=("Helvetica", 11, "bold"))
        self.btn_run_tiempo.pack(pady=20, fill="x", padx=50)
        #------------------------------------------------------------
    
    # Lógica de Autenticación
    def EjecutarAutenticacion(self):
        self.EnviarMensajePanel("Procesando...", "blue")
        self.root.update()
        try:
                from usuario.autenticar import Autenticar

                res = Autenticar(self.img_auth)
                if res == -1:
                    self.EnviarMensajePanel("Base de datos vacía.", "red")
                    messagebox.showerror("Error", "La base de datos está vacía. Registra a alguien primero.")
                    return
                if res == 0:
                    self.EnviarMensajePanel("ACCESO DENEGADO\nNo hay coincidencias en el sistema.", "red")
                    return
                
                nom, dist = res
                self.EnviarMensajePanel(f"ACCESO CONCEDIDO\nID: {nom}\nDistancia: {dist:.4f}", "green")
            
        except Exception as e:
            messagebox.showwarning("Fallo en Segmentación", f"\n{e}")
            self.EnviarMensajePanel("Error de detección.", "red")

    # Lógica de Registro
    def EjecutarRegistro(self):
        user_id = self.ent_id_reg.get().strip()
        if not user_id:
            messagebox.showwarning("Atención", "Debes introducir un ID de usuario.")
            return
        
        self.EnviarMensajePanel("Segmentando ojo...", "blue")
        self.root.update()

        try:
            from cv2 import destroyWindow, destroyAllWindows, imshow
            from usuario.registrarIris import Registrar
            from usuario.detectar import Detectar
            
            res = Detectar(self.img_reg)
            if res == -1:
                self.EnviarMensajePanel("Imagen no encontrada o formato inválido.","red")
                messagebox.showerror("Error", "Imagen no encontrada o formato inválido.")
                return
            if res == -2:
                self.EnviarMensajePanel("La imagen no parece ser un ojo humano.", "red")
                messagebox.showerror("Error", "La imagen no parece ser un ojo humano.")
                return
            
            img_color, _, _ = res

            self.EnviarMensajePanel("Visualizando detección...","blue")
            self.root.update()
            imshow("Resultado:", img_color)
            
            # Pedir confirmación al usuario
            if messagebox.askyesno("Validación Visual", "¿Es correcta la detección de pupila e iris?"):
                destroyWindow(f"Resultado:")
                
                self.EnviarMensajePanel("⏳ Generando plantilla...","blue")
                self.root.update()

                _ = Registrar(self.img_reg, user_id)
                
                self.EnviarMensajePanel(f"REGISTRO EXITOSO\nUsuario {user_id} guardado.","green")
            else:
                destroyWindow(f"Resultado:")
                self.EnviarMensajePanel("Registro cancelado por el usuario.","orange")

        except Exception as e:
            destroyAllWindows()
            messagebox.showerror("Error", f"No se pudo completar el registro:\n{e}")
            self.EnviarMensajePanel("Fallo al registrar.","red")
    def EjecutarRegistroMasivo(self):
        if not self.img_reg_carpeta:
            messagebox.showwarning("Atención", "Debes seleccionar una carpeta con imágenes primero.")
            return
    
        self.EnviarMensajePanel(f"Registrando carpeta...", "blue")
        self.root.update()
        try:
            from gestorBD.registrarCarpetaUbiris import RealizarRegistroParalelo
            from constantes import RUTA_BD

            self.EnviarMensajePanel("Registrando usuarios...","blue")
            self.root.update()
            exitos, errores = RealizarRegistroParalelo(
                4, 
                self.img_reg_carpeta, 
                RUTA_BD,
                callback=self.EnviarMensajePanel)

            self.EnviarMensajePanel(f"{exitos} imágenes registradas.\n{errores} imágenes falladas.","blue")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo completar el registro:\n{e}")
            self.EnviarMensajePanel("Fallo al registrar.","red")


    def EjecutarEliminarUsuario(self):
        user_id_elim = self.ent_id_elim.get().strip()
        if not user_id_elim:
            messagebox.showwarning("Atención", "Debes introducir un ID de usuario.")
            return
        
        self.EnviarMensajePanel("Eliminando usuario...", "blue")
        self.root.update()

        try:
            from gestorBD.eliminar import EliminarUsuarioBD
            res = EliminarUsuarioBD(user_id_elim)
            if not res:
                self.EnviarMensajePanel(f"La base de datos no existe.", "red")
            
            if res == 0:
                self.EnviarMensajePanel(f"El usuario no existe o BD vacía.", "orange")
            else:
                self.EnviarMensajePanel(f"Usuario {user_id_elim} eliminado.", "red")

        except Exception as e:
            messagebox.showerror("Error", f"Error eliminando el usuario:\n{e}")
            self.EnviarMensajePanel("Fallo","red")    


    def EjecutarEliminarBD(self):
        if messagebox.askyesno("Advertencia", "¿Estás seguro de que quieres BORRAR TODOS los usuarios registrados?", 
                icon="warning"):
            try:
                from gestorBD.eliminar import EliminarBD

                if not EliminarBD():
                    self.EnviarMensajePanel("La carpeta de la base de datos no existe.", "red")
                else:
                    self.EnviarMensajePanel(f"Base de datos purgada.", "red")
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando la base de datos:\n{e}")
                self.EnviarMensajePanel("Fallo","red")
        else:
            self.EnviarMensajePanel("Operación cancelada.", "orange")
    
    def EjecutarBenchmarkEstadisticas(self):
        if not self.img_stats:
            messagebox.showwarning("Atención", "Debes seleccionar una carpeta con imágenes primero.")
            return
        
        muestras = self.ent_muestras.get().strip()
        if not muestras.isdigit() or int(muestras) <= 0:
            messagebox.showwarning("Atención", "Debes introducir un número de muestras válido.")
            return

        muestras = int(muestras)
        self.EnviarMensajePanel(f"Ejecutando evaluación con {muestras} muestras...", "blue")
        self.root.update()

        try:
            from constantes import UMBRAL_DIST_HM
            
            plt.close('all')  
            from benchmarks.estadisticas import ObtenerImagenesEstadisticas, ObtenerEstadisticas, GenerarGraficoEstadisticas

            todas_imagenes = ObtenerImagenesEstadisticas(self.img_stats)

            if not todas_imagenes:
                messagebox.showerror("Error", "No se encontraron imágenes en la carpeta de entrada.")
                self.EnviarMensajePanel("Error: Sin imágenes para el test.", "red")
                return

            stats = ObtenerEstadisticas(todas_imagenes, muestras, UMBRAL_DIST_HM,self.EnviarMensajePanel)
            
            self.EnviarMensajePanel("Evaluación finalizada. Generando gráfico...", "green")
            
            # Generar y mostrar el gráfico
            fig = GenerarGraficoEstadisticas(stats, muestras, UMBRAL_DIST_HM)
            plt.show()
            plt.close('all')  

        except Exception as e:
            plt.close('all')
            messagebox.showerror("Error", f"Fallo al ejecutar estadísticas:\n{e}")
            self.EnviarMensajePanel("Error en test estadístico.", "red")

    def EjecutarBenchmarkTiempo(self):
        if not self.img_tiempo:
            messagebox.showwarning("Atención", "Debes seleccionar una carpeta con imágenes primero.")
            return
        
        iter_id = self.ent_iter.get().strip()
        if not iter_id.isdigit() or int(iter_id) <= 0:
            messagebox.showwarning("Atención", "Debes introducir un número entero de iteraciones.")
            return
        
        iter_id = int(iter_id)
        self.EnviarMensajePanel(f"Procesando {iter_id} iteraciones...", "blue")
        self.root.update()

        try:
            from benchmarks.tiempos import ObtenerImagenes, MedicionTiempos, GenerarGraficoTiempos
            

            todas_imagenes = ObtenerImagenes(self.img_tiempo)

            if not todas_imagenes:
                messagebox.showerror("Error", "No se encontraron imágenes en la carpeta de entrada o formato no válido.")
                self.EnviarMensajePanel("Error: Sin imágenes para el test o formato no válido.", "red")
                return


            medicion, exitos = MedicionTiempos(todas_imagenes, iter_id,callback=self.EnviarMensajePanel)
            
            if exitos > 0:
                self.EnviarMensajePanel("Prueba de rendimiento completada.", "green")
                
                # Lanzar el gráfico visual
                fig = GenerarGraficoTiempos(medicion, exitos)
                plt.show()
            else:
                self.EnviarMensajePanel("No se completó ninguna iteración.", "orange")
        except Exception as e:
            messagebox.showerror("Error", f"\n{e}")
            self.EnviarMensajePanel("Fallo al realizar la prueba.","red")

if __name__ == "__main__":
    root = Tk()
    app = Interfaz(root)
    root.mainloop()