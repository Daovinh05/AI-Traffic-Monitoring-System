/*
 * ESP32 MQTT Alert - AI Traffic Monitoring System
 * ================================================
 * Nhận cảnh báo vi phạm tài xế từ hệ thống AI qua MQTT
 * và kích hoạt buzzer/LED cảnh báo.
 * 
 * Phần cứng cần thiết:
 *   - ESP32 DevKit
 *   - Buzzer (GPIO 25)
 *   - LED Đỏ (GPIO 26) + điện trở 220Ω
 *   - LED Vàng (GPIO 27) + điện trở 220Ω
 * 
 * Thư viện cần cài (Arduino IDE → Library Manager):
 *   - PubSubClient by Nick O'Leary
 *   - ArduinoJson by Benoit Blanchon
 */


 
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ========================================
// CẤU HÌNH WiFi - THAY ĐỔI THEO MẠNG CỦA BẠN
// ========================================
const char* WIFI_SSID = "Long 2.4G 3";
const char* WIFI_PASSWORD = "123456789";

// ========================================
// CẤU HÌNH MQTT - PHẢI KHỚP VỚI FILE .env
// ========================================
const char* MQTT_SERVER = "192.168.0.103";  // IP máy tính chạy Mosquitto
const int   MQTT_PORT = 1883;
const char* MQTT_TOPIC = "traffic/alert";
const char* MQTT_STATUS_TOPIC = "traffic/esp32/status";
const char* MQTT_CLIENT_ID = "esp32_alert_device";

// ========================================
// CẤU HÌNH GPIO - CHÂN KẾT NỐI PHẦN CỨNG
// ========================================
#define RELAY_PIN     18
#define BUZZER_PIN    19

// ========================================
// CẤU HÌNH THỜI GIAN
// ========================================
#define ALERT_DURATION_MS     5000   // Tự tắt cảnh báo sau 5 giây
#define BUZZER_ON_MS          200    // Buzzer bật (cho chế độ ngắt quãng)
#define BUZZER_OFF_MS         300    // Buzzer tắt (cho chế độ ngắt quãng)
#define WIFI_RETRY_DELAY_MS   5000   // Thời gian chờ kết nối lại WiFi
#define STATUS_INTERVAL_MS    30000  // Gửi trạng thái mỗi 30 giây

// ========================================
// BIẾN TOÀN CỤC
// ========================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Trạng thái cảnh báo hiện tại
bool alertActive = false;
String currentAlertType = "";
String currentAlertLevel = "";
unsigned long alertStartTime = 0;
unsigned long lastBuzzerToggle = 0;
bool buzzerState = false;
unsigned long lastStatusSend = 0;

// ========================================
// KẾT NỐI WiFi
// ========================================
void setupWiFi() {
  Serial.println();
  Serial.print("[WiFi] Đang kết nối đến: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("[WiFi] ✅ Đã kết nối!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("[WiFi] ❌ Kết nối thất bại! Đang thử lại...");
  }
}

// ========================================
// XỬ LÝ MESSAGE MQTT NHẬN ĐƯỢC
// ========================================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // In tin nhắn thô để debug
  Serial.print("[MQTT] Nhận tin nhắn mới trên topic: ");
  Serial.println(topic);
  Serial.print("[MQTT] Nội dung thô: ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  // Parse JSON message
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    Serial.print("[MQTT] ❌ Lỗi parse JSON: ");
    Serial.println(error.c_str());
    return;
  }

  // Đọc dữ liệu từ JSON
  const char* type = doc["type"];       // "eye", "phone", "yawn", ...
  const char* message = doc["message"]; // Nội dung cảnh báo
  const char* level = doc["level"];     // "critical" hoặc "warning"
  const char* timestamp = doc["timestamp"];

  Serial.println("========================================");
  Serial.println("[MQTT] 📩 NHẬN CẢNH BÁO MỚI!");
  Serial.print("  Loại: ");      Serial.println(type);
  Serial.print("  Nội dung: ");  Serial.println(message);
  Serial.print("  Mức độ: ");    Serial.println(level);
  Serial.print("  Thời gian: "); Serial.println(timestamp);
  Serial.println("========================================");

  // Kích hoạt cảnh báo
  currentAlertType = String(type);
  currentAlertLevel = String(level);
  alertActive = true;
  alertStartTime = millis();
  lastBuzzerToggle = millis();
  buzzerState = true;

  // Bật Relay và Buzzer ngay lập tức
  if (currentAlertLevel == "critical") {
    // Critical: Relay đóng (đèn sáng) + Buzzer liên tục
    digitalWrite(RELAY_PIN, LOW);   // LOW = đóng tiếp điểm relay
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    // Warning: Chỉ bật Buzzer ngắt quãng (không bật đèn)
    digitalWrite(RELAY_PIN, HIGH);  // Relay tắt
    digitalWrite(BUZZER_PIN, HIGH);
  }
}

