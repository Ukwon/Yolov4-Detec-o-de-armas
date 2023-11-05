import cv2
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# Caminho para o modelo YOLOv4 e seus arquivos de configuração
model_cfg = "C:/Users/dudum/OneDrive/Documentos/yolov4/yolov4-obj.cfg"
model_weights = "C:/Users/dudum/OneDrive/Documentos/yolov4/backup/yolov4-obj_6000.weights"
net = cv2.dnn.readNet(model_weights, model_cfg)

# Carregando nomes das classes
classes = []
with open("C:/Users/dudum/OneDrive/Documentos/yolov4/data/obj.names", "r") as f:
    classes = f.read().strip().split("\n")

# Variável para controlar o estado de envio do email
enviado = False
# Variável de arquivo
opcao = ""

# Função para selecionar um arquivo de vídeo ou imagem
def selec_arquivo():
    global opcao
    caminho = filedialog.askopenfilename()
    if caminho:
        opcao = caminho

# Função para iniciar a detecção
def detectar():
    global opcao
    if choice.get() == 0:
        # Evita a detecção sem opção selecionada
        messagebox.showerror("Erro", "Nenhum tipo de detecção foi selecionado.")
        return
    if choice.get() == 1 and not opcao:
        # Evita a detecção sem um arquivo selecionado no modo de arquivo
        messagebox.showerror("Erro", "Nenhum arquivo selecionado.")
        return        
    # Variável para controlar o estado de envio do email
    global enviado
    enviado = False
    cap = cv2.VideoCapture(opcao)
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Sai do loop quando a captura termina
        frame = detect_objects(frame)
        cv2.imshow("Deteccao de Objetos", frame)
        cv2.putText(frame, "Pressione 'q' para cancelar a deteccao", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Deteccao de Objetos", frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Configuração do e-mail
email_user = "masqueico901@gmail.com"  # Seu endereço de e-mail Gmail
email_password = "alpjjnwhiiwcfvtw"  # Sua senha
email_send = "eduardobromattim@gmail.com"  # Endereço de e-mail de destino

# Função para enviar e-mail com a imagem
def enviar_email(image_path):
    subject = "Alerta de Detecção de Objeto"
    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = email_send
    msg["Subject"] = subject

    # Corpo do e-mail (mensagem de texto)
    body = "Um objeto suspeito foi detectado. Verifique a imagem anexa."
    msg.attach(MIMEText(body, "plain"))

    # Anexando a imagem
    image = open(image_path, "rb").read()
    image_attachment = MIMEImage(image, name="detected_object.jpg")
    msg.attach(image_attachment)

    # Enviar o e-mail
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email_user, email_password)
    text = msg.as_string()
    server.sendmail(email_user, email_send, text)
    server.quit()

# Função para detecção de objetos e desenho de retângulos
def detect_objects(frame):
  global enviado  # Variável para controlar o envio único de email
  blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
  net.setInput(blob)
  layer_names = net.getUnconnectedOutLayersNames()
  outs = net.forward(layer_names)

  class_ids = []
  confidences = []
  boxes = []
  width, height = frame.shape[1], frame.shape[0]

  for out in outs:
      for detection in out:
          scores = detection[5:]
          class_id = np.argmax(scores)
          confidence = scores[class_id]
          if confidence > 0.5:
              center_x, center_y, w, h = (detection[0:4] * np.array([width, height, width, height])).astype(int)
              x, y = int(center_x - w / 2), int(center_y - h / 2)
              boxes.append([x, y, int(w), int(h)])
              confidences.append(float(confidence))
              class_ids.append(class_id)

  indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

  for i in range(len(boxes)):
      if i in indexes:
          x, y, w, h = boxes[i]
          label = str(classes[class_ids[i]])
          confidence = confidences[i]
          # Defina a cor de fundo da label (por exemplo, amarelo)
          label_background_color = (154, 250, 0)  # No formato BGR (azul, verde, vermelho)

          # Defina a cor do retângulo que envolve o objeto (por exemplo, vermelho)
          rectangle_color = (154, 250, 0)  # No formato BGR (azul, verde, red)

          # Desenhe o retângulo que envolve o objeto
          cv2.rectangle(frame, (x, y), (x + w, y + h), rectangle_color, 2)

          # Determine as dimensões do texto da label
          (label_width, label_height), baseline = cv2.getTextSize(f"{label} {confidence:.2f}", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)

          # Calcule a posição para o retângulo da label
          label_x = x
          label_y = y - baseline

          # Desenhe o retângulo da label
          cv2.rectangle(frame, (label_x, label_y), (label_x + label_width, label_y - label_height), label_background_color, -1)

          # Adicione o texto da label
          cv2.putText(frame, f"{label} {confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)  # Cor do texto da label (preto)

          if not enviado:
              # Salvar a imagem com o objeto destacado
              cv2.imwrite("objeto_detectado.jpg", frame)
              # Enviar e-mail com a imagem
              enviar_email("objeto_detectado.jpg")
              enviado = True  # Marcar o email como enviado

  return frame

# Configuração da janela Tkinter
root = tk.Tk()
root.title("Detecção de Objetos")

# Botão para selecionar um arquivo
select_button = tk.Button(root, text="Selecionar Arquivo", command=selec_arquivo)
select_button.pack()

# Radiobutton para escolher entre arquivo e câmera em tempo real
choice = tk.IntVar()
file_radio = tk.Radiobutton(root, text="Arquivo", variable=choice, value=1)
file_radio.pack()

def update_opcao():
    global opcao
    opcao = 0

camera_radio = tk.Radiobutton(root, text="Câmera em Tempo Real", variable=choice, value=2, command=update_opcao)
camera_radio.pack()

# Botão para iniciar a detecção
start_button = tk.Button(root, text="Iniciar Detecção", command=detectar)
start_button.pack()

# Iniciar a interface Tkinter
root.mainloop()