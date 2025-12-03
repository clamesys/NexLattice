# NexLattice Platform Compatibility Matrix
**Generated:** Platform Compatibility Analysis

| Platform | Status | Compatibility | Notes |
|----------|--------|---------------|-------|
| ESP32 (WROOM-32, WROVER) | tested | ✅ Fully Compatible | All features supported |
| Raspberry Pi Pico W | compatible | ✅ Fully Compatible | All features supported |
| STM32 with WiFi (e.g., STM32F4 with ESP8266/ESP32) | compatible | ✅ Fully Compatible | All features supported |
| ESP8266 | compatible_with_fallback | ⚠️ Compatible (Fallbacks) | Uses fallback encryption |


## Detailed Analysis

### Dependencies Required

All platforms require MicroPython with the following modules:

- `network` - WiFi connectivity
- `socket` - UDP/TCP communication
- `uhashlib` - Cryptographic hashing
- `ubinascii` - Binary/hex encoding
- `urandom` - Random number generation
- `_thread` - Threading support
- `ucryptolib` - AES encryption (optional, fallback available)

### Platform-Specific Notes

#### ESP32 (WROOM-32, WROVER)

- **Status**: tested
- **Compatibility**: ✅ Compatible

#### Raspberry Pi Pico W

- **Status**: compatible
- **Compatibility**: ✅ Compatible

#### STM32 with WiFi (e.g., STM32F4 with ESP8266/ESP32)

- **Status**: compatible
- **Compatibility**: ✅ Compatible

#### ESP8266

- **Status**: compatible_with_fallback
- **Compatibility**: ✅ Compatible
- **Warnings**: [WARN] ucryptolib not available on ESP8266 (fallback encryption will be used)

