/* Minimal stand-in for ICU's unicode/utypes.h: only what Chkdraft's cross_cut/simple_icu.cpp needs.
   Used when isomtool is built without the real ICU library (default on Windows, see ../CMakeLists.txt).
   Values match ICU so code that tests error codes behaves the same. Part of VibeModForge (MIT). */
#pragma once
#include <stdint.h>
#ifdef __cplusplus
typedef char16_t UChar;
#else
typedef uint16_t UChar;
#endif
typedef int32_t UChar32;
typedef int8_t UBool;
typedef enum UErrorCode {
    U_STRING_NOT_TERMINATED_WARNING = -124,
    U_ZERO_ERROR = 0,
    U_ILLEGAL_ARGUMENT_ERROR = 1,
    U_INVALID_CHAR_FOUND = 10,
    U_BUFFER_OVERFLOW_ERROR = 15
} UErrorCode;
#define U_SUCCESS(x) ((x) <= U_ZERO_ERROR)
#define U_FAILURE(x) ((x) > U_ZERO_ERROR)
#define U_SENTINEL (-1)