// ========================================
// KẾT NỐI MQTT BROKER
// ========================================
void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Đang kết nối đến Broker...");

    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println(" ✅ Thành công!");

      // Subscribe topic nhận cảnh báo
      mqttClient.subscribe(MQTT_TOPIC, 1);  // QoS 1
      Serial.print("[MQTT] 📡 Đã subscribe topic: ");
      Serial.println(MQTT_TOPIC);

      // Gửi trạng thái online
      StaticJsonDocument<128> statusDoc;
      statusDoc["device"] = "esp32";
      statusDoc["status"] = "online";
      statusDoc["ip"] = WiFi.localIP().toString();
      
      char statusBuffer[128];
      serializeJson(statusDoc, statusBuffer);
      mqttClient.publish(MQTT_STATUS_TOPIC, statusBuffer, true);

    } else {
      Serial.print(" ❌ Thất bại, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" → Thử lại sau 5 giây...");
      delay(5000);
    }
  }
}

// ========================================
// XỬ LÝ CẢNH BÁO TRONG LOOP
// ========================================
void processAlert() {
  if (!alertActive) return;

  unsigned long elapsed = millis() - alertStartTime;

  // Tự động tắt cảnh báo sau ALERT_DURATION_MS
  if (elapsed >= ALERT_DURATION_MS) {
    stopAlert();
    return;
  }

  // Xử lý buzzer ngắt quãng cho mức warning
  if (currentAlertLevel == "warning") {
    unsigned long buzzerElapsed = millis() - lastBuzzerToggle;

    if (buzzerState && buzzerElapsed >= BUZZER_ON_MS) {
      // Tắt buzzer
      digitalWrite(BUZZER_PIN, LOW);
      buzzerState = false;
      lastBuzzerToggle = millis();
    } else if (!buzzerState && buzzerElapsed >= BUZZER_OFF_MS) {
      // Bật buzzer
      digitalWrite(BUZZER_PIN, HIGH);
      buzzerState = true;
      lastBuzzerToggle = millis();
    }
  }
  // Mức critical: buzzer đã bật liên tục ở callback, không cần xử lý thêm
}

// ========================================
// TẮT CẢNH BÁO
// ========================================
void stopAlert() {
  alertActive = false;
  currentAlertType = "";
  currentAlertLevel = "";
  digitalWrite(RELAY_PIN, HIGH);  // Tắt relay (ngắt đèn)
  digitalWrite(BUZZER_PIN, LOW);  // Tắt còi
  Serial.println("[Alert] 🔕 Cảnh báo đã tắt.");
}

// ========================================
// GỬI TRẠNG THÁI ĐỊNH KỲ
// ========================================
void sendStatus() {
  if (millis() - lastStatusSend < STATUS_INTERVAL_MS) return;
  lastStatusSend = millis();

  StaticJsonDocument<128> doc;
  doc["device"] = "esp32";
  doc["status"] = "online";
  doc["uptime"] = millis() / 1000;
  doc["wifi_rssi"] = WiFi.RSSI();

  char buffer[128];
  serializeJson(doc, buffer);
  mqttClient.publish(MQTT_STATUS_TOPIC, buffer);
}

// ========================================
// SETUP
// ========================================
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("========================================");
  Serial.println("  ESP32 MQTT Alert - Traffic Monitor");
  Serial.println("========================================");

  // Cấu hình GPIO
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Trạng thái ban đầu - TẮt hết
  digitalWrite(RELAY_PIN, HIGH);  // HIGH = Relay ngắt (tắt đèn)
  digitalWrite(BUZZER_PIN, LOW);

  // Test phần cứng khi khởi động
  Serial.println("[Setup] Test phần cứng...");
  
  // Test Relay (bật đèn 200ms)
  digitalWrite(RELAY_PIN, LOW);   // Đóng relay
  delay(200);
  digitalWrite(RELAY_PIN, HIGH);  // Ngắt relay
  
  // Test Còi (kêu 100ms)
  digitalWrite(BUZZER_PIN, HIGH);
  delay(100);
  digitalWrite(BUZZER_PIN, LOW);
  
  Serial.println("[Setup] Phan cung OK!");

  // Kết nối WiFi
  setupWiFi();

  // Cấu hình MQTT
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setBufferSize(512);

  // Kết nối MQTT
  connectMQTT();
}

// ========================================
// MAIN LOOP
// ========================================
void loop() {
  // Đảm bảo WiFi luôn kết nối
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] ⚠️ Mất kết nối WiFi! Đang kết nối lại...");
    setupWiFi();
  }

  // Đảm bảo MQTT luôn kết nối
  if (!mqttClient.connected()) {
    connectMQTT();
  }

  // Xử lý MQTT messages
  mqttClient.loop();

  // Xử lý cảnh báo đang active
  processAlert();

  // Gửi trạng thái định kỳ
  sendStatus();

  delay(10);  // Tránh CPU chạy 100%
}
