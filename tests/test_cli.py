from cockatiel_pet.app import main


def test_unsupported_platform_is_a_clear_message_without_stacktrace(monkeypatch,capsys):
    monkeypatch.setattr("sys.platform","linux")
    assert main([]) == 1
    assert "Windows 10/11 x64 only" in capsys.readouterr().err
