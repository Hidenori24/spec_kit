#ifndef COMMAND_PARSER_H
#define COMMAND_PARSER_H

#include <stdint.h>
#include <string.h>
#include "drawing_engine.h"

// ========== CommandParser クラス ==========
class CommandParser {
private:
    static const uint16_t MAX_COMMAND_SIZE = 256;

public:
    CommandParser();
    ~CommandParser();
    
    // コマンド検証
    bool validate(const Command* cmd);
    
    // エラー結果生成
    Result createError(uint8_t statusCode, const char* message);
    
    // パラメータ検証
    bool validateDrawCircleParams(const Command* cmd);
    bool validateDrawRectParams(const Command* cmd);
    bool validateDrawTextParams(const Command* cmd);
    bool validateSetItemParams(const Command* cmd);
    
private:
    // 内部検証
    bool validateCommandType(uint8_t type);
    bool validateParamLength(const Command* cmd);
};

#endif // COMMAND_PARSER_H
