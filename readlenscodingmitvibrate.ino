#include "esp_camera.h"
#include "img_converters.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "Audio.h"
#include <WebServer.h>

// --- Wi-Fi & Backend Settings ---
const char* ssid = "Apple";
const char* password = "haekal06";
const char* serverUrl = "http://172.20.10.9:5000/process_image"; 

// --- The Verified, Conflict-Free Pin Assignments ---
const int CAPTURE_BUTTON = 1;   
const int BATTERY_PIN    = 2;   
const int MODE_SWITCH    = 14;  
const int VIB_MOTOR      = 21;  

const int I2S_LRC        = 39;  // DAC Word Select 
const int I2S_DOUT       = 41;  // DAC Data In
const int I2S_BCLK       = 42;  // DAC Bit Clock 

// --- Core Objects ---
Audio audio;
WebServer server(80);

void handleRoot() {
  server.send(200, "text/plain", "SUCCESS");
}

// --- Standard ESP32-S3-CAM Pin Configuration ---
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     15
#define SIOD_GPIO_NUM     4   
#define SIOC_GPIO_NUM     5   
#define Y2_GPIO_NUM       11
#define Y3_GPIO_NUM       9
#define Y4_GPIO_NUM       8
#define Y5_GPIO_NUM       10
#define Y6_GPIO_NUM       12
#define Y7_GPIO_NUM       18
#define Y8_GPIO_NUM       17
#define Y9_GPIO_NUM       16
#define VREF_GPIO_NUM     6
#define HREF_GPIO_NUM     7
#define PCLK_GPIO_NUM     13

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Initialize Input/Output Pins
  pinMode(CAPTURE_BUTTON, INPUT_PULLUP);
  pinMode(MODE_SWITCH, INPUT_PULLUP);
  pinMode(VIB_MOTOR, OUTPUT);
  digitalWrite(VIB_MOTOR, LOW);

  // --- Wi-Fi Connection Setup ---
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected successfully!");
  Serial.print("ESP32-S3 IP Address: ");
  Serial.println(WiFi.localIP());

  // --- Web Server Setup ---
  server.on("/", handleRoot);
  server.begin();
  Serial.println("Web server started.");

  // --- I2S Audio Amplifier Setup ---
  audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  audio.setVolume(85); // Set clear volume level (0 to 100)

  // --- Camera Module Configuration ---
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VREF_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  
  // Use 20MHz standard clock frequency for OV2640/OV5640 to prevent frame timeout
  config.xclk_freq_hz = 20000000; 
  // BYPASS HARDWARE ENCODER: Stream raw uncompressed pixels to ESP32
  config.pixel_format = PIXFORMAT_RGB565;
  
  // Allocate Frame Buffer
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_LATEST; // Always keep only the most recent frame
  
  if (psramFound()) {
    Serial.println("✅ PSRAM found! Allocating buffer to PSRAM.");
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.fb_count = 2; // OV5640 often prefers 2 buffers in PSRAM
  } else {
    Serial.println("❌ WARNING: PSRAM NOT FOUND! Falling back to DRAM.");
    Serial.println("❌ OV5640 requires PSRAM for stable JPEG capture!");
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.fb_count = 1;
  }

  // Camera Init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera initialization failed with error 0x%x\n", err);
    return;
  }
  
  // OV5640 CRITICAL FIX: The OV5640's internal PLLs and JPEG encoder take time to stabilize.
  // If we don't wait, the very first real frame request will crash its internal state machine.
  delay(1000); 

  sensor_t * s = esp_camera_sensor_get();
  // Ensure the sensor is explicitly told to use VGA
  s->set_framesize(s, FRAMESIZE_VGA);

  // Warm-up the camera by grabbing and discarding the first few frames
  // The OV5640 usually outputs 1-2 corrupt frames on boot
  for (int i = 0; i < 2; i++) {
    camera_fb_t* dummy_fb = esp_camera_fb_get();
    if (dummy_fb) {
        esp_camera_fb_return(dummy_fb);
    }
    delay(50);
  }
  
  Serial.println("Camera successfully configured and initialized!");
}

