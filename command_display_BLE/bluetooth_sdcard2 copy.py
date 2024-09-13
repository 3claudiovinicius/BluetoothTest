"""# Import bibliotecas
import machine
from machine import Pin, SPI, PWM
from sdcard import SDCard
import os
import time
from ili9341 import Display, color565
import bluetooth
from micropython import const
from time import sleep
from sys import implementation

# Definições de pinos
TFT_CS = const(15)
TFT_DC = const(2)
TFT_SCK = const(14)
TFT_MOSI = const(13)

SD_CS = const(5)
SD_SCK = const(18)
SD_MOSI = const(23)
SD_MISO = const(19)

print(sys.implementation.name)

# Inicialização do SPI para o display TFT
#spi = SPI(2, baudrate=20000000, sck=Pin(TFT_SCK), mosi=Pin(TFT_MOSI))
spi=SPI(2, baudrate=20000000, sck=Pin(TFT_SCK), mosi=Pin(TFT_MOSI))
display = Display(spi, cs=Pin(15), dc=Pin(2), rst=Pin(0))
#liga o backlight
pwm_pin=Pin(const(27))
pwm=PWM(pwm_pin,freq=1000)
pwm.duty(1023)

# Inicialização do SPI para o cartão SD
spi2 = SPI(1, baudrate=20000000, sck=Pin(SD_SCK), mosi=Pin(SD_MOSI), miso=Pin(SD_MISO))

# Função para inicializar o cartão SD e montar o sistema de arquivos
def init_sd():
    try:
        sd = SDCard(spi2, Pin(SD_CS))
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
        return vfs
    except Exception as e:
        print("Erro ao inicializar o cartão SD:", e)
        return None
# Inicialização do cartão SD
sd = init_sd()

# Configuração do Bluetooth
device_name="ESP32_Test"
ble = bluetooth.BLE()
ble.active(True)
#ble.config(rxbuf=1024)
ble.config(gap_name='device_name')
ble.config('gap_name')
# Serviço e Característica BLE usando UUIDs curtos
SERVICE_UUID = bluetooth.UUID(0x180A)
CHARACTERISTIC_UUID = bluetooth.UUID(0x2A00)
characteristics = (
    (CHARACTERISTIC_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),
)
command_char = (
    (SERVICE_UUID, characteristics),
)
# Configuração do serviço BLE
srv = ble.gatts_register_services(command_char)

adv_data = bytearray([
    0x02, 0x01, 0x06,  # Flags
    0x03, 0x03, 0x0D, 0x18,  # Complete List of 16-bit Service Class UUIDs
    len(device_name) + 1, 0x09  # Length of local name field + type of local name
]) + device_name.encode('utf-8')

char_handles = srv[0]
char_handle=char_handles[0]
ble.gatts_write(char_handle, b'command')

# Inicia a publicidade
ble.gap_advertise(100, adv_data)

print("BLE ativo e serviço registrado.")

# Função para exibir imagem do cartão SD no display
def display_image(image_path):
    try:
        # Limpar a tela antes de desenhar a nova imagem
        
        # Usar a função draw_image para desenhar a imagem no display
        #display.draw_image(image_path, x=0, y=0, w=320, h=240)
        display.draw_circle(132, 96, 70,color565(0,255,0))
        sleep(9)
        display.draw_circle(132, 96, 70,color565(255,0,0))
        sleep(9)
        display.draw_circle(132, 96, 70,color565(0,0,255))
        sleep(9)

        return True
    except OSError as e:
        print("Erro ao abrir arquivo:", e)
        return False
# Função para listar imagens no cartão SD
def list_images():
    try:
        return [f for f in os.listdir('/sd') if f.endswith('.jpg') or f.endswith('.png')]
    except OSError as e:
        print("Erro ao listar arquivos:", e)
        return []
		
# Callback para tratamento de escrita na característica BLE
def on_command_received(event):
    print(f"Valor escrito: ", ble.gatts_read(event[1]))
    try:
        value = ble.gatts_read(event[1])  # Geralmente os dados estão no terceiro item do evento
        command = value.decode('utf-8') # Alterar essa parte para ble.gatts_read(event[1])
        
        if command.startswith('DI:'):
            image_name = command.split(':')[1]
            print('Comando para exibir imagem recebido')
            image_path = f'/sd/{image_name}'
            if display_image(image_path):
                print(f"Imagem {image_name} exibida no display.")
                ble.gatts_notify(0, char_handle, b'OK: Imagem exibida')
            else:
                print(f"Falha ao exibir imagem {image_name} no display.")
                ble.gatts_notify(0, char_handle, b'ERROR: Falha ao exibir imagem')
        elif command == 'LI':
            images = list_images()
            print('Comando para listar imagens recebido')
            images_str = ','.join(images)
            ble.gatts_notify(0, char_handle, images_str.encode('utf-8'))
    except Exception as e:
        print("Erro ao processar comando:", e)
        ble.gatts_notify(0, char_handle, b'ERROR: Falha ao processar comando')
		
is_connected = False

def ble_irq(event, data):
    global is_connected
    if event == const(3):  # Evento de escrita
        print("Evento de escrita")
        on_command_received(data)
    elif event == const(1):
        print("Cliente conectado via BLE!")
        is_connected = True
    elif event == const(2):
        print("Aguardando conexão BLE...")
        is_connected = False


# Registra a função de interrupção fora do loop principal
ble.irq(ble_irq)

# Loop principal
while True:
    if is_connected==False:
        print("Esperando nova conexão...")
    time.sleep(1)"""

