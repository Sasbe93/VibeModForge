/* Minimal stand-in for ICU's unicode/ustring.h (see utypes.h). Part of VibeModForge (MIT). */
#pragma once
#include "utypes.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Same contracts as ICU: srcLength -1 = NUL-terminated input; returns the full output length even on
   U_BUFFER_OVERFLOW_ERROR; writes a terminating NUL when there is room (else U_STRING_NOT_TERMINATED_WARNING);
   does nothing when *pErrorCode already holds a failure. */
char *u_strToUTF8(char *dest, int32_t destCapacity, int32_t *pDestLength,
                  const UChar *src, int32_t srcLength, UErrorCode *pErrorCode);
UChar *u_strFromUTF32(UChar *dest, int32_t destCapacity, int32_t *pDestLength,
                      const UChar32 *src, int32_t srcLength, UErrorCode *pErrorCode);
UChar *u_strFromUTF8WithSub(UChar *dest, int32_t destCapacity, int32_t *pDestLength,
                            const char *src, int32_t srcLength, UChar32 subchar,
                            int32_t *pNumSubstitutions, UErrorCode *pErrorCode);
#ifdef __cplusplus
}
#endif
