#ifndef SERIAL_HANDLER_H
#define SERIAL_HANDLER_H

#include <stdint.h>
#include "drawing_engine.h"

// ========== バッファサイズ定義 ==========
#define SERIAL_RX_BUFFER_SIZE   256
#define SERIAL_TX_BUFFER_SIZE   256
#define COMMAND_QUEUE_SIZE      10

// ========== フレーム定義 ==========
#define FRAME_HEADER            0x01
#define FRAME_DELIMITER_1       0x0D  // '\r'
#define FRAME_DELIMITER_2       0x0A  // '\n'

// ========== SerialHandler クラス ==========
class SerialHandler {
private:
    uint8_t rxBuffer[SERIAL_RX_BUFFER_SIZE];
    uint8_t txBuffer[SERIAL_TX_BUFFER_SIZE];
    
    uint16_t rxIndex;
    uint16_t txIndex;
    
    Command commandQueue[COMMAND_QUEUE_SIZE];
    uint8_t queueIndex;
    
    uint32_t lastRxTime;
    static const uint32_t RX_TIMEOUT_MS = 5000;

public:
    SerialHandler();
    ~SerialHandler();
    
    // 初期化
    void init();
    
    // シリアル受信
    void addRxByte(uint8_t byte);
    bool getCommand(Command* cmd);
    
    // シリアル送信
    void sendResponse(const Result* result);
    
    // ヘルパー
    uint16_t calculateCRC16(const uint8_t* data, uint16_t len);
    
private:
    // 内部処理
    bool parseFrame(const uint8_t* buf, uint16_t len, Command* cmd);
    void clearRxBuffer();
    void clearCommandQueue();
    uint16_t findFrameEnd();
};

#endif // SERIAL_HANDLER_H
