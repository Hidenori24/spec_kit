#include "drawing_engine.h"
#include "M5StickCPlus2.h"

// DrawingEngine メンバー関数実装

DrawingEngine::DrawingEngine() : activeItem(0), vramUsed(0) {
}

DrawingEngine::~DrawingEngine() {
}

void DrawingEngine::init() {
    activeItem = 0;
    vramUsed = 0;
    // M5Stick LCD は main() で初期化済み
}

Result DrawingEngine::drawCircle(uint16_t x, uint16_t y, uint8_t radius, uint16_t color) {
    Result result;
    
    // パラメータ検証
    if (!validateBounds(x, y)) {
        result.status = RESULT_PARAM;
        strcpy(result.message, "Invalid coordinate");
        return result;
    }
    
    if (radius > 120) {
        result.status = RESULT_PARAM;
        strcpy(result.message, "Radius too large");
        return result;
    }
    
    // VRAM チェック（円の描画に必要なメモリ）
    uint32_t requiredBytes = (uint32_t)radius * radius * 4;  // 粗い推定
    if (!validateVRAM(requiredBytes)) {
        result.status = RESULT_SIZE;
        strcpy(result.message, "VRAM exceeded");
        return result;
    }
    
    try {
        acquireLCD();
        M5.Display.drawCircle(x, y, radius, color);
        releaseLCD();
        
        vramUsed += requiredBytes;
        result.status = RESULT_OK;
        strcpy(result.message, "OK");
    } catch (...) {
        result.status = RESULT_DEVICE;
        strcpy(result.message, "LCD error");
    }
    
    return result;
}

Result DrawingEngine::drawRect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color) {
    Result result;
    
    // パラメータ検証
    if (!validateBounds(x, y, w, h)) {
        result.status = RESULT_PARAM;
        strcpy(result.message, "Invalid rectangle");
        return result;
    }
    
    // VRAM チェック
    uint32_t requiredBytes = (uint32_t)w * h * 2;  // RGB565 = 2 bytes/pixel
    if (!validateVRAM(requiredBytes)) {
        result.status = RESULT_SIZE;
        strcpy(result.message, "VRAM exceeded");
        return result;
    }
    
    try {
        acquireLCD();
        M5.Display.drawRect(x, y, w, h, color);
        releaseLCD();
        
        vramUsed += requiredBytes;
        result.status = RESULT_OK;
        strcpy(result.message, "OK");
    } catch (...) {
        result.status = RESULT_DEVICE;
        strcpy(result.message, "LCD error");
    }
    
    return result;
}

Result DrawingEngine::drawText(uint16_t x, uint16_t y, const char* text, uint16_t color) {
    Result result;
    
    if (text == nullptr || strlen(text) > 128) {
        result.status = RESULT_PARAM;
        strcpy(result.message, "Invalid text");
        return result;
    }
    
    if (!validateBounds(x, y)) {
        result.status = RESULT_PARAM;
        strcpy(result.message, "Invalid coordinate");
        return result;
    }
    
    try {
        acquireLCD();
        M5.Display.setTextColor(color);
        M5.Display.drawString(text, x, y);
        releaseLCD();
        
        uint32_t requiredBytes = strlen(text) * 8;  // 粗い推定
        vramUsed += requiredBytes;
        result.status = RESULT_OK;
        strcpy(result.message, "OK");
    } catch (...) {
        result.status = RESULT_DEVICE;
        strcpy(result.message, "LCD error");
    }
    
    return result;
}

Result DrawingEngine::clearScreen() {
    Result result;
    
    try {
        acquireLCD();
        M5.Display.fillScreen(TFT_BLACK);
        releaseLCD();
        
        vramUsed = 0;  // リセット
        result.status = RESULT_OK;
        strcpy(result.message, "OK");
    } catch (...) {
        result.status = RESULT_DEVICE;
        strcpy(result.message, "LCD error");
    }
    
    return result;
}

Result DrawingEngine::setActiveItem(uint8_t itemId) {
    Result result;
    
    if (itemId >= MAX_ITEMS) {
        result.status = RESULT_NOTFOUND;
        strcpy(result.message, "Item not found");
        return result;
    }
    
    activeItem = itemId;
    result.status = RESULT_OK;
    strcpy(result.message, "OK");
    
    return result;
}

bool DrawingEngine::validateBounds(uint16_t x, uint16_t y) {
    return (x >= 0 && x < FRAME_WIDTH && y >= 0 && y < FRAME_HEIGHT);
}

bool DrawingEngine::validateBounds(uint16_t x, uint16_t y, uint16_t w, uint16_t h) {
    return validateBounds(x, y) && (x + w <= FRAME_WIDTH) && (y + h <= FRAME_HEIGHT);
}

bool DrawingEngine::validateVRAM(uint32_t requiredBytes) {
    return (vramUsed + requiredBytes < VRAM_MAX);
}

void DrawingEngine::releaseVRAM(uint32_t bytes) {
    if (vramUsed >= bytes) {
        vramUsed -= bytes;
    }
}

void DrawingEngine::acquireLCD() {
    // LCD ミューテックス取得（今後実装：マルチスレッド対応）
}

void DrawingEngine::releaseLCD() {
    // LCD ミューテックス解放
}
