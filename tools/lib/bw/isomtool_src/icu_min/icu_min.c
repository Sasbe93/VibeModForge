/* Minimal UTF-8/UTF-16/UTF-32 converters with ICU's contracts, for building isomtool without the ICU library.
 *
 * Chkdraft's cross_cut/simple_icu.cpp is the only ICU user in the code isomtool compiles, and it calls exactly
 * u_strToUTF8, u_strFromUTF32 and u_strFromUTF8WithSub. isomtool itself never reaches them (it reads its inputs
 * with std::ifstream), but the mapping-core objects reference them, so they have to link. These implementations
 * follow ICU's documented behaviour (argument checks, U_INVALID_CHAR_FOUND for unpaired surrogates and invalid
 * code points, substitution of each maximal ill-formed UTF-8 subpart, preflighting, NUL termination and its
 * warning) and are cross-checked against the real ICU by test_icu_min.c.
 *
 * Part of VibeModForge (MIT).
 */
#include "unicode/ustring.h"
#include <stddef.h>

/* NUL-terminate like ICU's u_terminateChars/u_terminateUChars. */
#define TERMINATE(dest, cap, len, ec) do { \
    if (U_SUCCESS(*(ec))) { \
        if ((len) < (cap)) { (dest)[len] = 0; if (*(ec) == U_STRING_NOT_TERMINATED_WARNING) *(ec) = U_ZERO_ERROR; } \
        else if ((len) == (cap)) *(ec) = U_STRING_NOT_TERMINATED_WARNING; \
        else *(ec) = U_BUFFER_OVERFLOW_ERROR; \
    } } while (0)

static int bad_args(const void *src, int32_t srcLength, const void *dest, int32_t destCapacity, UErrorCode *ec) {
    if ((src == NULL && srcLength != 0) || srcLength < -1 || destCapacity < 0 || (dest == NULL && destCapacity > 0)) {
        *ec = U_ILLEGAL_ARGUMENT_ERROR;
        return 1;
    }
    return 0;
}

/* Append one code point as UTF-16 (u_strFromUTF8WithSub); once something did not fit, only count. */
static void put16(UChar *dest, int32_t cap, int32_t *n, int *full, UChar32 cp) {
    if (cp < 0x10000) {
        if (!*full && *n < cap) dest[*n] = (UChar)cp; else *full = 1;
        *n += 1;
    } else {
        if (!*full && *n < cap) dest[*n] = (UChar)(0xD7C0 + (cp >> 10)); else *full = 1;   /* like ICU, a lead */
        if (!*full && *n + 1 < cap) dest[*n + 1] = (UChar)(0xDC00 | (cp & 0x3FF)); else *full = 1; /* may fit alone */
        *n += 2;
    }
}

char *u_strToUTF8(char *dest, int32_t destCapacity, int32_t *pDestLength,
                  const UChar *src, int32_t srcLength, UErrorCode *pErrorCode) {
    int32_t i = 0, n = 0;
    int full = 0;
    if (pErrorCode == NULL || U_FAILURE(*pErrorCode)) return NULL;
    if (bad_args(src, srcLength, dest, destCapacity, pErrorCode)) return NULL;
    if (srcLength == -1) { srcLength = 0; while (src[srcLength]) srcLength++; }
    while (i < srcLength) {
        UChar32 cp = src[i++];
        unsigned char b[4];
        int32_t k;
        if (cp >= 0xD800 && cp <= 0xDFFF) {
            if (cp <= 0xDBFF && i < srcLength && src[i] >= 0xDC00 && src[i] <= 0xDFFF)
                cp = 0x10000 + ((cp - 0xD800) << 10) + (src[i++] - 0xDC00);
            else { *pErrorCode = U_INVALID_CHAR_FOUND; return NULL; }
        }
        if (cp < 0x80) { b[0] = (unsigned char)cp; k = 1; }
        else if (cp < 0x800) { b[0] = (unsigned char)(0xC0 | (cp >> 6)); b[1] = (unsigned char)(0x80 | (cp & 0x3F)); k = 2; }
        else if (cp < 0x10000) {
            b[0] = (unsigned char)(0xE0 | (cp >> 12)); b[1] = (unsigned char)(0x80 | ((cp >> 6) & 0x3F));
            b[2] = (unsigned char)(0x80 | (cp & 0x3F)); k = 3;
        } else {
            b[0] = (unsigned char)(0xF0 | (cp >> 18)); b[1] = (unsigned char)(0x80 | ((cp >> 12) & 0x3F));
            b[2] = (unsigned char)(0x80 | ((cp >> 6) & 0x3F)); b[3] = (unsigned char)(0x80 | (cp & 0x3F)); k = 4;
        }
        if (!full && n + k <= destCapacity) { int32_t j; for (j = 0; j < k; j++) dest[n + j] = (char)b[j]; }
        else full = 1;
        n += k;
    }
    if (pDestLength) *pDestLength = n;
    TERMINATE(dest, destCapacity, n, pErrorCode);
    return dest;
}

