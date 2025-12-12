#!/usr/bin/python3
# -*- coding: UTF8 -*-
"""
@created: 17-10-2025
@author: rafael
@description: Converteix àudios a text introduits per micròfon

Instalació prèvia:
sudo apt-get install python-tk
sudo apt-get install python3-pil python3-pil.imagetk
pip3 install --user pydub speechrecognition pyaudio
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pydub import AudioSegment
import speech_recognition as sr
import threading

class AudioTranscriber:
   def __init__(self, root):
      self.root = root
      self.root.title("Dictat")
      self.root.minsize(800, 600)

      # Variables
      self.twav = "static/tmp/temp.wav"

      self.selected_language = tk.StringVar(value="ca-ES")  # Idioma per defecte
      self.dir_images = "static/img"
      self.images = {}
      self.default_state = "Fes clic al micròfon"
      self.status_text = tk.StringVar(value=self.default_state)
      self.languages = {
         "Català": "ca-ES",
         "Español": "es-ES",
         "English": "en-US"
      }

      self.carrega_imatges()
      self.create_widgets()

   def carrega_imatges(self):
      self.images['micro'] = tk.PhotoImage(file=f"{self.dir_images}/microfon.png")
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

      ttk.Button(button_frame, image=self.images['micro'], command=self.inici_gravació).pack(side=tk.LEFT, padx=5)
      ttk.Button(button_frame, image=self.images['clear'], command=self.clear_all).pack(side=tk.LEFT, padx=5)
      ttk.Button(button_frame, image=self.images['save'], command=self.save_text).pack(side=tk.LEFT, padx=5)
      ttk.Button(button_frame, image=self.images['exit'], command=self.root.destroy).pack(side=tk.LEFT, padx=(10,0))

      # Estat
      ttk.Label(main_frame, textvariable=self.status_text, font=("Arial",9,"italic")).grid(row=5, column=0, columnspan=3, sticky=(tk.N,tk.W))


   def on_language_change(self, event):
      """Actualitza l'etiqueta del codi d'idioma quan canvia la selecció"""
      selected_language_name = self.language_combo.get()
      language_code = self.languages[selected_language_name]
      self.selected_language.set(language_code)
      self.language_code_label.config(text=f"Codi: {language_code}")
      self.status_text.set(f"Idioma cambiat a: {selected_language_name}")

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
      except sr.UnknownValueError:
         self.root.after(0, self.actualitza_estat, "", f"Error: No he pogut entendre l'àudio [{self.language_combo.get()}]")
      except sr.RequestError as e:
         self.root.after(0, self.actualitza_estat, "", f"Error en el servei: {str(e)}")
      except Exception as e:
         self.root.after(0, self.actualitza_estat, "", f"Error inesperat: {str(e)}")

      return text_reconegut

   '''
   Genera un text a partir de la veu captada pel micròfon
   '''
   def escolta_microfon_wav(self):
      timeout = 0    #temps que espera a sentir veu abans de generar una Excepció
      time_limit = 0  # nombre de segons de temps per poder dir la frase

      r = sr.Recognizer()
      with sr.Microphone() as source:
          audio = r.adjust_for_ambient_noise(source)
          audio = r.listen(source, timeout=timeout, phrase_time_limit=time_limit)
          with open(self.twav, "wb") as f:
            f.write(audio.get_wav_data())

      song = AudioSegment.from_wav(self.twav)
      text_reconegut = self.reconeixement_d_audio(song, r)
      self.root.after(0, self.actualitza_estat, text_reconegut, "activa el microfon")

   '''
   Genera un text a partir de la veu captada pel micròfon
   '''
   def escolta_microfon(self):
      timeout = 3    #temps que espera a sentir veu abans de generar una Excepció
      time_limit = 20  # nombre de segons de temps per poder dir la frase

      r = sr.Recognizer()
      with sr.Microphone() as source:
         audio = r.adjust_for_ambient_noise(source)
         audio = r.listen(source, timeout=timeout, phrase_time_limit=time_limit)

      text_reconegut = self.reconeixement_d_audio(audio, r)
      self.root.after(0, self.actualitza_estat, text_reconegut, "activa el microfon")

   def inici_gravació(self):
      """Inicia el procés de gravació en un fil separat"""
      self.status_text.set(f"Escoltant [{self.language_combo.get()}]")

      # Executar en un fil separat per a no bloquejar l'interfase
      thread = threading.Thread(target=self.escolta_microfon)
      thread.daemon = True
      thread.start()

   def actualitza_estat(self, text, status):
      """Actualitza l'interfase amb el resultat del reconeixement de veu"""
      if text:
         self.text_area.insert(1.0, text)
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
