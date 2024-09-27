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
#import sys

# Definições de pinos para os displays, customizar conforme o modelo de display
TFT_CS = const(15)
TFT_DC = const(2)
TFT_SCK = const(14)
TFT_MOSI = const(13)
TFT_PWM = const(27)
# Definições de pinos para os SPI do cartão SD, customizar conforme o schematic
SD_CS = const(5)
SD_SCK = const(18)
SD_MOSI = const(23)
SD_MISO = const(19)

# Desligar o LED vermelho
RLED = const(4)
RLED_pin = Pin(RLED,Pin.OUT)
RLED_pin.value(1)

# Inicialização do SPI para o display TFT
def init_display():
    spi = SPI(2, baudrate=20000000, sck=Pin(TFT_SCK), mosi=Pin(TFT_MOSI))
    display = Display(spi, cs=Pin(TFT_CS), dc=Pin(TFT_DC), rst=Pin(0))
    #display.fill_rectangle(0,0,229,309,color565(255,255,255))
    pwm = PWM(Pin(TFT_PWM), freq=1000)
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
        prepare_display(display)
        display.draw_image(image_path)
        #display.draw_circle(132, 96, 70, color565(0, 255, 0))
        #sleep(9)
        #display.draw_circle(132, 96, 70, color565(255, 0, 0))
        #sleep(9)
        #display.draw_circle(132, 96, 70, color565(0, 0, 255))
        #sleep(9)
        return True
    except OSError as e:
        print("Erro ao abrir arquivo:", e)
        return False

def prepare_display(display, brightness=None, clear=True, bg_color=color565(0, 0, 0)):
    """Prepara o display para uso.
    Args:
        display: Objeto display que será manipulado.
        brightness (Optional int): Nível de brilho (0-255).
        clear (Optional bool): Se deve limpar o display (default True).
        bg_color (Optional int): Cor de fundo ao limpar o display (default preto).
    
    
    """
    #display.cleanup()

    #if display.display_off():
    #    display.display_on()  # Liga o display apenas se estiver desligado
    #display.reset_mpy
    display.clear()

    if brightness is not None:
        display.set_brightness(brightness)  # Ajusta o brilho se necessário

    if clear:
        display.clear(bg_color)  # Limpa o display com a cor de fundo escolhida

# Função para listar imagens no cartão SD
def list_images():
    try:
        return [f for f in os.listdir('/sd') if f.endswith('.jpg') or f.endswith('.raw')]
    except OSError as e:
        print("Erro ao listar arquivos:", e)
        return []


