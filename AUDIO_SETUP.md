# Audio Device Setup Guide

This guide helps you configure audio devices for the STT-Vosk module, particularly for USB microphones on Linux systems.

## ALSA Configuration

### Option 1: Use the included `.asoundrc` file (Recommended)

The `.asoundrc` file in the project root configures ALSA to:
- Use your USB microphone (card 1) by default
- Suppress errors for non-existent audio devices
- Disable playback devices (not needed for speech recognition)

To use it, copy it to your home directory:

```bash
cp .asoundrc ~/.asoundrc
```

### Option 2: System-wide configuration

If you prefer system-wide configuration, you can use `/etc/asound.conf` instead:

```bash
sudo cp .asoundrc /etc/asound.conf
```

### Finding Your Audio Device

To find your USB microphone's card and device numbers:

```bash
# List all recording devices
arecord -l

# Example output:
# card 0: PCH [HDA Intel PCH], device 0: ALC295 Analog [ALC295 Analog]
# card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
```

In this example:
- Built-in mic is card 0, device 0
- USB mic is card 1, device 0

Update the `.asoundrc` file accordingly if your USB mic is on a different card number.

## Python Configuration Options

The module now supports several configuration options in your Viam config:

### Basic Configuration

```json
{
  "model_name": "vosk-model-small-en-us-0.15",
  "model_lang": "en-us",
  "disable_mic": false
}
```

### Advanced Audio Device Configuration

```json
{
  "model_name": "vosk-model-small-en-us-0.15",
  "model_lang": "en-us",
  "disable_mic": false,
  "mic_device_index": 1,
  "suppress_alsa_errors": true
}
```

### Optimized Configuration for Polling Scenarios

For applications that poll the sensor periodically (e.g., every 5-10 seconds) and need reliable detection:

```json
{
  "mic_device_index": 1,
  "suppress_alsa_errors": true,
  "listen_timeout": 5.0,
  "phrase_time_limit": 3.0,
  "energy_threshold": 300,
  "pause_threshold": 0.5
}
```

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | string | `"vosk-model-small-en-us-0.15"` | Name of the Vosk model to use |
| `model_lang` | string | `"en-us"` | Language code for the model |
| `disable_mic` | boolean | `false` | Set to true to disable microphone (useful for file-only processing) |
| `mic_device_name` | string | `""` | Name of the microphone device (e.g., "USB Audio Device") |
| `mic_device_index` | integer | `null` | PyAudio device index (takes precedence over `mic_device_name`) |
| `suppress_alsa_errors` | boolean | `true` | Suppress ALSA error messages during device initialization |
| `listen_timeout` | float | `null` | Maximum seconds to wait for speech to start (null = wait indefinitely) |
| `phrase_time_limit` | float | `null` | Maximum seconds to record after speech starts (null = no limit) |
| `energy_threshold` | integer | `null` | Microphone sensitivity (lower = more sensitive, null = auto-calibrated) |
| `pause_threshold` | float | `0.8` | Seconds of silence to consider phrase ended |

#### Timeout Parameter Tuning Guide

**`listen_timeout`** - How long to wait for speech to start:
- **Use case**: Prevents indefinite waiting when polling periodically
- **Recommended for polling**: 3-7 seconds (match or slightly less than your polling interval)
- **Example**: If polling every 7 seconds, use `5.0` to allow quick retry on next poll
- **Default behavior**: `null` (waits indefinitely until speech detected)

**`phrase_time_limit`** - Maximum recording duration after speech starts:
- **Use case**: Prevents overly long recordings and improves responsiveness
- **Recommended for short commands**: 2-5 seconds
- **Recommended for longer speech**: 10-15 seconds
- **Example**: For single word commands like "steve", use `3.0`
- **Default behavior**: `null` (records until pause detected)

**`energy_threshold`** - Speech detection sensitivity:
- **Use case**: Adjusts for quiet speech or noisy environments
- **Lower values (100-500)**: More sensitive, better for quiet speech, may have false positives
- **Higher values (1000-4000)**: Less sensitive, better for noisy environments, may miss quiet speech
- **Recommended starting point**: `300` for quiet environments, `800` for normal
- **Default behavior**: `null` (auto-calibrated during initialization based on ambient noise)

**`pause_threshold`** - Silence duration to end phrase:
- **Use case**: Faster phrase ending detection
- **Lower values (0.3-0.5)**: Faster response, may cut off slow speakers
- **Higher values (0.8-1.2)**: More tolerant of pauses, slower response
- **Recommended for commands**: `0.5` seconds
- **Recommended for natural speech**: `0.8` seconds (default)

