#include <Arduino.h>
#include "M5StickCPlus2.h"
#include "drawing_engine.h"
#include "serial_handler.h"
#include "command_parser.h"

// グローバルインスタンス
DrawingEngine drawingEngine;
SerialHandler serialHandler;
CommandParser commandParser;

// ログ用マクロ
#define LOG_INFO(fmt, ...)
#define LOG_WARN(fmt, ...)
#define LOG_ERROR(fmt, ...)

void setup() {
    // M5StickC Plus2 初期化
    auto cfg = M5.config();
    M5.begin(cfg);
    
    // 通信シリアル（USB）
    Serial.begin(115200);
    delay(100);
    
    LOG_INFO("M5StickC Plus2 Boot");
    LOG_INFO("Drawing Engine initialized");
    
    // 画面表示：起動完了
    M5.Display.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Display.setFont(&fonts::DejaVu12);
    M5.Display.drawString("Ready", 10, 10);
    
    serialHandler.init();
    LOG_INFO("Serial Handler initialized");
}

void loop() {
    M5.update();
    
    // シリアルデータ受信確認
    if (Serial.available()) {
        uint8_t data = Serial.read();
        serialHandler.addRxByte(data);
    }
    
    // コマンド処理
    Command cmd;
    if (serialHandler.getCommand(&cmd)) {
        LOG_INFO("Command received: type=0x%02X, params_len=%d", cmd.type, cmd.paramsLen);
        
        // コマンド妥当性検証
        if (!commandParser.validate(&cmd)) {
            LOG_WARN("Command validation failed");
            Result error = commandParser.createError(RESULT_MALFORMED, "CRC or format error");
            serialHandler.sendResponse(&error);
            return;
        }
        
        // コマンド実行
        Result result;
        uint32_t startTime = millis();
        
        switch (cmd.type) {
            case CMD_DRAW_CIRCLE: {
                uint16_t x = (cmd.params[0] << 8) | cmd.params[1];
                uint16_t y = (cmd.params[2] << 8) | cmd.params[3];
                uint8_t radius = cmd.params[4];
                uint16_t color = (cmd.params[5] << 8) | cmd.params[6];
                
                result = drawingEngine.drawCircle(x, y, radius, color);
                break;
            }
            
            case CMD_DRAW_RECT: {
                uint16_t x = (cmd.params[0] << 8) | cmd.params[1];
                uint16_t y = (cmd.params[2] << 8) | cmd.params[3];
                uint16_t w = (cmd.params[4] << 8) | cmd.params[5];
                uint16_t h = (cmd.params[6] << 8) | cmd.params[7];
                uint16_t color = (cmd.params[8] << 8) | cmd.params[9];
                
                result = drawingEngine.drawRect(x, y, w, h, color);
                break;
            }
            
            case CMD_DRAW_TEXT: {
                uint16_t x = (cmd.params[0] << 8) | cmd.params[1];
                uint16_t y = (cmd.params[2] << 8) | cmd.params[3];
                const char* text = (const char*)&cmd.params[4];
                // テキスト後の色
                uint8_t textLen = strlen(text);
                uint16_t color = (cmd.params[4 + textLen + 1] << 8) | cmd.params[4 + textLen + 2];
                
                result = drawingEngine.drawText(x, y, text, color);
                break;
            }
            
            case CMD_CLEAR_SCREEN: {
                result = drawingEngine.clearScreen();
                break;
            }
            
            case CMD_SET_ITEM: {
                uint8_t itemId = cmd.params[0];
                result = drawingEngine.setActiveItem(itemId);
                break;
            }
            
            case CMD_PING: {
                result.status = RESULT_INFO;
                result.duration_ms = 0;
                strncpy(result.message, "PONG", sizeof(result.message) - 1);
                result.message[sizeof(result.message) - 1] = '\0';
                break;
            }
            
            default: {
                LOG_WARN("Unknown command type: 0x%02X", cmd.type);
                result = commandParser.createError(RESULT_PARSE, "Unknown command");
                break;
            }
        }
        
        result.duration_ms = millis() - startTime;
        
        // ログ出力
        if (result.status == RESULT_OK || result.status == RESULT_INFO) {
            LOG_INFO("Command executed: status=0x%02X, duration=%dms", result.status, result.duration_ms);
        } else {
            LOG_ERROR("Command failed: status=0x%02X, message=%s", result.status, result.message);
        }
        
        // 応答送信
        serialHandler.sendResponse(&result);
    }
    
    delay(10);  // CPU 負荷軽減
}
