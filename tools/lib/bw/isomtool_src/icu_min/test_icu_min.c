/* Known-answer tests for icu_min.c (expected values produced by ICU 76). Build: see ../CMakeLists.txt (ctest)
   or  cc -I. test_icu_min.c icu_min.c -o test_icu_min && ./test_icu_min   Part of VibeModForge (MIT). */
#include "unicode/ustring.h"
#include <stdio.h>
#include <string.h>

static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)

static void from8(const char *s, int32_t n, UChar32 sub, const UChar *want, int32_t wantLen, int32_t wantSubs) {
    UChar d[32]; int32_t len = -1, subs = -1; UErrorCode e = U_ZERO_ERROR;
    u_strFromUTF8WithSub(d, 32, &len, s, n, sub, &subs, &e);
    CHECK(e == U_ZERO_ERROR); CHECK(len == wantLen); CHECK(subs == wantSubs);
    CHECK(len == wantLen && memcmp(d, want, (size_t)wantLen * sizeof(UChar)) == 0); CHECK(d[wantLen] == 0);
}

int main(void) {
    /* UTF-8 -> UTF-16, valid input incl. supplementary characters */
    { const UChar w[] = {0x4A, 0xF6, 0x72, 0x67, 0x20AC, 0xD83D, 0xDE00};
      from8("J\xC3\xB6rg\xE2\x82\xAC\xF0\x9F\x98\x80", 12, '?', w, 7, 0); }
    /* each maximal ill-formed subpart becomes one substitution character (Unicode 3-7, ICU behaviour) */
    { const UChar w[] = {'?', '?'};            from8("\xC0\xAF", 2, '?', w, 2, 2); }          /* overlong '/' */
    { const UChar w[] = {'?', '?', '?'};       from8("\xED\xA0\x80", 3, '?', w, 3, 3); }      /* surrogate */
    { const UChar w[] = {'?', '?', '?', '?'};  from8("\xF4\x90\x80\x80", 4, '?', w, 4, 4); }  /* > U+10FFFF */
    { const UChar w[] = {'?', 'A'};            from8("\xE2\x82" "A", 3, '?', w, 2, 1); }      /* truncated */
    { const UChar w[] = {0xFFFD, 'B'};         from8("\xF0\x9F\x98" "B", 4, 0xFFFD, w, 2, 1); }
    /* no substitution character: invalid input is an error */
    { UChar d[8]; int32_t len = -1; UErrorCode e = U_ZERO_ERROR;
      CHECK(u_strFromUTF8WithSub(d, 8, &len, "\xFF", 1, U_SENTINEL, NULL, &e) == NULL); CHECK(e == U_INVALID_CHAR_FOUND); }
    /* UTF-16 -> UTF-8 */
    { const UChar s[] = {0x4A, 0xF6, 0x20AC, 0xD83D, 0xDE00, 0}; char d[16]; int32_t len = -1; UErrorCode e = U_ZERO_ERROR;
      u_strToUTF8(d, 16, &len, s, -1, &e);
      CHECK(e == U_ZERO_ERROR); CHECK(len == 10); CHECK(memcmp(d, "J\xC3\xB6\xE2\x82\xAC\xF0\x9F\x98\x80", 11) == 0); }
    { const UChar s[] = {0x41, 0xD800, 0x42}; char d[16]; int32_t len = -1; UErrorCode e = U_ZERO_ERROR;   /* lone surrogate */
      CHECK(u_strToUTF8(d, 16, &len, s, 3, &e) == NULL); CHECK(e == U_INVALID_CHAR_FOUND); CHECK(len == -1); }
    /* preflighting, exact fit and overflow */
    { const UChar s[] = {0x41, 0xF6}; char d[4]; int32_t len = -1; UErrorCode e = U_ZERO_ERROR;
      u_strToUTF8(NULL, 0, &len, s, 2, &e); CHECK(e == U_BUFFER_OVERFLOW_ERROR); CHECK(len == 3);
      e = U_ZERO_ERROR; u_strToUTF8(d, 3, &len, s, 2, &e); CHECK(e == U_STRING_NOT_TERMINATED_WARNING); CHECK(len == 3);
      e = U_ZERO_ERROR; u_strToUTF8(d, 2, &len, s, 2, &e); CHECK(e == U_BUFFER_OVERFLOW_ERROR); CHECK(d[0] == 'A'); }
    /* UTF-32 -> UTF-16 */
    { const UChar32 s[] = {0x41, 0x1F600}; UChar d[8]; int32_t len = -1; UErrorCode e = U_ZERO_ERROR;
      u_strFromUTF32(d, 8, &len, s, 2, &e);
      CHECK(e == U_ZERO_ERROR); CHECK(len == 3); CHECK(d[0] == 0x41 && d[1] == 0xD83D && d[2] == 0xDE00 && d[3] == 0); }
    { const UChar32 s[] = {0x110000}; UChar d[8]; int32_t len = -1; UErrorCode e = U_ZERO_ERROR;
      CHECK(u_strFromUTF32(d, 8, &len, s, 1, &e) == NULL); CHECK(e == U_INVALID_CHAR_FOUND); }
    /* a failure passed in is kept and nothing happens */
    { UChar d[4] = {7, 7, 7, 7}; int32_t len = -1; UErrorCode e = U_ILLEGAL_ARGUMENT_ERROR;
      CHECK(u_strFromUTF8WithSub(d, 4, &len, "A", 1, '?', NULL, &e) == NULL); CHECK(d[0] == 7 && len == -1); }
    printf(fails ? "icu_min: %d FAILED\n" : "icu_min: all tests passed\n", fails);
    return fails != 0;
}
