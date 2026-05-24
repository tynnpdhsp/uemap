from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import config_service

pytestmark = pytest.mark.unit

ADMIN_ID = ObjectId()
IP = "127.0.0.1"


@pytest.mark.asyncio
async def test_get_map_config_empty(mock_db):
    result = await config_service.get_map_config()
    assert result == {}


@pytest.mark.asyncio
async def test_get_map_config_existing(mock_db):
    await mock_db["app_config"].insert_one({
        "_id": "map",
        "default_center": {"lat": 10.76, "lng": 106.68},
        "default_zoom": 15,
    })
    result = await config_service.get_map_config()
    assert result["default_center"]["lat"] == 10.76
    assert result["default_zoom"] == 15
    assert "_id" not in result


@pytest.mark.asyncio
async def test_update_map_config_center(mock_db):
    await mock_db["app_config"].insert_one({"_id": "map", "default_zoom": 15})
    result = await config_service.update_map_config(
        {"default_center": {"lat": 10.77, "lng": 106.69}}, ADMIN_ID, IP,
    )
    assert result["default_center"]["lat"] == 10.77

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "CONFIG_MAP_UPDATE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_update_map_config_zoom(mock_db):
    await mock_db["app_config"].insert_one({"_id": "map", "default_zoom": 15})
    result = await config_service.update_map_config({"default_zoom": 18}, ADMIN_ID, IP)
    assert result["default_zoom"] == 18


@pytest.mark.asyncio
async def test_update_map_config_geofence_rectangle(mock_db):
    await mock_db["app_config"].insert_one({"_id": "map"})
    geofence = {
        "type": "rectangle",
        "bounds": {"sw": {"lat": 10.0, "lng": 106.0}, "ne": {"lat": 11.0, "lng": 107.0}},
    }
    result = await config_service.update_map_config({"geofence": geofence}, ADMIN_ID, IP)
    assert result["geofence"]["type"] == "rectangle"


@pytest.mark.asyncio
async def test_update_map_config_geofence_radius_missing_center(mock_db):
    await mock_db["app_config"].insert_one({"_id": "map"})
    with pytest.raises(HTTPException) as exc:
        await config_service.update_map_config(
            {"geofence": {"type": "radius"}}, ADMIN_ID, IP,
        )
    assert exc.value.detail["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_update_map_config_geofence_radius_valid(mock_db):
    await mock_db["app_config"].insert_one({"_id": "map"})
    geofence = {
        "type": "radius",
        "center": {"lat": 10.76, "lng": 106.68},
        "radius_meters": 5000,
    }
    result = await config_service.update_map_config({"geofence": geofence}, ADMIN_ID, IP)
    assert result["geofence"]["type"] == "radius"
    assert result["geofence"]["radius_meters"] == 5000


@pytest.mark.asyncio
async def test_get_email_templates_empty(mock_db):
    result = await config_service.get_email_templates()
    assert result == {}


@pytest.mark.asyncio
async def test_get_email_templates_existing(mock_db):
    await mock_db["app_config"].insert_one({
        "_id": "email_templates",
        "activation": {"subject": "Test", "html_body": "<p>{full_name} {otp_code}</p>", "text_body": "{full_name} {otp_code}"},
    })
    result = await config_service.get_email_templates()
    assert result["activation"]["subject"] == "Test"
    assert "_id" not in result


@pytest.mark.asyncio
async def test_update_email_templates_success(mock_db):
    await mock_db["app_config"].insert_one({"_id": "email_templates"})
    tpl = {
        "activation": {
            "subject": "Kích hoạt",
            "html_body": "<p>Xin chào {full_name}, mã: {otp_code}</p>",
            "text_body": "Xin chào {full_name}, mã: {otp_code}",
        },
    }
    result = await config_service.update_email_templates(tpl, ADMIN_ID, IP)
    assert result["activation"]["subject"] == "Kích hoạt"

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "CONFIG_EMAIL_UPDATE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_update_email_templates_missing_placeholder(mock_db):
    await mock_db["app_config"].insert_one({"_id": "email_templates"})
    tpl = {
        "activation": {
            "subject": "Test",
            "html_body": "<p>Không có placeholder</p>",
            "text_body": "Không có",
        },
    }
    with pytest.raises(HTTPException) as exc:
        await config_service.update_email_templates(tpl, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_update_email_templates_partial_update(mock_db):
    await mock_db["app_config"].insert_one({
        "_id": "email_templates",
        "activation": {"subject": "Old", "html_body": "{full_name} {otp_code}", "text_body": "old"},
    })
    tpl = {
        "password_reset": {
            "subject": "Reset",
            "html_body": "<p>Xin chào {full_name}, mã: {otp_code}</p>",
            "text_body": "Xin chào {full_name}, mã: {otp_code}",
        },
    }
    result = await config_service.update_email_templates(tpl, ADMIN_ID, IP)
    assert result["password_reset"]["subject"] == "Reset"
    assert result["activation"]["subject"] == "Old"


@pytest.mark.asyncio
async def test_test_email_dev_mode(mock_db):
    await mock_db["app_config"].insert_one({
        "_id": "email_templates",
        "activation": {"subject": "Test", "html_body": "{full_name} {otp_code}", "text_body": "{full_name} {otp_code}"},
    })
    with patch.object(config_service.settings, "ENV", "dev"), \
         patch.object(config_service.settings, "SMTP_USER", ""), \
         patch.object(config_service.settings, "SMTP_PASSWORD", ""):
        result = await config_service.test_email("test@test.vn", "activation", ADMIN_ID, IP)
    assert result["smtp_success"] is True
    assert "DEV MODE" in result["message"]

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "CONFIG_EMAIL_TEST"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_test_email_smtp_failure(mock_db):
    await mock_db["app_config"].insert_one({
        "_id": "email_templates",
        "activation": {"subject": "Test", "html_body": "{full_name} {otp_code}", "text_body": "{full_name} {otp_code}"},
    })
    with patch.object(config_service.settings, "ENV", "production"), \
         patch("app.services.config_service.aiosmtplib.send", AsyncMock(side_effect=Exception("Connection refused"))):
        result = await config_service.test_email("test@test.vn", "activation", ADMIN_ID, IP)
    assert result["smtp_success"] is False
    assert "Connection refused" in result["message"]
