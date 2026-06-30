from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_workspace_contains_voice_chat_controls(client):
    response = client.get("/")

    assert response.status_code == 200

    page = response.get_data(as_text=True)

    assert 'id="voiceInputButton"' in page
    assert 'id="voiceOutputButton"' in page
    assert 'id="voiceStatus"' in page
    assert 'aria-label="Start voice input"' in page
    assert 'aria-label="Automatic read aloud is off"' in page


def test_voice_module_supports_input_output_and_read_buttons():
    voice_module = (
        PROJECT_ROOT
        / "static"
        / "js"
        / "voice.js"
    ).read_text(encoding="utf-8")

    assert "SpeechRecognition" in voice_module
    assert "speechSynthesis" in voice_module
    assert "attachReadAloudButton" in voice_module
    assert "speakAssistantResponse" in voice_module
    assert "aiStudioVoiceSettingsV1" in voice_module


def test_voice_module_is_initialized_by_app():
    app_module = (
        PROJECT_ROOT
        / "static"
        / "js"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert 'from "./voice.js"' in app_module
    assert "initializeVoiceChat();" in app_module