void loop() {
  // Handle incoming web server client requests (ping from Flask app)
  server.handleClient();

  // Check the trigger button
  if (digitalRead(CAPTURE_BUTTON) == LOW) {
    // Short debounce
    delay(50);
    if (digitalRead(CAPTURE_BUTTON) == LOW) {
      Serial.println("📸 Capture button triggered!");

      // Capture frame buffer from camera FIRST (before any motors turn on!)
      // This prevents the Vibration Motor from causing a voltage drop/brownout that crashes the camera.
      camera_fb_t* fb = esp_camera_fb_get();
      if (!fb) {
        Serial.println("Camera capture failed! Buffer returned NULL.");
        return;
      }
      
      Serial.println("Software compressing RGB565 to JPEG...");
      uint8_t * out_jpg = NULL;
      size_t out_jpg_len = 0;
      bool jpeg_converted = frame2jpg(fb, 80, &out_jpg, &out_jpg_len);
      
      // Return uncompressed buffer memory immediately back to camera pool
      esp_camera_fb_return(fb);

      if (!jpeg_converted) {
        Serial.println("Software JPEG compression failed!");
        return;
      }

      // Provide a short haptic pulse to confirm the photo was taken.
      // We don't leave it ON continuously to prevent drawing too much current 
      // while the ESP32 is uploading via Wi-Fi (which causes power brownouts).
      digitalWrite(VIB_MOTOR, HIGH);
      delay(150);
      digitalWrite(VIB_MOTOR, LOW);

      // Read state parameters
      String mode = (digitalRead(MODE_SWITCH) == HIGH) ? "DESCRIBE" : "TEXT";
      float batteryPct = getBatteryPercentage();

      // Stream the image data package up to Flask (this will block until the AI finishes)
      sendImageToServer(out_jpg, out_jpg_len, mode, batteryPct);

      // The AI has finished and the server responded. 
      // Provide another short haptic pulse to confirm the answer is ready.
      digitalWrite(VIB_MOTOR, HIGH);
      delay(150);
      digitalWrite(VIB_MOTOR, LOW);

      // Free the software allocated JPEG buffer
      free(out_jpg);

      // Prevent button echo re-triggers
      while(digitalRead(CAPTURE_BUTTON) == LOW) {
        audio.loop(); // Keep audio engine processing active even if button held down
      }
    }
  } else {
    // CRITICAL: This audio engine must background-run constantly so streaming MP3 audio doesn't stutter!
    // We only run it when the button is NOT pressed to prevent DMA starvation during camera capture.
    audio.loop(); 
  }
}

// --- Read Hardware Battery Voltage Level ---
float getBatteryPercentage() {
  int raw = analogRead(BATTERY_PIN);
  float voltage = (raw / 4095.0) * 2.0 * 3.3 * 1.1; 

  float percentage = ((voltage - 3.4) / (4.2 - 3.4)) * 100.0;
  if (percentage > 100.0) percentage = 100.0;
  if (percentage < 0.0) percentage = 0.0;

  return percentage;
}

// --- Send Image & Run Streamed Speech ---
void sendImageToServer(uint8_t* imageBytes, size_t imageLength, String mode, float battery) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    
    // Upload raw binary data payload to protect performance overhead
    http.addHeader("Content-Type", "image/jpeg");
    http.addHeader("X-Glasses-Mode", mode);
    http.addHeader("X-Battery-Level", String(battery, 1));

    Serial.println("Uploading frame to server...");
    int httpResponseCode = http.POST(imageBytes, imageLength);

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println("Flask Server Response: " + payload);

      // Hardware execution handoff: Let laptop host the audio stream entirely
      // The background engine fetches the server's compiled static voice artifact
      Serial.println("🔊 Fetching text-to-speech audio path from Flask host...");
      audio.connecttohost("http://172.20.10.9:5000/static/voice.mp3");
    } else {
      Serial.printf("Error code on image dispatch connection: %d\n", httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("Wi-Fi dropped out, cannot compile post request.");
  }
}