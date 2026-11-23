"""Tests for ONVIF WS-Discovery XML parsing, SOAP WS-Security digest, and Media Profiles parsing."""

from __future__ import annotations

from backend.services.onvif.connection import build_wsse_security_header
from backend.services.onvif.device_information import parse_device_information_xml
from backend.services.onvif.discovery import (
    build_ws_discovery_probe_xml,
    parse_ws_discovery_response,
)
from backend.services.onvif.media_profiles import parse_media_profiles_xml, parse_uri_from_xml


def test_onvif_ws_discovery_probe_and_response_parsing() -> None:
    probe_xml = build_ws_discovery_probe_xml()
    assert "NetworkVideoTransmitter" in probe_xml

    sample_probe_match = """<?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery">
      <SOAP-ENV:Body>
        <d:ProbeMatches>
          <d:ProbeMatch>
            <d:Types>dn:NetworkVideoTransmitter</d:Types>
            <d:Scopes>onvif://www.onvif.org/name/IPC-2122 onvif://www.onvif.org/manufacturer/Uniview</d:Scopes>
            <d:XAddrs>http://192.168.1.88:8080/onvif/device_service</d:XAddrs>
          </d:ProbeMatch>
        </d:ProbeMatches>
      </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    """
    parsed = parse_ws_discovery_response(sample_probe_match, "192.168.1.88")
    assert parsed is not None
    assert parsed["ip_address"] == "192.168.1.88"
    assert parsed["onvif_port"] == 8080
    assert parsed["manufacturer"] == "Uniview"
    assert parsed["model"] == "IPC-2122"


def test_onvif_soap_device_info_and_profiles_parsing() -> None:
    wsse = build_wsse_security_header("admin", "password123")
    assert "PasswordDigest" in wsse
    assert "Nonce" in wsse

    dev_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
      <s:Body>
        <tds:GetDeviceInformationResponse>
          <tds:Manufacturer>Axis Communications</tds:Manufacturer>
          <tds:Model>AXIS M3065-V</tds:Model>
          <tds:FirmwareVersion>10.12.1</tds:FirmwareVersion>
          <tds:SerialNumber>ACCC8E123456</tds:SerialNumber>
          <tds:HardwareId>750</tds:HardwareId>
        </tds:GetDeviceInformationResponse>
      </s:Body>
    </s:Envelope>"""
    dev_info = parse_device_information_xml(dev_xml)
    assert dev_info["manufacturer"] == "Axis Communications"
    assert dev_info["model"] == "AXIS M3065-V"
    assert dev_info["serial_number"] == "ACCC8E123456"

    prof_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
                xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
                xmlns:tt="http://www.onvif.org/ver10/schema">
      <s:Body>
        <trt:GetProfilesResponse>
          <trt:Profiles token="Profile_1">
            <tt:Name>mainStream</tt:Name>
            <tt:VideoEncoderConfiguration>
              <tt:Encoding>H264</tt:Encoding>
              <tt:Resolution><tt:Width>1920</tt:Width><tt:Height>1080</tt:Height></tt:Resolution>
            </tt:VideoEncoderConfiguration>
          </trt:Profiles>
        </trt:GetProfilesResponse>
      </s:Body>
    </s:Envelope>"""
    profiles = parse_media_profiles_xml(prof_xml)
    assert len(profiles) == 1
    assert profiles[0]["token"] == "Profile_1"
    assert profiles[0]["resolution"] == "1920x1080"

    uri_xml = "<Envelope><Body><GetStreamUriResponse><MediaUri><Uri>rtsp://192.168.1.88:554/live</Uri></MediaUri></GetStreamUriResponse></Body></Envelope>"
    assert parse_uri_from_xml(uri_xml) == "rtsp://192.168.1.88:554/live"

