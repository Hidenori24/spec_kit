#include "command_parser.h"

CommandParser::CommandParser() {
}

CommandParser::~CommandParser() {
}

bool CommandParser::validate(const Command* cmd) {
    if (cmd == nullptr) {
        return false;
    }
    
    // コマンドタイプ検証
    if (!validateCommandType(cmd->type)) {
        return false;
    }
    
    // パラメータ長検証
    if (!validateParamLength(cmd)) {
        return false;
    }
    
    // コマンド固有の検証
    switch (cmd->type) {
        case CMD_DRAW_CIRCLE:
            return validateDrawCircleParams(cmd);
        case CMD_DRAW_RECT:
            return validateDrawRectParams(cmd);
        case CMD_DRAW_TEXT:
            return validateDrawTextParams(cmd);
        case CMD_CLEAR_SCREEN:
            return (cmd->paramsLen == 0);
        case CMD_SET_ITEM:
            return validateSetItemParams(cmd);
        case CMD_PING:
            return (cmd->paramsLen == 0);
        default:
            return false;
    }
}

Result CommandParser::createError(uint8_t statusCode, const char* message) {
    Result result;
    result.status = statusCode;
    result.duration_ms = 0;
    
    if (message != nullptr) {
        strncpy(result.message, message, sizeof(result.message) - 1);
        result.message[sizeof(result.message) - 1] = '\0';
    } else {
        strcpy(result.message, "Unknown error");
    }
    
    return result;
}

bool CommandParser::validateDrawCircleParams(const Command* cmd) {
    if (cmd == nullptr || cmd->paramsLen != 7) {
        return false;
    }
    
    // x: 0-319, y: 0-239, radius: 1-120, color: 0x0000-0xFFFF
    uint16_t x = ((uint16_t)cmd->params[0] << 8) | cmd->params[1];
    uint16_t y = ((uint16_t)cmd->params[2] << 8) | cmd->params[3];
    uint8_t radius = cmd->params[4];
    // uint16_t color = ((uint16_t)cmd->params[5] << 8) | cmd->params[6];
    
    if (x >= 135 || y >= 240 || radius < 1 || radius > 120) {
        return false;
    }
    
    return true;
}

bool CommandParser::validateDrawRectParams(const Command* cmd) {
    if (cmd == nullptr || cmd->paramsLen != 10) {
        return false;
    }
    
    uint16_t x = ((uint16_t)cmd->params[0] << 8) | cmd->params[1];
    uint16_t y = ((uint16_t)cmd->params[2] << 8) | cmd->params[3];
    uint16_t w = ((uint16_t)cmd->params[4] << 8) | cmd->params[5];
    uint16_t h = ((uint16_t)cmd->params[6] << 8) | cmd->params[7];
    // uint16_t color = ((uint16_t)cmd->params[8] << 8) | cmd->params[9];
    
    if (x >= 135 || y >= 240 || w < 1 || h < 1 || 
        (x + w) > 135 || (y + h) > 240) {
        return false;
    }
    
    return true;
}

bool CommandParser::validateDrawTextParams(const Command* cmd) {
    if (cmd == nullptr || cmd->paramsLen < 5) {
        return false;
    }
    
    uint16_t x = ((uint16_t)cmd->params[0] << 8) | cmd->params[1];
    uint16_t y = ((uint16_t)cmd->params[2] << 8) | cmd->params[3];
    
    // テキスト部分のサイズ確認
    // params[4]以降がテキスト＋カラー
    uint8_t textLen = cmd->paramsLen - 7;  // x(2) + y(2) + color(2) + null(1)
    
    if (x >= 135 || y >= 240 || textLen < 1 || textLen > 128) {
        return false;
    }
    
    return true;
}

bool CommandParser::validateSetItemParams(const Command* cmd) {
    if (cmd == nullptr || cmd->paramsLen != 1) {
        return false;
    }
    
    uint8_t itemId = cmd->params[0];
    
    if (itemId >= 10) {
        return false;
    }
    
    return true;
}

bool CommandParser::validateCommandType(uint8_t type) {
    return (type >= CMD_DRAW_CIRCLE && type <= CMD_PING);
}

bool CommandParser::validateParamLength(const Command* cmd) {
    if (cmd == nullptr) {
        return false;
    }
    
    // パラメータ長の上限確認
    if (cmd->paramsLen > 254) {
        return false;
    }
    
    return true;
}
