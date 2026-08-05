from ai_image_studio.doctor import system_doctor


def test_doctor_reports_ready(tmp_path):
    report = system_doctor(str(tmp_path / "workspace"))
    assert report["ready"] is True
    assert report["ai_image_studio_version"] == "0.5.0"
    assert any(check["name"] == "Workspace escribible" and check["status"] == "PASS" for check in report["checks"])