#<===============================================
# Importação de bibliotecas
import machine
from machine import Pin, SPI, PWM
from sdcard import SDCard
import os
import time
from ili9341 import Display, color565
import bluetooth
from micropython import const
from time import sleep
import sys

# Definições de pinos
TFT_CS = const(15)
TFT_DC = const(2)
TFT_SCK = const(14)
TFT_MOSI = const(13)
SD_CS = const(5)
SD_SCK = const(18)
SD_MOSI = const(23)
SD_MISO = const(19)

# Inicialização do SPI para o display TFT
def init_display():
    spi = SPI(2, baudrate=20000000, sck=Pin(TFT_SCK), mosi=Pin(TFT_MOSI))
    display = Display(spi, cs=Pin(TFT_CS), dc=Pin(TFT_DC), rst=Pin(0))
    display.fill_rectangle(0,0,229,309,color565(255,255,255))
    pwm_pin = Pin(const(27))
    pwm = PWM(pwm_pin, freq=1000)
    pwm.duty(1023)  # Liga o backlight
    return display

# Inicialização do SPI para o cartão SD
def init_sd():
    try:
        spi2 = SPI(1, baudrate=20000000, sck=Pin(SD_SCK), mosi=Pin(SD_MOSI), miso=Pin(SD_MISO))
        sd = SDCard(spi2, Pin(SD_CS))
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
        return vfs
    except Exception as e:
        print("Erro ao inicializar o cartão SD:", e)
        return None

# Inicialização do Bluetooth
def init_bluetooth(device_name):
    ble = bluetooth.BLE()
    ble.active(True)
    ble.config(gap_name=device_name)
    return ble

# Publicidade BLE
def advertise_ble(ble, device_name):
    adv_data = bytearray([
        0x02, 0x01, 0x06,  # Flags
        0x03, 0x03, 0x0D, 0x18,  # Complete List of 16-bit Service Class UUIDs
        len(device_name) + 1, 0x09  # Length of local name field + type of local name
    ]) + device_name.encode('utf-8')

    ble.gap_advertise(100, adv_data)

# Configuração de serviços e características BLE
def setup_ble_services(ble):
    SERVICE_UUID = bluetooth.UUID(0x180A)
    CHARACTERISTIC_UUID = bluetooth.UUID(0x2A00)
    characteristics = (
        (CHARACTERISTIC_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),
    )
    service = (
        (SERVICE_UUID, characteristics),
    )
    srv = ble.gatts_register_services(service)
    return srv[0]

# Função para exibir imagem do cartão SD no display
def display_image(display, image_path):
    try:
        display.draw_circle(132, 96, 70, color565(0, 255, 0))
        sleep(9)
        display.draw_circle(132, 96, 70, color565(255, 0, 0))
        sleep(9)
        display.draw_circle(132, 96, 70, color565(0, 0, 255))
        sleep(9)
        return True
    except OSError as e:
        print("Erro ao abrir arquivo:", e)
        return False

# Função para listar imagens no cartão SD
def list_images():
    try:
        return [f for f in os.listdir('/sd') if f.endswith('.jpg') or f.endswith('.png')]
    except OSError as e:
        print("Erro ao listar arquivos:", e)
        return []

# Callback para tratamento de escrita na característica BLE
def on_command_received(event, ble, display, char_handle):
    try:
        value = ble.gatts_read(event[1])
        command = value.decode('utf-8')
        
        if command.startswith('DI:'):
            image_name = command.split(':')[1]
            image_path = f'/sd/{image_name}'
            if display_image(display, image_path):
                print(f"Imagem {image_name} exibida no display.")
                ble.gatts_notify(0, char_handle, b'OK: Imagem exibida')
            else:
                ble.gatts_notify(0, char_handle, b'ERROR: Falha ao exibir imagem')
        elif command == 'LI':
            images = list_images()
            images_str = ','.join(images)
            ble.gatts_notify(0, char_handle, images_str.encode('utf-8'))
    except Exception as e:
        print("Erro ao processar comando:", e)
        ble.gatts_notify(0, char_handle, b'ERROR: Falha ao processar comando')

# Interrupção BLE
def ble_irq(event, data, ble, display, char_handle):
    global is_connected
    if event == const(3):  # Evento de escrita
        on_command_received(data, ble, display, char_handle)
    elif event == const(1):
        is_connected = True
        print("Cliente conectado via BLE!")
    elif event == const(2):
        is_connected = False
        print("Cliente desconectado do BLE.")

# Inicialização principal
def main():
    global is_connected
    is_connected = False
    #print(sys.implementation.name)
    
    # Inicializar componentes
    display = init_display()
    sd = init_sd()
    device_name = "ESP32_Test"
    ble = init_bluetooth(device_name)

    # Configuração do serviço BLE
    
    char_handle = setup_ble_services(ble)

    # Iniciar publicidade
    advertise_ble(ble, device_name)
    print("BLE ativo e serviço registrado.")

    # Registra a interrupção BLE
    ble.irq(lambda event, data: ble_irq(event, data, ble, display, char_handle))

    # Loop principal
    while True:
        if not is_connected:
            print("Esperando nova conexão...")
        time.sleep(1)

# Executa o programa
if __name__ == "__main__":
    main()