UChar *u_strFromUTF32(UChar *dest, int32_t destCapacity, int32_t *pDestLength,
                      const UChar32 *src, int32_t srcLength, UErrorCode *pErrorCode) {
    int32_t i, n = 0, w = 0;
    if (pErrorCode == NULL || U_FAILURE(*pErrorCode)) return NULL;
    if (bad_args(src, srcLength, dest, destCapacity, pErrorCode)) return NULL;
    if (srcLength == -1) { srcLength = 0; while (src[srcLength]) srcLength++; }
    for (i = 0; i < srcLength; i++) {
        UChar32 cp = src[i];
        if (cp < 0 || cp > 0x10FFFF || (cp >= 0xD800 && cp <= 0xDFFF)) { *pErrorCode = U_INVALID_CHAR_FOUND; return NULL; }
        /* Same quirk as ICU's u_strFromUTF32: a unit or pair that does not fit is only counted, and later
           units that still fit are written right after the last written one (only matters on overflow). */
        if (cp < 0x10000) { if (w < destCapacity) dest[w++] = (UChar)cp; else n++; }
        else if (w + 2 <= destCapacity) { dest[w++] = (UChar)(0xD7C0 + (cp >> 10)); dest[w++] = (UChar)(0xDC00 | (cp & 0x3FF)); }
        else n += 2;
    }
    n += w;
    if (pDestLength) *pDestLength = n;
    TERMINATE(dest, destCapacity, n, pErrorCode);
    return dest;
}

/* Length of the well-formed sequence starting at s[i] (Unicode table 3-7), or 0 if it is ill-formed;
   *sub receives the length of the maximal ill-formed subpart that one substitution character replaces. */
static int utf8_seq(const unsigned char *s, int32_t i, int32_t len, UChar32 *out, int32_t *sub) {
    unsigned char c = s[i];
    int need, k;
    unsigned char lo = 0x80, hi = 0xBF;
    UChar32 cp;
    if (c < 0x80) { *out = c; return 1; }
    if (c >= 0xC2 && c <= 0xDF) { need = 2; cp = c & 0x1F; }
    else if (c >= 0xE0 && c <= 0xEF) { need = 3; cp = c & 0x0F; if (c == 0xE0) lo = 0xA0; else if (c == 0xED) hi = 0x9F; }
    else if (c >= 0xF0 && c <= 0xF4) { need = 4; cp = c & 0x07; if (c == 0xF0) lo = 0x90; else if (c == 0xF4) hi = 0x8F; }
    else { *sub = 1; return 0; }
    for (k = 1; k < need; k++) {
        unsigned char t;
        if (i + k >= len) { *sub = k; return 0; }
        t = s[i + k];
        if (t < lo || t > hi) { *sub = k; return 0; }
        lo = 0x80; hi = 0xBF;
        cp = (cp << 6) | (t & 0x3F);
    }
    *out = cp;
    return need;
}

UChar *u_strFromUTF8WithSub(UChar *dest, int32_t destCapacity, int32_t *pDestLength,
                            const char *src, int32_t srcLength, UChar32 subchar,
                            int32_t *pNumSubstitutions, UErrorCode *pErrorCode) {
    const unsigned char *s = (const unsigned char *)src;
    int32_t i = 0, n = 0, subs = 0;
    int full = 0;
    if (pErrorCode == NULL || U_FAILURE(*pErrorCode)) return NULL;
    if (bad_args(src, srcLength, dest, destCapacity, pErrorCode) ||
        subchar > 0x10FFFF || (subchar >= 0xD800 && subchar <= 0xDFFF)) {
        *pErrorCode = U_ILLEGAL_ARGUMENT_ERROR;
        return NULL;
    }
    if (pNumSubstitutions) *pNumSubstitutions = 0;
    if (srcLength == -1) { srcLength = 0; while (s[srcLength]) srcLength++; }
    while (i < srcLength) {
        UChar32 cp = 0;
        int32_t sub = 0;
        int k = utf8_seq(s, i, srcLength, &cp, &sub);
        if (k) i += k;
        else {
            if (subchar < 0) { *pErrorCode = U_INVALID_CHAR_FOUND; return NULL; }
            cp = subchar; subs++; i += sub;
        }
        put16(dest, destCapacity, &n, &full, cp);
    }
    if (pNumSubstitutions) *pNumSubstitutions = subs;
    if (pDestLength) *pDestLength = n;
    TERMINATE(dest, destCapacity, n, pErrorCode);
    return dest;
}
