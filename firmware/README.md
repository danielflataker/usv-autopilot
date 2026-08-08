# Firmware

The autopilot firmware targets the **NUCLEO-H533RE**.

## Development tools

- STM32CubeMX for MCU and peripheral configuration
- STM32CubeIDE for Visual Studio Code by STMicroelectronics
- CMake
- GCC Arm toolchain

The STM32CubeMX project is stored in
`usv_autopilot/usv_autopilot.ioc`.

Peripheral and clock changes should be made in CubeMX and the generated
code regenerated from there. Review the resulting Git diff before committing.

## Project configuration

The initial project was generated with:

- STM32CubeMX 6.18.1
- STM32CubeH5 V1.7.0
- CMake project generation
- GCC compiler
- TrustZone disabled
