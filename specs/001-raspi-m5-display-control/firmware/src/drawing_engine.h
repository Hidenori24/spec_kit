#ifndef DRAWING_ENGINE_H
#define DRAWING_ENGINE_H

#include <stdint.h>
#include <string.h>

// ========== コマンドタイプ定義 ==========
#define CMD_DRAW_CIRCLE   0x11
#define CMD_DRAW_RECT     0x12
#define CMD_DRAW_TEXT     0x13
#define CMD_CLEAR_SCREEN  0x14
#define CMD_SET_ITEM      0x15
#define CMD_PING          0x16

// ========== ステータスコード定義 ==========
#define RESULT_OK           0x00  // 成功
#define RESULT_INFO         0x10  // 情報応答（PING用）
#define RESULT_PARSE        0xE0  // 解析エラー
#define RESULT_PARAM        0xE1  // パラメータエラー
#define RESULT_SIZE         0xE2  // サイズ/VRAM エラー
#define RESULT_NOTFOUND     0xE3  // アイテムなし
#define RESULT_TIMEOUT      0xE4  // タイムアウト
#define RESULT_MALFORMED    0xE5  // フレーム破損
#define RESULT_DEVICE       0xE6  // デバイスエラー
#define RESULT_BUSY         0xE7  // ビジー

// ========== 制約定義 ==========
#define VRAM_MAX            (8 * 1024 * 1024)  // 8MB
#define FRAME_WIDTH         135
#define FRAME_HEIGHT        240
#define MAX_ITEMS           10
#define MAX_MESSAGE_LEN     64

// ========== データ構造 ==========

// コマンド構造体
typedef struct {
    uint8_t  type;
    uint8_t  params[256];
    uint16_t paramsLen;
    uint16_t crc;
} Command;

// 結果構造体
typedef struct {
    uint8_t  status;           // ステータスコード
    uint16_t duration_ms;      // 実行時間
    char     message[MAX_MESSAGE_LEN];  // エラーメッセージ/情報
    uint16_t crc;
} Result;

// ========== DrawingEngine クラス ==========
class DrawingEngine {
private:
    uint8_t activeItem;
    uint32_t vramUsed;

public:
    DrawingEngine();
    ~DrawingEngine();
    
    // 初期化
    void init();
    
    // 描画メソッド
    Result drawCircle(uint16_t x, uint16_t y, uint8_t radius, uint16_t color);
    Result drawRect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color);
    Result drawText(uint16_t x, uint16_t y, const char* text, uint16_t color);
    Result clearScreen();
    
    // アイテム管理
    Result setActiveItem(uint8_t itemId);
    uint8_t getActiveItem() const { return activeItem; }
    
    // VRAM 管理
    bool validateVRAM(uint32_t requiredBytes);
    void releaseVRAM(uint32_t bytes);
    uint32_t getVRAMUsed() const { return vramUsed; }
    
private:
    // 内部検証
    bool validateBounds(uint16_t x, uint16_t y);
    bool validateBounds(uint16_t x, uint16_t y, uint16_t w, uint16_t h);
    
    // LCD アクセス
    void acquireLCD();
    void releaseLCD();
};

#endif // DRAWING_ENGINE_H
