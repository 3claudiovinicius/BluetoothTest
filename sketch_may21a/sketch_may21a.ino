#include <ArduinoBLE.h>

#define REDled 4      // Pino 4 para o LED vermelho
#define GREENled 17   // Pino 17 para o LED verde
#define BLUEled 16    // Pino 16 para o LED azul

BLEService ledService("181A"); // Serviço de LED
BLEStringCharacteristic ledCharacteristic("2A56", BLERead | BLENotify, 20); // Característica para LED (máximo de 20 caracteres)

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // Inicializa os pinos dos LEDs como saída
  pinMode(REDled, OUTPUT);
  pinMode(GREENled, OUTPUT);
  pinMode(BLUEled, OUTPUT);

  // Inicializa todos os LEDs como apagados
  digitalWrite(REDled, HIGH);
  digitalWrite(GREENled, HIGH);
  digitalWrite(BLUEled, HIGH);

  // Inicializa o Bluetooth
  if (!BLE.begin()) {
    Serial.println("Falha ao inicializar o BLE!");
    while (1);
  }

  // Configura o dispositivo BLE
  BLE.setLocalName("ESP32_LED_Controller");
  BLE.setAdvertisedService(ledService);
  ledService.addCharacteristic(ledCharacteristic);
  BLE.addService(ledService);

  // Inicia a publicidade do BLE
  BLE.advertise();
  Serial.println("Esperando uma conexão de cliente para notificar...");
}

void loop() {
  // Verifica se um dispositivo BLE está conectado
  BLEDevice central = BLE.central();

  if (central) {
    Serial.println("Cliente conectado!");

    // Verifica se o serviço está disponível
    if (central.connected() && central.discoverAttributes()) {
      Serial.println("Serviços descobertos!");

      // Alterna os LEDs e envia a informação via Bluetooth e Serial
      while (central.connected()) {
        // Lógica para alternar LEDs e enviar informações
        digitalWrite(REDled, LOW);
        digitalWrite(GREENled, HIGH);
        digitalWrite(BLUEled, HIGH);
        if (!enviarInformacao("RED LED aceso")) {
          break; // Se falhar ao enviar, desconecta
        }
        delay(3000);

        // Lógica para alternar LEDs e enviar informações
        digitalWrite(REDled, HIGH);
        digitalWrite(GREENled, LOW);
        digitalWrite(BLUEled, HIGH);
        if (!enviarInformacao("GREEN LED aceso")) {
          break; // Se falhar ao enviar, desconecta
        }
        delay(3000);

        // Lógica para alternar LEDs e enviar informações
        digitalWrite(REDled, HIGH);
        digitalWrite(GREENled, HIGH);
        digitalWrite(BLUEled, LOW);
        if (!enviarInformacao("BLUE LED aceso")) {
          break; // Se falhar ao enviar, desconecta
        }
        delay(3000);
      }
    } else {
      Serial.println("Falha ao descobrir serviços. Desconectando...");
      BLE.disconnect();
    }

    Serial.println("Cliente desconectado!");
  }
}


bool enviarInformacao(const char* info) {
  Serial.print("Enviando informacao via BLE: ");
  Serial.println(info);
  bool status = ledCharacteristic.writeValue(info);
  if (!status) {
    Serial.println("Falha ao enviar informacao via BLE!");
  }
  return status;
}
