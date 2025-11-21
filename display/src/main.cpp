// SPDX-FileCopyrightText: 2023 Limor Fried for Adafruit Industries
//
// SPDX-License-Identifier: MIT

#include <Arduino_GFX_Library.h>
#include <Adafruit_FT6206.h>
#include <Adafruit_CST8XX.h>
#include <WiFi.h>
#include <Fonts/FreeMono9pt7b.h>
#include <Fonts/FreeSansBoldOblique24pt7b.h>
#include <WiFiClient.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <base64.hpp>
#include <StreamUtils.h>

#include "cJSON.h"
#include "config.h"
#include "display.h"

cJSON_Hooks hooks = {
  .malloc_fn = ps_malloc,
  .free_fn = free
};

void printMem() {
  Serial.printf("Total heap: %d\n", ESP.getHeapSize());
  Serial.printf("Free heap: %d\n", ESP.getFreeHeap());
  Serial.printf("Total PSRAM: %d\n", ESP.getPsramSize());
  Serial.printf("Free PSRAM: %d\n", ESP.getFreePsram());
}

WiFiClient client;
HttpClient http(client, BACKEND_HOST, BACKEND_PORT);

Arduino_XCA9554SWSPI *expander = new Arduino_XCA9554SWSPI(
    PCA_TFT_RESET, PCA_TFT_CS, PCA_TFT_SCK, PCA_TFT_MOSI,
    &Wire, 0x3F);

Arduino_ESP32RGBPanel *rgbpanel = new Arduino_ESP32RGBPanel(
    TFT_DE, TFT_VSYNC, TFT_HSYNC, TFT_PCLK,
    TFT_R1, TFT_R2, TFT_R3, TFT_R4, TFT_R5,
    TFT_G0, TFT_G1, TFT_G2, TFT_G3, TFT_G4, TFT_G5,
    TFT_B1, TFT_B2, TFT_B3, TFT_B4, TFT_B5,
    1 /* hsync_polarity */, 50 /* hsync_front_porch */, 2 /* hsync_pulse_width */, 44 /* hsync_back_porch */,
    1 /* vsync_polarity */, 16 /* vsync_front_porch */, 2 /* vsync_pulse_width */, 18 /* vsync_back_porch */
//    ,1, 30000000
    );

GFXcanvas16 canvas(480, 480);
Arduino_RGB_Display *gfx = new Arduino_RGB_Display(
// 2.1" 480x480 round display
//    480 /* width */, 480 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
//    expander, GFX_NOT_DEFINED /* RST */, TL021WVC02_init_operations, sizeof(TL021WVC02_init_operations));

// 2.8" 480x480 round display
//    480 /* width */, 480 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
//    expander, GFX_NOT_DEFINED /* RST */, TL028WVC01_init_operations, sizeof(TL028WVC01_init_operations));

// 3.4" 480x480 square display
//    480 /* width */, 480 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
//    expander, GFX_NOT_DEFINED /* RST */, tl034wvs05_b1477a_init_operations, sizeof(tl034wvs05_b1477a_init_operations));

/* 4.0" 480x480 square */
   480 /* width */, 480 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
   expander, GFX_NOT_DEFINED /* RST */, tl040wvs03_init_operations, sizeof(tl040wvs03_init_operations));

// 3.2" 320x820 rectangle bar display
//    320 /* width */, 820 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
//    expander, GFX_NOT_DEFINED /* RST */, tl032fwv01_init_operations, sizeof(tl032fwv01_init_operations));

// 3.7" 240x960 rectangle bar display
//    240 /* width */, 960 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
//    expander, GFX_NOT_DEFINED /* RST */, HD371001C40_init_operations, sizeof(HD371001C40_init_operations), 120 /* col_offset1 */);

// 4.0" 720x720 square display
//    720 /* width */, 720 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
//    expander, GFX_NOT_DEFINED /* RST */, NULL, 0);

