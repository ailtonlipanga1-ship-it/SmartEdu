#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

// ============================================================
// SMARTEDU RFID - ESP32 + RC522
// Desenvolvido para o sistema SmartEdu Access
// ============================================================

// -------------------- RC522 --------------------
#define SS_PIN 5
#define RST_PIN 22

MFRC522 rfid(SS_PIN, RST_PIN);

// -------------------- Sinais --------------------
#define LED_GREEN 26
#define LED_RED 27
#define BUZZER 25

// -------------------- Wi-Fi --------------------
const char* WIFI_SSID = "NOME_DA_TUA_WIFI";
const char* WIFI_PASSWORD = "PASSWORD_DA_TUA_WIFI";

// -------------------- SmartEdu --------------------
// ATENÇÃO:
// Este endereço será substituído pelo IP do computador
// onde o Flask SmartEdu estiver a executar.
const char* SERVER_URL =
    "http://IP_DO_PC:5000/api/v1/device/scan";

// Token exclusivo do dispositivo.
// Será criado pelo SmartEdu posteriormente.
const char* DEVICE_TOKEN =
    "COLOCAR_DEVICE_TOKEN_AQUI";

// Identificação deste leitor.
const char* DEVICE_CODE =
    "RFID-GW-001";

// -------------------- Configuração --------------------
const unsigned long WIFI_TIMEOUT = 20000;
const unsigned long CARD_COOLDOWN = 1500;

String lastUID = "";
unsigned long lastScanTime = 0;


// ============================================================
// SINAL DE ACESSO AUTORIZADO
// ============================================================

void signalGranted()
{
    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN, HIGH);

    tone(BUZZER, 2000, 150);

    delay(700);

    digitalWrite(LED_GREEN, LOW);
}


// ============================================================
// SINAL DE ACESSO NEGADO
// ============================================================

void signalDenied()
{
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);

    tone(BUZZER, 500, 500);

    delay(700);

    digitalWrite(LED_RED, LOW);
}


// ============================================================
// SINAL DE ERRO DE COMUNICAÇÃO
// ============================================================

void signalError()
{
    digitalWrite(LED_GREEN, LOW);

    for (int i = 0; i < 2; i++)
    {
        digitalWrite(LED_RED, HIGH);
        tone(BUZZER, 350, 150);
        delay(200);

        digitalWrite(LED_RED, LOW);
        delay(150);
    }
}


// ============================================================
// LER UID DO CARTÃO
// ============================================================

String readUID()
{
    String uid = "";

    for (byte i = 0; i < rfid.uid.size; i++)
    {
        if (rfid.uid.uidByte[i] < 0x10)
        {
            uid += "0";
        }

        uid += String(
            rfid.uid.uidByte[i],
            HEX
        );
    }

    uid.toUpperCase();

    return uid;
}


// ============================================================
// LIGAR AO WI-FI
// ============================================================

bool connectWiFi()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        return true;
    }

    Serial.println();
    Serial.println("A ligar ao Wi-Fi...");

    WiFi.mode(WIFI_STA);
    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD
    );

    unsigned long start = millis();

    while (
        WiFi.status() != WL_CONNECTED &&
        millis() - start < WIFI_TIMEOUT
    )
    {
        delay(500);
        Serial.print(".");
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.println("Wi-Fi ligado.");
        Serial.print("IP do ESP32: ");
        Serial.println(WiFi.localIP());

        return true;
    }

    Serial.println("Falha ao ligar ao Wi-Fi.");

    return false;
}


// ============================================================
// ENVIAR LEITURA PARA O SMARTEDU
// ============================================================

void sendScan(const String& uid)
{
    if (!connectWiFi())
    {
        Serial.println(
            "Não foi possível comunicar com o SmartEdu."
        );

        signalError();

        return;
    }

    HTTPClient http;

    Serial.println();
    Serial.println("A contactar o SmartEdu...");

    http.begin(SERVER_URL);

    http.addHeader(
        "Content-Type",
        "application/json"
    );

    http.addHeader(
        "X-Device-Token",
        DEVICE_TOKEN
    );

    String body =
        "{"
        "\"uid\":\"" + uid + "\","
        "\"direction\":\"entry\","
        "\"device_code\":\"" +
        String(DEVICE_CODE) +
        "\""
        "}";

    Serial.println("JSON enviado:");
    Serial.println(body);

    int httpCode = http.POST(body);

    Serial.print("HTTP Status: ");
    Serial.println(httpCode);

    String response = http.getString();

    Serial.println("Resposta do servidor:");
    Serial.println(response);

    if (httpCode >= 200 && httpCode < 300)
    {
        Serial.println(
            "ACESSO AUTORIZADO"
        );

        signalGranted();
    }
    else if (httpCode == 401)
    {
        Serial.println(
            "DISPOSITIVO NÃO AUTORIZADO"
        );

        signalDenied();
    }
    else if (httpCode == 403)
    {
        Serial.println(
            "ACESSO NEGADO"
        );

        signalDenied();
    }
    else if (httpCode >= 400)
    {
        Serial.println(
            "ERRO NA API SMARTEDU"
        );

        signalError();
    }
    else
    {
        Serial.println(
            "Falha de comunicação."
        );

        signalError();
    }

    http.end();
}


// ============================================================
// CONFIGURAÇÃO INICIAL
// ============================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println(
        "================================"
    );
    Serial.println(
        "       SMARTEDU RFID"
    );
    Serial.println(
        "       ESP32 + RC522"
    );
    Serial.println(
        "================================"
    );

    // LEDs
    pinMode(
        LED_GREEN,
        OUTPUT
    );

    pinMode(
        LED_RED,
        OUTPUT
    );

    pinMode(
        BUZZER,
        OUTPUT
    );

    digitalWrite(
        LED_GREEN,
        LOW
    );

    digitalWrite(
        LED_RED,
        LOW
    );

    // SPI
    SPI.begin();

    // RC522
    rfid.PCD_Init();

    delay(100);

    Serial.println(
        "RC522 inicializado."
    );

    // Wi-Fi
    connectWiFi();

    Serial.println();
    Serial.println(
        "Leitor RFID pronto."
    );

    Serial.println(
        "Aproxime um cartão..."
    );
}


// ============================================================
// LOOP PRINCIPAL
// ============================================================

void loop()
{
    // Verifica Wi-Fi periodicamente
    if (WiFi.status() != WL_CONNECTED)
    {
        connectWiFi();
    }

    // Não existe cartão novo
    if (!rfid.PICC_IsNewCardPresent())
    {
        delay(50);
        return;
    }

    // Não conseguiu ler o cartão
    if (!rfid.PICC_ReadCardSerial())
    {
        delay(50);
        return;
    }

    String uid = readUID();

    // Evita enviar o mesmo cartão várias vezes
    // em sequência.
    unsigned long now = millis();

    if (
        uid == lastUID &&
        now - lastScanTime < CARD_COOLDOWN
    )
    {
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();

        delay(50);

        return;
    }

    lastUID = uid;
    lastScanTime = now;

    Serial.println();
    Serial.println(
        "--------------------------------"
    );

    Serial.print(
        "RFID detectado: "
    );

    Serial.println(uid);

    Serial.print(
        "Dispositivo: "
    );

    Serial.println(DEVICE_CODE);

    sendScan(uid);

    Serial.println(
        "--------------------------------"
    );

    // Finalizar comunicação com o cartão
    rfid.PICC_HaltA();

    rfid.PCD_StopCrypto1();

    delay(100);
}