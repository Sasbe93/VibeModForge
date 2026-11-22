# isomtool: paints ISOM terrain with Chkdraft's mapping core (see docs/bw-terrain-setup.md).
#
# One CMake file for Linux, macOS and Windows (MinGW-w64 or MSVC). Third-party sources are never committed;
# clone them into external/ next to this file (or point the ISOMTOOL_*_DIR cache variables elsewhere):
#   external/Chkdraft   https://github.com/TheNitesWhoSay/Chkdraft  (MIT)
#   external/RareCpp    https://github.com/TheNitesWhoSay/RareCpp   (MIT)
#   external/StormLib   https://github.com/ladislav-zezula/StormLib (MIT)  optional on Linux, see below
#   external/CascLib    https://github.com/ladislav-zezula/CascLib  (MIT)  optional on Linux, see below
#
# StormLib/CascLib: when both source trees exist they are built here as static libraries (no install step, no
# patches to their sources). Otherwise installed libraries are used (ISOMTOOL_STORMLIB_LIBRARY /
# ISOMTOOL_CASCLIB_LIBRARY, default: libstorm/libcasc found in the usual prefixes such as /usr/local/lib).
#
# ICU: Chkdraft's simple_icu.cpp needs three UTF converters from ICU. ISOMTOOL_ICU=AUTO (default) links the
# system ICU (icuuc) when CMake finds it and otherwise compiles icu_min/, our drop-in implementation of exactly
# those three functions with ICU's behaviour (checked against ICU by icu_min/test_icu_min.c).
cmake_minimum_required(VERSION 3.24)
project(isomtool C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(ISOMTOOL_CHKDRAFT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/Chkdraft" CACHE PATH "Chkdraft source tree")
set(ISOMTOOL_RARECPP_DIR  "${CMAKE_CURRENT_SOURCE_DIR}/external/RareCpp"  CACHE PATH "RareCpp source tree")
set(ISOMTOOL_STORMLIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/StormLib" CACHE PATH "StormLib source tree (optional)")
set(ISOMTOOL_CASCLIB_DIR  "${CMAKE_CURRENT_SOURCE_DIR}/external/CascLib"  CACHE PATH "CascLib source tree (optional)")
option(ISOMTOOL_CASCLIB_DLL "Also build CascLib as a shared library (CascLib.dll / libcasc.so) for tools/bw/extract_tilesets.py --casc" OFF)
set(ISOMTOOL_ICU AUTO CACHE STRING "AUTO, SYSTEM (link icuuc) or BUNDLED (icu_min/)")
set_property(CACHE ISOMTOOL_ICU PROPERTY STRINGS AUTO SYSTEM BUNDLED)

set(CD "${ISOMTOOL_CHKDRAFT_DIR}/src")
foreach(f "${CD}/mapping_core/scenario.h" "${ISOMTOOL_RARECPP_DIR}/include/rarecpp/reflect.h")
    if(NOT EXISTS "${f}")
        message(FATAL_ERROR "Missing ${f}. Clone Chkdraft and RareCpp into ${CMAKE_CURRENT_SOURCE_DIR}/external "
                            "(docs/bw-terrain-setup.md) or set ISOMTOOL_CHKDRAFT_DIR / ISOMTOOL_RARECPP_DIR.")
    endif()
endforeach()

# ---- StormLib + CascLib ----
if(EXISTS "${ISOMTOOL_STORMLIB_DIR}/CMakeLists.txt" AND EXISTS "${ISOMTOOL_CASCLIB_DIR}/CMakeLists.txt")
    message(STATUS "isomtool: building StormLib and CascLib from source")
    # One zlib and one bzip2 for both libraries. Their bundled copies differ (StormLib ships zlib 1.2.5,
    # CascLib 1.2.11); compiling both into one binary gives duplicate symbols, and silencing that with
    # --allow-multiple-definition would mix two zlib versions. Use the system libraries when they exist,
    # otherwise build StormLib's complete copy once and hand it to both through find_package redirects.
    find_package(ZLIB QUIET)
    find_package(BZip2 QUIET)
    if(NOT ZLIB_FOUND OR NOT BZip2_FOUND)
        set(SZ "${ISOMTOOL_STORMLIB_DIR}/src")
        if(NOT ZLIB_FOUND)
            add_library(isomtool_zlib STATIC ${SZ}/zlib/adler32.c ${SZ}/zlib/compress.c ${SZ}/zlib/crc32.c
                ${SZ}/zlib/deflate.c ${SZ}/zlib/inffast.c ${SZ}/zlib/inflate.c ${SZ}/zlib/inftrees.c
                ${SZ}/zlib/trees.c ${SZ}/zlib/zutil.c)
            target_include_directories(isomtool_zlib PUBLIC $<BUILD_INTERFACE:${SZ}/zlib>)
            add_library(ZLIB::ZLIB ALIAS isomtool_zlib)
            file(WRITE "${CMAKE_FIND_PACKAGE_REDIRECTS_DIR}/zlib-config.cmake" "# provided by isomtool (StormLib's zlib)\n")
            # CascLib declares an install export set that lists its link libraries; isomtool is never installed,
            # but CMake still requires every linked target to be in some export set.
            install(TARGETS isomtool_zlib EXPORT CascLibTargets ARCHIVE DESTINATION lib)
        endif()
        if(NOT BZip2_FOUND)
            add_library(isomtool_bzip2 STATIC ${SZ}/bzip2/blocksort.c ${SZ}/bzip2/bzlib.c ${SZ}/bzip2/compress.c
                ${SZ}/bzip2/crctable.c ${SZ}/bzip2/decompress.c ${SZ}/bzip2/huffman.c ${SZ}/bzip2/randtable.c)
            target_compile_definitions(isomtool_bzip2 PRIVATE BZ_STRICT_ANSI)
            target_include_directories(isomtool_bzip2 PUBLIC $<BUILD_INTERFACE:${SZ}/bzip2>)
            add_library(BZip2::BZip2 ALIAS isomtool_bzip2)
            file(WRITE "${CMAKE_FIND_PACKAGE_REDIRECTS_DIR}/bzip2-config.cmake" "# provided by isomtool (StormLib's bzip2)\n")
        endif()
    endif()
    set(BUILD_SHARED_LIBS OFF)
    set(STORM_USE_BUNDLED_LIBRARIES OFF CACHE BOOL "" FORCE)
    set(WITH_BUNDLED_LIBTOMMATH ON CACHE BOOL "" FORCE)
    set(WITH_BUNDLED_LIBTOMCRYPT ON CACHE BOOL "" FORCE)
    set(STORM_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(STORM_SKIP_INSTALL ON CACHE BOOL "" FORCE)
    set(CASC_BUILD_SHARED_LIB ${ISOMTOOL_CASCLIB_DLL} CACHE BOOL "" FORCE)
    set(CASC_BUILD_STATIC_LIB ON CACHE BOOL "" FORCE)
    set(CASC_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    # CascLib still declares cmake_minimum_required(3.2), which CMake 4 refuses; this documented variable
    # raises the policy level for that subproject without editing its sources.
    set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
    add_subdirectory("${ISOMTOOL_STORMLIB_DIR}" "${CMAKE_CURRENT_BINARY_DIR}/StormLib" EXCLUDE_FROM_ALL)
    add_subdirectory("${ISOMTOOL_CASCLIB_DIR}" "${CMAKE_CURRENT_BINARY_DIR}/CascLib" EXCLUDE_FROM_ALL)
    unset(CMAKE_POLICY_VERSION_MINIMUM)
    set(ISOMTOOL_ARCHIVE_LIBS storm casc_static)
    if(WIN32)
        # CascLib's HTTP stream uses Winsock. MSVC gets it from a #pragma comment(lib) in CascFiles.cpp,
        # MinGW ignores that pragma, and CascLib's CMakeLists only lists wininet.
        list(APPEND ISOMTOOL_ARCHIVE_LIBS ws2_32 wininet)
    endif()
    set(ISOMTOOL_ARCHIVE_INCLUDES "${ISOMTOOL_STORMLIB_DIR}/src" "${ISOMTOOL_CASCLIB_DIR}/src")
    if(ISOMTOOL_CASCLIB_DLL)
        if(WIN32)
            target_link_libraries(casc ws2_32)                  # see above
            set_target_properties(casc PROPERTIES PREFIX "")    # CascLib.dll with MinGW too (not libCascLib.dll)
        endif()
        if(MINGW)
            # Python 3.8+ does not search PATH for a DLL's dependencies; link the MinGW runtime in statically so
            # CascLib.dll loads without libgcc_s/libstdc++/libwinpthread DLLs next to it.
            target_link_options(casc PRIVATE -static)
        endif()
        set_target_properties(casc PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
                                              LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")
        set(ISOMTOOL_BUILD_CASC_DLL ON)
    endif()
else()
    if(ISOMTOOL_CASCLIB_DLL)
        message(FATAL_ERROR "ISOMTOOL_CASCLIB_DLL needs the StormLib and CascLib source trees in external/")
    endif()
    message(STATUS "isomtool: using installed StormLib and CascLib")
    find_library(ISOMTOOL_STORMLIB_LIBRARY NAMES libstorm.a storm StormLib)
    find_library(ISOMTOOL_CASCLIB_LIBRARY NAMES libcasc.a casc CascLib)
    find_path(ISOMTOOL_ARCHIVE_INCLUDES NAMES StormLib.h)
    if(NOT ISOMTOOL_STORMLIB_LIBRARY OR NOT ISOMTOOL_CASCLIB_LIBRARY)
        message(FATAL_ERROR "StormLib/CascLib not found. Either install them (docs/bw-terrain-setup.md) or clone their "
                            "sources into ${CMAKE_CURRENT_SOURCE_DIR}/external/StormLib and .../CascLib.")
    endif()
    find_package(ZLIB REQUIRED)
    find_package(BZip2 REQUIRED)
    find_package(Threads REQUIRED)
    set(ISOMTOOL_ARCHIVE_LIBS ${ISOMTOOL_STORMLIB_LIBRARY} ${ISOMTOOL_CASCLIB_LIBRARY} BZip2::BZip2 ZLIB::ZLIB Threads::Threads)
    if(WIN32)
        list(APPEND ISOMTOOL_ARCHIVE_LIBS ws2_32 wininet)
    endif()
endif()

# ---- isomtool ----
file(GLOB MAPPING_CORE "${CD}/mapping_core/*.cpp")
list(FILTER MAPPING_CORE EXCLUDE REGEX "lite_")
add_executable(isomtool main.cpp ${MAPPING_CORE} "${CD}/cross_cut/logger.cpp" "${CD}/cross_cut/simple_icu.cpp")
target_include_directories(isomtool PRIVATE "${CD}" "${CD}/mapping_core" "${ISOMTOOL_RARECPP_DIR}/include"
                           ${ISOMTOOL_ARCHIVE_INCLUDES})
target_compile_definitions(isomtool PRIVATE NOMINMAX)
target_link_libraries(isomtool PRIVATE ${ISOMTOOL_ARCHIVE_LIBS})
if(ISOMTOOL_BUILD_CASC_DLL)
    add_dependencies(isomtool casc)
endif()

set(_icu "${ISOMTOOL_ICU}")
if(_icu STREQUAL "AUTO" OR _icu STREQUAL "SYSTEM")
    find_package(ICU COMPONENTS uc QUIET)
    if(ICU_FOUND)
        set(_icu SYSTEM)
    elseif(_icu STREQUAL "SYSTEM")
        message(FATAL_ERROR "ISOMTOOL_ICU=SYSTEM but ICU (icuuc) was not found")
    else()
        set(_icu BUNDLED)
    endif()
endif()
if(_icu STREQUAL "SYSTEM")
    target_link_libraries(isomtool PRIVATE ICU::uc)
else()
    # BEFORE: icu_min's unicode/*.h must win over any ICU headers on the include path.
    target_include_directories(isomtool BEFORE PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/icu_min")
    target_sources(isomtool PRIVATE icu_min/icu_min.c)
endif()
message(STATUS "isomtool: ICU = ${_icu}")

if(WIN32)
    # Chkdraft's system_io.cpp includes <Windows.h> and uses the common file dialogs, so do not define
    # WIN32_LEAN_AND_MEAN (it would drop commdlg.h). shell32 for CommandLineToArgvW in main.cpp.
    target_link_libraries(isomtool PRIVATE user32 comdlg32 shell32)
    if(MINGW)
        target_link_options(isomtool PRIVATE -static)   # no libstdc++/libgcc/winpthread DLLs next to the exe
    endif()
else()
    # Older Chkdraft revisions call GetLastError() outside their _WIN32 blocks; gle.h supplies a stub there.
    target_compile_options(isomtool PRIVATE "SHELL:-include ${CMAKE_CURRENT_SOURCE_DIR}/gle.h")
endif()

# Unit test for icu_min (ctest): known vectors, runs on every platform without ICU.
enable_testing()
add_executable(test_icu_min EXCLUDE_FROM_ALL icu_min/test_icu_min.c icu_min/icu_min.c)
target_include_directories(test_icu_min PRIVATE icu_min)
add_test(NAME icu_min COMMAND test_icu_min)