// 4.0" 720x720 round display
//    720 /* width */, 720 /* height */, rgbpanel, 0 /* rotation */, true /* auto_flush */,
//    expander, GFX_NOT_DEFINED /* RST */, hd40015c40_init_operations, sizeof(hd40015c40_init_operations));
// needs also the rgbpanel to have these pulse/sync values:
//    1 /* hync_polarity */, 46 /* hsync_front_porch */, 2 /* hsync_pulse_width */, 44 /* hsync_back_porch */,
//    1 /* vsync_polarity */, 50 /* vsync_front_porch */, 16 /* vsync_pulse_width */, 16 /* vsync_back_porch */

void setDefaultFont() {
  gfx->setFont(&FreeMono9pt7b);
}

uint16_t *colorWheel;

// The Capacitive touchscreen overlays uses hardware I2C (SCL/SDA)

// Most touchscreens use FocalTouch with I2C Address often but not always 0x48!
#define I2C_TOUCH_ADDR 0x48

// 2.1" 480x480 round display use CST826 touchscreen with I2C Address at 0x15
//#define I2C_TOUCH_ADDR 0x15  // often but not always 0x48!

Adafruit_FT6206 focal_ctp = Adafruit_FT6206();  // this library also supports FT5336U!
Adafruit_CST8XX cst_ctp = Adafruit_CST8XX();
bool touchOK = false;        // we will check if the touchscreen exists
bool isFocalTouch = false;

// https://chat.openai.com/share/8edee522-7875-444f-9fea-ae93a8dfa4ec
void generateColorWheel(uint16_t *colorWheel) {
  int width = gfx->width();
  int height = gfx->height();
  int half_width = width / 2;
  int half_height = height / 2;
  float angle;
  uint8_t r, g, b;
  int index, scaled_index;

  for(int y = 0; y < half_height; y++) {
    for(int x = 0; x < half_width; x++) {
      index = y * half_width + x;
      angle = atan2(y - half_height / 2, x - half_width / 2);
      r = uint8_t(127.5 * (cos(angle) + 1));
      g = uint8_t(127.5 * (sin(angle) + 1));
      b = uint8_t(255 - (r + g) / 2);
      uint16_t color = RGB565(r, g, b);

      // Scale this pixel into 4 pixels in the full buffer
      for(int dy = 0; dy < 2; dy++) {
        for(int dx = 0; dx < 2; dx++) {
          scaled_index = (y * 2 + dy) * width + (x * 2 + dx);
          colorWheel[scaled_index] = color;
        }
      }
    }
  }
}

char buf[100];

void setup(void)
{
  Serial.begin(115200);
  //while (!Serial) delay(100);

#ifdef GFX_EXTRA_PRE_INIT
  GFX_EXTRA_PRE_INIT();
#endif

  Serial.println("Beginning");
  // Init Display

  Wire.setClock(1000000); // speed up I2C
  if (!gfx->begin()) {
    Serial.println("gfx->begin() failed!");
  }

  Serial.println("Initialized!");

  gfx->fillScreen(BLACK);
  setDefaultFont();
  gfx->setTextColor(WHITE);
  gfx->setCursor(0, 20);
  colorWheel = (uint16_t *) ps_malloc(gfx->width() * gfx->height() * sizeof(uint16_t));
  if (colorWheel) {
    generateColorWheel(colorWheel);
    gfx->draw16bitRGBBitmap(0, 0, colorWheel, gfx->width(), gfx->height());
  }
  free(colorWheel);
  DISPLAY_PRINTF("Initializing Goober System...\n");

  expander->pinMode(PCA_TFT_BACKLIGHT, OUTPUT);
  expander->digitalWrite(PCA_TFT_BACKLIGHT, HIGH);

  // Set WiFi to station mode and disconnect from an AP if it was previously connected
  delay(15000);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  printMem();

  int status = WL_IDLE_STATUS;

  // attempt to connect to Wifi network:

  while ( status != WL_CONNECTED) {
    DISPLAY_PRINTF("Connecting to WiFi network '%s'", WIFI_SSID);

    status = WiFi.begin(WIFI_SSID, WIFI_PASS);

    for (int i = 0; i < 10; i++) {
      delay(1000);
      DISPLAY_PRINTF(".");
      status = WiFi.status();
      Serial.println(status);
      if (status == WL_CONNECTED) {
        DISPLAY_PRINTF("\n");
        break;
      }
    }


  }
  IPAddress ip = WiFi.localIP();
  DISPLAY_PRINTF("Connected! IP: %u.%u.%u.%u\n", ip[0], ip[1], ip[2], ip[3]);

  if (!focal_ctp.begin(0, &Wire, I2C_TOUCH_ADDR)) {
    // Try the CST826 Touch Screen
    if (!cst_ctp.begin(&Wire, I2C_TOUCH_ADDR)) {
      Serial.print("No Touchscreen found at address 0x");
      Serial.println(I2C_TOUCH_ADDR, HEX);
      touchOK = false;
    } else {
      Serial.println("CST826 Touchscreen found");
      touchOK = true;
      isFocalTouch = false;
    }
  } else {
    Serial.println("Focal Touchscreen found");
    touchOK = true;
    isFocalTouch = true;
  }
}

