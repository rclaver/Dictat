#!/usr/bin/python3
# -*- coding: UTF8 -*-
"""
@created: 17-10-2025
@author: rafael
@description: Converteix àudios a text introduits per micròfon

Instalació prèvia:
sudo apt-get install python-tk
sudo apt-get install python3-pil python3-pil.imagetk
pip3 install --user pydub speechrecognition
"""

import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog
import speech_recognition as sr

class AudioTranscriber:
   def __init__(self, root):
      self.root = root
      self.root.title("Dictat")
      self.root.minsize(800, 600)

      # Variables
      self.selected_language = tk.StringVar(value="es-ES")  # Idioma per defecte
      self.dir_images = "static/img"
      self.images = {}
      self.default_state = "Fes clic al micròfon"
      self.status_text = tk.StringVar(value=self.default_state)
      self.languages = {
         "Català": "ca-ES",
         "Español": "es-ES",
         "English": "en-US"
      }
      # Variables para el control del hilo
      self.escolta = False
      self.audio_queue = queue.Queue()
      self.text_queue = queue.Queue()
      self.recognizer_thread = None

      self.carrega_imatges()
      self.create_widgets()
      # Iniciar el proceso de verificación de resultados
      self.verifica_resultats()

   def carrega_imatges(self):
      self.images['micro_on'] = tk.PhotoImage(file=f"{self.dir_images}/micro_on.png")
      self.images['micro_off'] = tk.PhotoImage(file=f"{self.dir_images}/micro_off.png")
      self.images['clear'] = tk.PhotoImage(file=f"{self.dir_images}/clear.png")
      self.images['save'] = tk.PhotoImage(file=f"{self.dir_images}/save.png")
      self.images['exit'] = tk.PhotoImage(file=f"{self.dir_images}/exit.png")

   def create_widgets(self):
      # Frame principal
      main_frame = ttk.Frame(self.root, padding="10")
      main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

      # Configurar grid weights
      self.root.columnconfigure(0, weight=1)
      self.root.rowconfigure(0, weight=1)
      main_frame.columnconfigure(1, weight=1)
      main_frame.rowconfigure(4, weight=1)

      # Títol
      ttk.Label(main_frame, text="Transcripció d'àudio a text", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 10))

      # Selector d'idioma
      ttk.Label(main_frame, text="Idioma:", font=("Arial",9,"bold")).grid(row=2, column=0, sticky=(tk.N,tk.W), pady=(5,10))
      language_frame = ttk.Frame(main_frame)
      language_frame.grid(row=2, column=1, sticky=(tk.N,tk.W), pady=(5,10))
      language_frame.columnconfigure(0, weight=1)

      # Combobox per seleccionar idioma
      self.language_combo = ttk.Combobox(
         language_frame,
         values=list(self.languages.keys()),
         state="readonly",
         font=("Arial",9),
         width=12
      )
      self.language_combo.grid(row=0, column=0, sticky=tk.W, padx=0)
      self.language_combo.set("Català")  # Valor per defecte

      # Vincular l'event de canvi de selecció
      self.language_combo.bind('<<ComboboxSelected>>', self.on_language_change)

      # Àrea de text per a la transcripció
      ttk.Label(main_frame, text="Transcripció:",font=("Arial",9,"bold")).grid(row=3, column=0, sticky=(tk.W, tk.N), pady=(5, 0))
      self.text_area = tk.Text(main_frame, wrap=tk.WORD, width=80, height=25)
      self.text_area.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))

      # Scrollbar de l'àrea de text
      scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.text_area.yview)
      scrollbar.grid(row=3, column=2, sticky=(tk.N, tk.S), pady=(5, 0))
      self.text_area.configure(yscrollcommand=scrollbar.set)

      # Botons de control
      button_frame = ttk.Frame(main_frame)
      button_frame.grid(row=4, column=0, columnspan=3, sticky=tk.N, pady=(15,0))

      self.micro_button = ttk.Button(button_frame, image=self.images['micro_off'], command=self.control_microfon).pack(side=tk.LEFT, padx=5)
      ttk.Button(button_frame, image=self.images['clear'], command=self.clear_all).pack(side=tk.LEFT, padx=5)
      ttk.Button(button_frame, image=self.images['save'], command=self.save_text).pack(side=tk.LEFT, padx=5)
      ttk.Button(button_frame, image=self.images['exit'], command=self.root.destroy).pack(side=tk.LEFT, padx=(10,0))

      # Estat
      ttk.Label(main_frame, textvariable=self.status_text, font=("Arial",9,"italic")).grid(row=5, column=0, columnspan=3, sticky=(tk.N,tk.W))


   def on_language_change(self, event):
      '''Actualitza l'etiqueta del codi d'idioma quan canvia la selecció'''
      selected_language_name = self.language_combo.get()
      language_code = self.languages[selected_language_name]
      self.selected_language.set(language_code)
      self.status_text.set(f"Idioma cambiat a: {selected_language_name}")
      self.root.after(100, self.verifica_resultats)

   def control_microfon(self):
      '''Inicia o deté l'escolta del micròfon'''
      if not self.escolta:
         '''Inicia el procés de gravació en un fil separat'''
         self.escolta = True
         self.status_text.set(f"Escoltant [{self.language_combo.get()}]")
         self.micro_button.config(image=self.images['micro_on'])

         # Executar en un fil separat per a no bloquejar l'interfase
         self.recognizer_thread = threading.Thread(target=self.escolta_microfon, daemon = True)
         self.recognizer_thread.start()
      else:
         '''Deté la gravació'''
         self.escolta = False
         self.micro_button.config(image=self.images['micro_off'])

         if self.recognizer_thread and self.recognizer_thread.is_alive():
            self.recognizer_thread.join(timeout=1)
         self.status_text.set(self.default_state)

   def escolta_microfon(self):
      '''Genera un text a partir de la veu captada pel micròfon'''
      timeout = 1    #temps que espera a sentir veu abans de generar una Excepció
      time_limit = 5  # nombre de segons de temps per poder dir la frase

      r = sr.Recognizer()
      with sr.Microphone() as source:
         r.adjust_for_ambient_noise(source, duration=timeout)

         while self.escolta:
            try:
               audio = r.listen(source, timeout=timeout, phrase_time_limit=time_limit)
               # Processar l'àudio en un altre fir per no bloquejar la captura
               threading.Thread(
                  target=self.reconeixement_d_audio,
                  args=(audio, r),
                  daemon=True
               ).start()

            except sr.WaitTimeoutError:
               # Timeout esperando voz, continuar escuchando
               continue
            except Exception as e:
               self.root.after(0, self.actualitza_estat, f"Error: {str(e)}")
               break

   '''
   Transforma un audio en text (utilitza speech_recognition)
   @type audio: AudioSource; audio d'entrada que es vol convertir a text
   @type r: Recognizer; instància de speech_recognition.Recognizer()
   '''
   def reconeixement_d_audio(self, audio, r):
      text_reconegut = ""
      try:
         # Google Speech Recognition. For testing purposes, we're just using the default API key
         # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
         text_reconegut = r.recognize_google(audio, language=self.selected_language.get())
         text_processat = self.processamet_de_text(text_reconegut)
         # Envia el text a la cua per que el fil principal el processi
         self.text_queue.put(text_processat)

      except sr.UnknownValueError:
         self.root.after(0, self.actualitza_estat, f"No he pogut entendre l'àudio [{self.language_combo.get()}]")
      except sr.RequestError as e:
         self.root.after(0, self.actualitza_estat, f"Error en el servei: {str(e)}")
      except Exception as e:
         self.root.after(0, self.actualitza_estat, f"Error inesperat: {str(e)}")

      return text_reconegut

   def processamet_de_text(self, text):
      text = text.replace(" punto y coma ", "; ")
      text = text.replace(" punto ", ". ")
      text = text.replace(" coma ", ", ")
      text = text.replace(" abre paréntesis ", " (")
      text = text.replace(" cierra paréntesis ", ") ")
      return text

   def verifica_resultats(self):
      '''Verifica periódicament si hi ha nous textos reconeguts'''
      try:
         while not self.text_queue.empty():
            text = self.text_queue.get_nowait()
            self.text_area.insert(tk.END, text + " ")
            # desplaçament al final
            self.text_area.see(tk.END)
      except queue.Empty:
         pass

      # Programar pròxima verificació
      self.root.after(100, self.verifica_resultats)

   def actualitza_estat(self, status):
      """Actualitza l'interfase amb el resultat del reconeixement de veu"""
      self.status_text.set(status)

   def clear_all(self):
      """Neteja tota l'interfase"""
      self.text_area.delete(1.0, tk.END)
      self.status_text.set(self.default_state)

   def save_text(self):
      """Desa la transcripció en un arxiu de text"""
      text = self.text_area.get(1.0, tk.END).strip()
      if not text:
         self.status_text.set("No hi ha text per desar")
         return

      # Diàlog per definir la ruta i nom de l'arxiu a desar
      file_path = filedialog.asksaveasfilename(
         title="Desar la transcripció",
         defaultextension=".txt",
         filetypes=[("Arxius de text", "*.txt"), ("Tots els arxius", "*.*")]
      )
      if file_path:
         try:
            with open(file_path, 'w', encoding='utf-8') as file:
               file.write(text)
            self.status_text.set(f"Transcripció desada a: {file_path}")
         except Exception as e:
            self.status_text.set(f"Error en desar: {str(e)}")


def main():
   root = tk.Tk()
   AudioTranscriber(root)
   root.mainloop()

if __name__ == "__main__":
   main()
