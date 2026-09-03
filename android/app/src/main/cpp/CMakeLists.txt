cmake_minimum_required(VERSION 3.4.1)

set(${CMAKE_C_FLAGS}, "${CMAKE_C_FLAGS}")

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=gnu++11 -Wall -Werror")

# Gradle stages the Makefile output here before this runs (see stageJniLibs in app/build.gradle),
# and packages the APK from the same directory. JNI_STAGE_DIR is passed in by Gradle; the fallback
# keeps a bare cmake invocation working.
if(NOT DEFINED JNI_STAGE_DIR)
	set(JNI_STAGE_DIR ${CMAKE_SOURCE_DIR}/../../../build/jniStage)
endif()
link_directories(${JNI_STAGE_DIR}/arm64-v8a)

add_library(main SHARED main.c)

target_include_directories(main PRIVATE
	${CMAKE_SOURCE_DIR}/code/OpenXR-SDK/include
	${CMAKE_SOURCE_DIR}/code/OpenXR-SDK/src/common
	${CMAKE_SOURCE_DIR}/code/SDL2/include
	${CMAKE_SOURCE_DIR}/code)

target_compile_definitions(main PRIVATE
	ARCH_STRING=android)

find_library(log-lib log)

target_link_libraries(main
	android
	ioquake3_opengl2
	SDL2
	openxr_loader
	${log-lib})
