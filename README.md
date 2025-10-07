# stt-vosk

A modular service that provides speech-to-text (STT) capabilities for machines running on the Viam platform.

This module implements the `listen` and `to_text` commands of the [speech service API (`viam-labs:service:speech`)](https://github.com/viam-labs/speech-service-api). Follow the documentation below to learn about how to use it with the Viam SDKs.

## Usage

To use this module, follow these instructions to [add a module from the Viam Registry](https://docs.viam.com/registry/configure/#add-a-modular-resource-from-the-viam-registry) and select the `viam-labs:speech:stt-vosk` model from the [`stt-vosk` module](https://app.viam.com/module/viam-labs/stt-vosk).

### Prerequisites

On Linux:

`build.sh` will automatically include the following system dependencies as part of the PyInstaller executable:

- `python3-pyaudio`
- `ffmpeg`
- `alsa-tools`
- `alsa-utils`
- `flac`

On MacOS, `build.sh` will include the following dependencies using [Homebrew](https://brew.sh):

``` bash
brew install portaudio
```

Before configuring your speech service, you must also [create a machine](https://docs.viam.com/fleet/machines/#add-a-new-machine).

## Config

### Viam Service Configuration

Navigate to the **Config** tab of your machine's page in [the Viam app](https://app.viam.com/).
Click on the **Services** subtab and click **Create service**.
Select the `speech` type, then select the `speech:stt-vosk` model.
Click **Add module**, then enter a name for your speech service and click **Create**.

On the new component panel, copy and paste the following attribute template into your service’s **Attributes** box:

```json
{
  "model_name": "vosk-model-small-en-us-0.15",
  "model_lang": "en-us",
  "mic_device_name": "default"
}
```

These are the default values for these fields, none are required to be set for this service.

### Attributes

The following attributes are available for the `viam-labs:speech:speechio` speech service:

| Name    | Type   | Inclusion    | Description |
| ------- | ------ | ------------ | ----------- |
| `model_name` | string | Optional |  The name of the pre-trained [Vosk model](https://alphacephei.com/vosk/models) to be used. Default: `"vosk-model-small-en-us-0.15"`.  |
| `model_lang` | string | Optional |  The spoken language for the model to process. Default: `"en-us"`. |
| `mic_device_name`  | string | Optional |  The name of the hardware device used for audio input if more than one is available. Default: `"default"`. |
| `disable_mic`  | boolean | Optional | If true, will not configure any listening capabilities. This must be set to true if you do not have a valid microphone attached to your system. Default: `false`. |

> [!NOTE]
> For more information, see [Configure a Machine](https://docs.viam.com/manage/configuration/).

## Contributing

This project was bootstrapped and it managed by [`uv`](https://docs.astral.sh/uv/). Follow the documentation for [installing uv](https://docs.astral.sh/uv/#installation) and then run the `sync` command in your local `git clone` of this project to get started:

```console
git clone https://github.com/viam-labs/stt-vosk && cd stt-vosk
uv sync
```

## License: Apache-2.0
