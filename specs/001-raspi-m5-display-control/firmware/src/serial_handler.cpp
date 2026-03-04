#include "serial_handler.h"
#include <Arduino.h>
#include <string.h>

SerialHandler::SerialHandler() 
    : rxIndex(0), txIndex(0), queueIndex(0), lastRxTime(0) {
    memset(rxBuffer, 0, SERIAL_RX_BUFFER_SIZE);
    memset(txBuffer, 0, SERIAL_TX_BUFFER_SIZE);
    clearCommandQueue();
}

SerialHandler::~SerialHandler() {
}

void SerialHandler::init() {
    // UART1 は main() で既に初期化済み
    lastRxTime = millis();
}

void SerialHandler::addRxByte(uint8_t byte) {
    if (rxIndex >= SERIAL_RX_BUFFER_SIZE - 1) {
        // バッファオーバーフロー対策
        clearRxBuffer();
    }
    
    rxBuffer[rxIndex++] = byte;
    lastRxTime = millis();
    
    // フレーム区切り検出（\r\n）
    if (rxIndex >= 2 && rxBuffer[rxIndex - 2] == FRAME_DELIMITER_1 && 
        rxBuffer[rxIndex - 1] == FRAME_DELIMITER_2) {
        // フレーム完成
        rxIndex -= 2;  // \r\n を除外
    }
}

bool SerialHandler::getCommand(Command* cmd) {
    if (cmd == nullptr || queueIndex == 0) {
        return false;
    }
    
    // キューから取得
    memcpy(cmd, &commandQueue[0], sizeof(Command));
    
    // 次のコマンドにシフト
    for (uint8_t i = 0; i < queueIndex - 1; i++) {
        memcpy(&commandQueue[i], &commandQueue[i + 1], sizeof(Command));
    }
    queueIndex--;
    
    return true;
}

void SerialHandler::sendResponse(const Result* result) {
    if (result == nullptr) {
        return;
    }
    
    // フレーム構築：[0x01] [status] [message_len] [message] [CRC16] [\r\n]
    uint8_t frame[SERIAL_TX_BUFFER_SIZE];
    uint16_t idx = 0;
    
    frame[idx++] = FRAME_HEADER;
    frame[idx++] = result->status;
    
    uint8_t msgLen = strlen(result->message);
    frame[idx++] = msgLen;
    
    if (msgLen > 0) {
        memcpy(&frame[idx], result->message, msgLen);
        idx += msgLen;
    }
    
    // CRC-16 計算（ペイロード全体）
    uint16_t crc = calculateCRC16(frame, idx);
    frame[idx++] = (crc >> 8) & 0xFF;
    frame[idx++] = crc & 0xFF;
    
    frame[idx++] = FRAME_DELIMITER_1;
    frame[idx++] = FRAME_DELIMITER_2;
    
    // シリアル送信
    Serial1.write(frame, idx);
    Serial1.flush();
}

uint16_t SerialHandler::calculateCRC16(const uint8_t* data, uint16_t len) {
    if (data == nullptr || len == 0) {
        return 0xFFFF;
    }
    
    // CCITT CRC-16 (Poly: 0x1021, Init: 0xFFFF)
    uint16_t crc = 0xFFFF;
    
    for (uint16_t i = 0; i < len; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = crc << 1;
            }
            crc &= 0xFFFF;
        }
    }
    
    return crc;
}

bool SerialHandler::parseFrame(const uint8_t* buf, uint16_t len, Command* cmd) {
    if (buf == nullptr || len < 4 || cmd == nullptr) {
        return false;
    }
    
    // フレーム構造チェック
    if (buf[0] != FRAME_HEADER) {
        return false;
    }
    
    uint8_t cmdType = buf[1];
    uint8_t paramsLen = buf[2];
    
    // パラメータ長チェック
    if (len < 3 + paramsLen + 2) {  // Header + Type + Len + Params + CRC
        return false;
    }
    
    // CRC 検証
    uint16_t expectedCrc = calculateCRC16(buf, 3 + paramsLen);
    uint16_t receivedCrc = ((uint16_t)buf[3 + paramsLen] << 8) | buf[3 + paramsLen + 1];
    
    if (expectedCrc != receivedCrc) {
        return false;
    }
    
    // コマンド構築
    cmd->type = cmdType;
    cmd->paramsLen = paramsLen;
    if (paramsLen > 0) {
        memcpy(cmd->params, &buf[3], paramsLen);
    }
    cmd->crc = receivedCrc;
    
    return true;
}

void SerialHandler::clearRxBuffer() {
    memset(rxBuffer, 0, SERIAL_RX_BUFFER_SIZE);
    rxIndex = 0;
}

void SerialHandler::clearCommandQueue() {
    memset(commandQueue, 0, sizeof(commandQueue));
    queueIndex = 0;
}

uint16_t SerialHandler::findFrameEnd() {
    for (uint16_t i = 1; i < rxIndex; i++) {
        if (rxBuffer[i - 1] == FRAME_DELIMITER_1 && rxBuffer[i] == FRAME_DELIMITER_2) {
            return i - 1;
        }
    }
    return 0;
}