#### Example Configurations by Use Case

**Fast polling for single word commands (every 5-7 seconds):**
```json
{
  "listen_timeout": 5.0,
  "phrase_time_limit": 3.0,
  "energy_threshold": 300,
  "pause_threshold": 0.5
}
```
This configuration will:
- Wait up to 5 seconds for speech to start
- Record up to 3 seconds after detection
- Be sensitive to quiet speech
- Quickly detect phrase endings

**Natural speech with moderate polling:**
```json
{
  "listen_timeout": 8.0,
  "phrase_time_limit": 10.0,
  "energy_threshold": 500,
  "pause_threshold": 0.8
}
```
This configuration will:
- Allow more time for speaker to begin
- Record longer phrases
- Balance sensitivity and noise rejection
- Use standard pause detection

**Continuous listening (no polling):**
```json
{
  "listen_timeout": null,
  "phrase_time_limit": null,
  "energy_threshold": null,
  "pause_threshold": 0.8
}
```
This uses library defaults for always-on listening.

### Finding Your Device Index

The module logs available microphones when it starts. Check your logs for:

```
Available microphones: ['HDA Intel PCH: ALC295 Analog (hw:0,0)', 'USB Audio Device: USB Audio (hw:1,0)']
```

The device index is the position in this list (0-based):
- Index 0: Built-in microphone
- Index 1: USB Audio Device

Then configure using the index:

```json
{
  "mic_device_index": 1,
  "suppress_alsa_errors": true
}
```

## Troubleshooting

### Speech detection issues

**Problem: Missing spoken words (like "steve" not always detected)**

Solutions:
1. Lower the `energy_threshold` (try 200-400 for quiet speech)
2. Increase `listen_timeout` to give more time for speech to start
3. Check microphone positioning and ambient noise levels
4. Enable debug logging to see energy levels: check logs for "Listening..." messages

**Problem: Polling takes too long / timeouts are slow**

Solutions:
1. Set `listen_timeout` to match or be slightly less than your polling interval
2. Reduce `phrase_time_limit` to 2-3 seconds for short commands
3. Lower `pause_threshold` to 0.4-0.5 for faster phrase ending detection

**Problem: False positives / detecting noise as speech**

Solutions:
1. Increase `energy_threshold` (try 800-1500 for noisy environments)
2. Re-run ambient noise calibration by restarting the module
3. Check for electrical interference near the microphone

**Problem: Speech gets cut off mid-word**

Solutions:
1. Increase `pause_threshold` to 1.0-1.2 seconds
2. Increase `phrase_time_limit` if recordings are timing out
3. Check that microphone volume is adequate

### "Unable to open slave" or "Unknown PCM" errors

These errors occur when ALSA tries to access non-existent audio device configurations. The `.asoundrc` file and `suppress_alsa_errors: true` configuration should eliminate these.

### Microphone not working after configuration

1. Test your USB mic with:
   ```bash
   arecord -D hw:1,0 -d 5 test.wav
   aplay test.wav
   ```

2. Check permissions:
   ```bash
   # Add your user to the audio group
   sudo usermod -aG audio $USER
   # Log out and back in for changes to take effect
   ```

3. Enable debug logging in your Viam config to see which device is being selected

### Still seeing ALSA errors in logs

If you still see ALSA errors despite the configuration:

1. Make sure the `.asoundrc` file is in your home directory
2. Set `suppress_alsa_errors: true` in your configuration
3. Verify your USB mic is plugged in and recognized by the system

### Using a different card number

If your USB mic is not on card 1, update the `.asoundrc` file:

```
# Change these values to match your device
ctl.!default {
    type hw
    card 2  # Change this to your card number
}

pcm.usb {
    type hw
    card 2  # Change this to your card number
    device 0
}
```

## Environment Variables

You can also suppress ALSA errors at the environment level:

```bash
# Add to your shell profile or systemd service
export PULSE_LATENCY_MSEC=60
export ALSA_CARD=1
```

## Docker/Container Usage

If running in a container, you'll need to:

1. Mount the audio device:
   ```bash
   docker run --device /dev/snd ...
   ```

2. Copy the `.asoundrc` file into the container
3. Ensure the container user is in the audio group

## Systemd Service Configuration

If running as a systemd service, add to your service file:

```ini
[Service]
Environment="ALSA_CARD=1"
SupplementaryGroups=audio
```