int lastStatusCode = -1;
char lastGooberName[50] = "";
void loop()
{
  DISPLAY_DBGF("HTTP Sent... ");
  http.get("/v1/sessions");
  int statusCode = http.responseStatusCode();
  long contentLength = http.contentLength();
  DISPLAY_DBGF("Response Received: %d, length %d\n", statusCode, contentLength);

  Serial.println("malloc response");
  char *response = (char *) ps_malloc(sizeof(char) * contentLength);
  printMem();

  if (statusCode == 200 || statusCode == 201) {
    if (lastStatusCode != statusCode) {
      gfx->fillScreen(WHITE);
      gfx->setTextColor(BLACK);
      gfx->setTextSize(2);
      gfx->setCursor(75, 240);
      if (statusCode == 200) {
        DISPLAY_PRINTF("Loading Goober");
      } else if (statusCode == 201) {
        DISPLAY_PRINTF("Loading QR Code");
      }
      gfx->setTextSize(1);
    }

    // Get the raw and the decoded stream
    DISPLAY_DBGF("Skipping Headers: %d\n", http.skipResponseHeaders());
    int remainingLength = contentLength;
    int i = 0;
    while(!http.endOfBodyReached()) {
      if (http.available()) {
        response[i] = http.read();
        i++;
        remainingLength--;
      }
    }
    DISPLAY_DBGF("Response Gathered!\n");

    // Parse response
    Serial.println("cJSON Parse");
    cJSON *json = cJSON_Parse(response);
    printMem();
    if(json == NULL) {
      DISPLAY_DBGF("JSON Decode Failed\n");
      return;
    }
    cJSON *key = json->child;
    while (key) {
      DISPLAY_DBGF("%s ", key->string);
      key = key->next;
    }
    DISPLAY_DBGF("\n");


    DISPLAY_DBGF("JSON Deserialized, %d\n", http.endOfBodyReached());
    Serial.println("JSON Parsing");
    uint32_t width = cJSON_GetObjectItem(json, "width")->valueint;
    uint32_t height = cJSON_GetObjectItem(json, "height")->valueint;
    char *bitmapB64Str = cJSON_GetObjectItem(json, "bitmap")->valuestring;
    Serial.println("malloc bitmap");
    uint16_t *bitmap = (uint16_t *) ps_malloc(sizeof(uint16_t) * width * height);
    printMem();
    DISPLAY_DBGF("Malloc'd... ");
    unsigned int nBytes = decode_base64((const unsigned char *)bitmapB64Str, (unsigned char *)bitmap);
    DISPLAY_DBGF("Bitmap Parsed, %d bytes\n", nBytes);
    char *maskB64Str = cJSON_GetObjectItem(json, "mask")->valuestring;
    int maskLength = strlen(maskB64Str);
    Serial.println("malloc mask");
    uint8_t *mask = (uint8_t *) ps_malloc(maskLength);
    printMem();
    DISPLAY_DBGF("Malloc'd... ");
    nBytes = decode_base64((const unsigned char *)maskB64Str, (unsigned char *)mask);
    DISPLAY_DBGF("Mask Parsed, %d bytes\n", nBytes);
    if (lastStatusCode != statusCode) {
      gfx->fillScreen(WHITE);
    }
    gfx->setCursor(0, 20);
    gfx->setTextSize(2);
    if (statusCode == 200) {
      cJSON *goober = cJSON_GetObjectItem(json, "goober");
      char *gooberName = cJSON_GetObjectItem(goober, "name")->valuestring;
      if(strcmp(gooberName, lastGooberName) != 0) {
        gfx->fillScreen(WHITE);
      }
      DISPLAY_PRINTF("Name: %s\n", gooberName);
      cJSON *stat = NULL;
      cJSON_ArrayForEach(stat, cJSON_GetObjectItem(goober, "stats")) {
        if (strcmp(cJSON_GetObjectItem(stat, "type")->valuestring, "float") == 0) {
          DISPLAY_PRINTF("%s: %.2f\n", cJSON_GetObjectItem(stat, "stat_name")->valuestring, cJSON_GetObjectItem(stat, "stat_value")->valuedouble);
        } else {
          DISPLAY_PRINTF("%s: %.2f\n", cJSON_GetObjectItem(stat, "stat_name")->valuestring, cJSON_GetObjectItem(stat, "stat_value")->valuestring);
        }
      }
      drawRGBBitmap(gfx, 140, 140, bitmap, mask, width, height);
      strcpy(lastGooberName, gooberName);
    } else {
      drawRGBBitmap(gfx, 0, 0, bitmap, mask, width, height);
    }

    Serial.println("free bitmap");
    free(bitmap);
    Serial.println("free mask");
    free(mask);
    Serial.println("cJSON Delete");
    cJSON_Delete(json);
  } else {
    // Get the raw and the decoded stream
    DISPLAY_DBGF("Skipping Headers: %d\n", http.skipResponseHeaders());
    int remainingLength = contentLength;
    int i = 0;
    while(!http.endOfBodyReached()) {
      if (http.available()) {
        response[i] = http.read();
        i++;
        remainingLength--;
      }
    }
    DISPLAY_DBGF("Response Gathered!\n");
    DISPLAY_DBGF("%s\n", response);
    canvas.setFont(&FreeSansBoldOblique24pt7b);
    canvas.setTextColor(BLACK);
    canvas.setTextSize(2);
    canvas.startWrite();
    for (int y = 0; y < 480; y+=4) {
      for (int x = 0; x < 480; x+=4) {
        canvas.writeFillRect(x, y, 4, 4, random(0xFFFF));
      }
    }
    canvas.endWrite();
    canvas.setCursor(15, 85);
    canvas.print("G");
    canvas.setCursor(90, 160);
    canvas.print("O");
    canvas.setCursor(165, 235);
    canvas.print("O");
    canvas.setCursor(240, 310);
    canvas.print("B");
    canvas.setCursor(315, 385);
    canvas.print("E");
    canvas.setCursor(390, 460);
    canvas.print("R");
    drawRGBBitmap(gfx, 0, 0, (uint16_t *) canvas.getBuffer(), NULL, canvas.width(), canvas.height());
  }

  Serial.println("free response");
  free(response);
  printMem();

  if (touchOK) {
    if (isFocalTouch && focal_ctp.touched()) {
      TS_Point p = focal_ctp.getPoint(0);
      Serial.printf("(%d, %d)\n", p.x, p.y);
      gfx->fillRect(p.x, p.y, 5, 5, WHITE);
    } else if (!isFocalTouch && cst_ctp.touched()) {
      CST_TS_Point p = cst_ctp.getPoint(0);
      Serial.printf("(%d, %d)\n", p.x, p.y);
      gfx->fillRect(p.x, p.y, 5, 5, WHITE);
    }
  }

  // use the buttons to turn off
  if (! expander->digitalRead(PCA_BUTTON_DOWN)) {
    expander->digitalWrite(PCA_TFT_BACKLIGHT, LOW);
  }
  // and on the backlight
  if (! expander->digitalRead(PCA_BUTTON_UP)) {
    expander->digitalWrite(PCA_TFT_BACKLIGHT, HIGH);
  }

  lastStatusCode = statusCode;
}