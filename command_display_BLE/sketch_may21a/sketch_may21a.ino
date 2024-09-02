#include <Arduino.h>
#include <SD.h>       // Biblioteca para manipular cartão TF (microSD)
#include <TFT_eSPI.h> // Biblioteca para display TFT

#define TFT_CS    5
#define TFT_DC    21
#define TFT_RST   -1  // Set TFT_RST to -1 if display RESET is connected to ESP32 board RST
#define SD_CS     13  // Pino CS do cartão TF

TFT_eSPI tft = TFT_eSPI(); // Inicializa o objeto para o display

BLEService imageService("0000180A-0000-1000-8000-00805F9B34FB");
BLECharacteristic commandCharacteristic("00002A7E-0000-1000-8000-00805F9B34FB", BLEWrite);

File imageFile;

void setup() {
  Serial.begin(115200);
  
  // Inicializa o cartão TF
  if (!SD.begin(SD_CS)) {
    Serial.println("Falha ao inicializar o cartão TF!");
    while (1);
  }
  Serial.println("Cartão TF inicializado.");

  // Inicializa o display
  tft.begin();
  tft.setRotation(1); // Ajuste de rotação do display, se necessário

  // Configura o Bluetooth
  BLE.begin();
  BLE.setLocalName("ESP32_Image_Display");
  BLE.setAdvertisedService(imageService);
  imageService.addCharacteristic(commandCharacteristic);
  BLE.addService(imageService);
  BLE.advertise();
  
  Serial.println("Esperando uma conexão de cliente para receber comandos...");
}

void loop() {
  BLEDevice central = BLE.central();
  
  if (central) {
    Serial.println("Cliente conectado!");
    
    while (central.connected()) {
      if (commandCharacteristic.written()) {
        std::string command = commandCharacteristic.value();
        if (command == "display_image") {
          displayImageFromSD();
        }
      }
    }
    
    Serial.println("Cliente desconectado!");
  }
}

void displayImageFromSD() {
  // Abre o arquivo de imagem do cartão TF
  imageFile = SD.open("/image.jpg");
  
  if (imageFile) {
    Serial.println("Exibindo imagem...");

    // Carrega a imagem para o display
    tft.fillScreen(TFT_BLACK); // Limpa a tela
    tft.setSwapBytes(true);    // Opcional, dependendo do formato da imagem

    // Lê e exibe os dados da imagem
    uint16_t xPos = 0;
    uint16_t yPos = 0;
    while (imageFile.available()) {
      uint8_t buf[512];
      size_t len = imageFile.read(buf, 512);
      tft.pushImage(xPos, yPos, 128, 160, buf); // Exemplo de exibição de parte da imagem
      yPos += len;
    }

    imageFile.close();
  } else {
    Serial.println("Falha ao abrir o arquivo de imagem!");
  }
}