def send_notification(ble, char_handle, message, chunk_size=20):
    """
    Envia uma mensagem por BLE dividida em "chunks", adicionando perguntas de controle.
    
    :param ble: Objeto BLE para envio.
    :param char_handle: Handle da característica BLE.
    :param message: A mensagem a ser enviada.
    :param chunk_size: Tamanho máximo de cada "chunk" (20 bytes por padrão).
    """
    try:
        data = message.encode('utf-8')
        total_chunks = (len(data) + chunk_size - 1) // chunk_size  # Calcular número de chunks

        for i in range(0, len(data), chunk_size):
            chunk = message[i:i + chunk_size]  # Pegando o substring do chunk atual
            remaining_chunks = total_chunks - (i // chunk_size) - 1  # Restantes

            # Adicionar perguntas ao final do chunk com base na posição
            if remaining_chunks > 0:
                chunk += " Prosseguir[P]" if i == 0 else " Prosseguir[P], Voltar[V], Encerrar[E]"
            else:
                chunk += " Voltar[V], Encerrar[E]"

            ble.gatts_notify(0, char_handle, chunk.encode('utf-8'))

    except Exception as e:
        print(f"Erro ao enviar notificação BLE: {e}")

def welcome_page(ble, char_handle, conn_handle):
    """
    Função para enviar a mensagem de boas-vindas e opções de ação para o cliente conectado.
    
    :param ble: Objeto BLE para enviar as notificações.
    :param char_handle: Handle da característica BLE para enviar os dados.
    :param conn_handle: Handle da conexão do cliente.
    """
    try:
        # Envia mensagem de conexão
        send_notification(ble, char_handle, "Conectado!")
        
        # Aguarda 2 segundos
        time.sleep(2)

        # Envia as opções de ação
        options = (
            "1- Listar imagens [LI], "
            "2- Mostrar imagem [DI], "
            "3- Mostrar retângulo vermelho [R/r], "
            "4- Mostrar retângulo verde [G/g], "
            "5- Mostrar retângulo azul [B/b], "
            "6- Mostrar retângulo preto [BK/bk], "
            "7- Mostrar retângulo branco [W/w], "
            "8-Desconectar[D]?"
        )
        send_notification(ble, char_handle, options)

    except Exception as e:
        print(f"Ocorreu um erro na página de boas-vindas: {e}")

# Exemplo de uso
# welcome_page(ble_instance, char_handle_instance, conn_handle_instance)


# Callback para tratamento de escrita na característica BLE
def on_command_received(event, ble, display, char_handle):
    print(f"Valor escrito: ", ble.gatts_read(event[1]))
    try:
        # Lê o valor enviado pelo cliente BLE
        value = ble.gatts_read(event[1])
        command = value.decode('utf-8')
        
        # Verifica se o comando começa com 'DI:' para exibir uma imagem
        if command.startswith('DI:'):
            image_name = command.split(':')[1]
            image_path = f'/sd/{image_name}'
            if display_image(display, image_path):
                print(f"Imagem {image_name} exibida no display.")
                #ble.gatts_notify(0, char_handle, b'OK: Imagem exibida')
                message = "OK: Imagem exibida"
                send_notification(ble, char_handle, message)
            else:
                #ble.gatts_notify(0, char_handle, b'ERROR: Falha ao exibir imagem')
                message = "ERROR: Falha ao exibir imagem"
                send_notification(ble, char_handle, message)

        # Verifica se o comando é 'R' ou 'r' para exibir a tela vermelha
        elif command in ['R', 'r']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(255, 0, 0))
            print(f"Red screen displayed")
            #ble.gatts_notify(0, char_handle, b'red screen')
            message = "red screen"
            send_notification(ble, char_handle, message)

        # Verifica se o comando é 'G' ou 'g' para exibir a tela verde
        elif command in ['G', 'g']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(0, 255, 0))
            print(f"Green screen displayed")
            #ble.gatts_notify(0, char_handle, b'green screen')
            message = "green screen"
            send_notification(ble, char_handle, message)

        # Verifica se o comando é 'B' ou 'b' para exibir a tela azul
        elif command in ['B', 'b']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(0, 0, 255))
            print(f"Blue screen displayed")
            #ble.gatts_notify(0, char_handle, b'blue screen')
            message = "blue screen"
            send_notification(ble, char_handle, message)
        
        # Verifica se o comando é 'B' ou 'b' para exibir a tela azul
        elif command in ['W', 'w']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(255, 255, 255))
            print(f"White screen displayed")
            #ble.gatts_notify(0, char_handle, b'white screen')
            message = "white screen"
            send_notification(ble, char_handle, message)
        
        elif command in ['BK', 'bk']:
            prepare_display(display)
            display.fill_rectangle(0, 0, 229, 309, color565(0, 0, 0))
            print(f"Black screen displayed")
            #ble.gatts_notify(0, char_handle, b'black screen')
            message = "black screen"
            send_notification(ble, char_handle, message)

        # Verifica se o comando é 'LI' para listar imagens
        elif command == 'LI':
            images = list_images()
            images_str = ','.join(images)
            #ble.gatts_notify(0, char_handle, images_str.encode('utf-8'))
            message = images_str
            send_notification(ble, char_handle, message)
        
        elif command == 'D':
            ble.gatts_disconnect(event[0])
            print("Cliente desconectado")        
           
    except Exception as e:
        print("Erro ao processar comando:", e)
        #ble.gatts_notify(0, char_handle, b'ERROR: Falha ao processar comando')
        message = "ERROR: Falha ao processar comando"
        send_notification(ble, char_handle, message)


# Interrupção BLE
def ble_irq(event, data, ble, display, char_handle):
    global is_connected
    if event == const(3):  # Evento de escrita
        on_command_received(data, ble, display, char_handle)
    elif event == const(1):
        is_connected = True
        print("Cliente conectado via BLE!")
        welcome_page()
    elif event == const(2):
        is_connected = False
        print("Cliente desconectado do BLE.")
        advertise_ble(ble, "ESP32_Test")

# Inicialização principal
def main():
    global is_connected
    is_connected = False
    #print(sys.implementation.name)
    
    # Inicializar componentes
    display = init_display()
    init_sd()
    device_name = "ESP32_Test"
    ble = init_bluetooth(device_name)

    # Configuração do serviço BLE
    
    char_handles = setup_ble_services(ble)
    char_handle = char_handles[0]
    #ble.gatts_write(char_handle, b'command')

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