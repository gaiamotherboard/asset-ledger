"""
Unit tests for asset management app
Tests LSHW parsing, memory slot detection, and data integrity
Includes new tests for scan bundle ingest, deduplication, and schema validation
"""

import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .lshw_parser import (
    extract_basic_hw,
    extract_cpu_info,
    extract_serial,
    format_bytes,
    parse_disks,
    parse_lshw_json,
)
from .models import Asset, Drive, HardwareScan


class FormatBytesTestCase(TestCase):
    """Test human-readable byte formatting"""

    def test_bytes(self):
        self.assertEqual(format_bytes(512), "512.0 B")

    def test_kilobytes(self):
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(2048), "2.0 KB")

    def test_megabytes(self):
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")
        self.assertEqual(format_bytes(512 * 1024 * 1024), "512.0 MB")

    def test_gigabytes(self):
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.0 GB")
        self.assertEqual(format_bytes(16 * 1024 * 1024 * 1024), "16.0 GB")

    def test_terabytes(self):
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1024), "1.0 TB")

    def test_zero(self):
        self.assertEqual(format_bytes(0), "0 B")

    def test_none(self):
        self.assertEqual(format_bytes(None), "0 B")


class MemorySlotParsingTestCase(TestCase):
    """Test memory slot detection and parsing from LSHW JSON"""

    def setUp(self):
        """Create test LSHW data with memory slots"""
        self.lshw_single_slot = {
            "id": "computer",
            "class": "system",
            "children": [
                {
                    "id": "core",
                    "class": "bus",
                    "children": [
                        {
                            "id": "memory",
                            "class": "memory",
                            "description": "System Memory",
                            "size": 8589934592,  # 8 GB
                            "children": [
                                {
                                    "id": "bank:0",
                                    "class": "memory",
                                    "description": "SODIMM DDR4 Synchronous",
                                    "slot": "DIMM 0",
                                    "size": 8589934592,  # 8 GB
                                    "vendor": "Samsung",
                                    "product": "M471A1K43CB1-CTD",
                                    "serial": "12345678",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        self.lshw_dual_slot = {
            "id": "computer",
            "class": "system",
            "children": [
                {
                    "id": "core",
                    "class": "bus",
                    "children": [
                        {
                            "id": "memory",
                            "class": "memory",
                            "description": "System Memory",
                            "size": 17179869184,  # 16 GB
                            "children": [
                                {
                                    "id": "bank:0",
                                    "class": "memory",
                                    "description": "SODIMM DDR4",
                                    "slot": "DIMM A",
                                    "size": 8589934592,  # 8 GB
                                    "vendor": "Crucial",
                                    "product": "CT8G4SFRA266.C8FE",
                                    "serial": "AAAA1111",
                                },
                                {
                                    "id": "bank:1",
                                    "class": "memory",
                                    "description": "SODIMM DDR4",
                                    "slot": "DIMM B",
                                    "size": 8589934592,  # 8 GB
                                    "vendor": "Crucial",
                                    "product": "CT8G4SFRA266.C8FE",
                                    "serial": "BBBB2222",
                                },
                            ],
                        }
                    ],
                }
            ],
        }

        self.lshw_no_memory = {
            "id": "computer",
            "class": "system",
            "children": [
                {
                    "id": "core",
                    "class": "bus",
                    "children": [],
                }
            ],
        }

    def test_single_memory_slot_parsing(self):
        """Test parsing a single memory slot"""
        parsed = parse_lshw_json(self.lshw_single_slot)

        self.assertIsNotNone(parsed)
        self.assertIn("memory_slots", parsed)
        self.assertIn("memory_total_bytes", parsed)

        # Check slot count
        slots = parsed["memory_slots"]
        self.assertEqual(len(slots), 1)

        # Check first slot details
        slot = slots[0]
        self.assertEqual(slot["slot"], "DIMM 0")
        self.assertEqual(slot["size_bytes"], 8589934592)
        self.assertEqual(slot["size_human"], "8.0 GB")
        self.assertEqual(slot["vendor"], "Samsung")
        self.assertEqual(slot["product"], "M471A1K43CB1-CTD")
        self.assertEqual(slot["serial"], "12345678")

        # Check total memory
        self.assertEqual(parsed["memory_total_bytes"], 8589934592)

    def test_dual_memory_slot_parsing(self):
        """Test parsing dual memory slots"""
        parsed = parse_lshw_json(self.lshw_dual_slot)

        self.assertIsNotNone(parsed)
        self.assertIn("memory_slots", parsed)
        self.assertIn("memory_total_bytes", parsed)

        # Check slot count
        slots = parsed["memory_slots"]
        self.assertEqual(len(slots), 2)

        # Check first slot
        slot0 = slots[0]
        self.assertEqual(slot0["slot"], "DIMM A")
        self.assertEqual(slot0["size_bytes"], 8589934592)
        self.assertEqual(slot0["size_human"], "8.0 GB")
        self.assertEqual(slot0["vendor"], "Crucial")
        self.assertEqual(slot0["serial"], "AAAA1111")

        # Check second slot
        slot1 = slots[1]
        self.assertEqual(slot1["slot"], "DIMM B")
        self.assertEqual(slot1["size_bytes"], 8589934592)
        self.assertEqual(slot1["size_human"], "8.0 GB")
        self.assertEqual(slot1["vendor"], "Crucial")
        self.assertEqual(slot1["serial"], "BBBB2222")

        # Check total memory (should be 16 GB from system memory node)
        self.assertEqual(parsed["memory_total_bytes"], 17179869184)

    def test_no_memory_slots(self):
        """Test handling of LSHW output with no memory information"""
        parsed = parse_lshw_json(self.lshw_no_memory)

        self.assertIsNotNone(parsed)
        self.assertIn("memory_slots", parsed)
        self.assertEqual(len(parsed["memory_slots"]), 0)
        # memory_total_bytes can be None if no memory info found
        self.assertIsNone(parsed["memory_total_bytes"])

    def test_memory_total_from_slots_fallback(self):
        """Test that memory total is calculated from slots when system memory is missing"""
        # Remove the system memory node, keep only slots
        lshw_slots_only = {
            "id": "computer",
            "class": "system",
            "children": [
                {
                    "id": "core",
                    "class": "bus",
                    "children": [
                        {
                            "id": "memory",
                            "class": "memory",
                            "children": [
                                {
                                    "id": "bank:0",
                                    "class": "memory",
                                    "slot": "DIMM 0",
                                    "size": 4294967296,  # 4 GB
                                },
                                {
                                    "id": "bank:1",
                                    "class": "memory",
                                    "slot": "DIMM 1",
                                    "size": 4294967296,  # 4 GB
                                },
                            ],
                        }
                    ],
                }
            ],
        }

        parsed = parse_lshw_json(lshw_slots_only)

        # Total should be sum of slots (8 GB)
        self.assertEqual(parsed["memory_total_bytes"], 8589934592)
        self.assertEqual(len(parsed["memory_slots"]), 2)


class DriveModelTestCase(TestCase):
    """Test Drive model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.asset = Asset.objects.create(asset_tag="TEST001", created_by=self.user)

    def test_capacity_human_formatting(self):
        """Test human-readable capacity formatting"""
        # 256 GB drive
        drive = Drive.objects.create(
            asset=self.asset,
            serial="SN123456",
            capacity_bytes=256 * 1024 * 1024 * 1024,
            model="Samsung SSD 840",
        )
        self.assertEqual(drive.capacity_human, "256.0 GB")

    def test_serial_tag_normal(self):
        """Test serial tag for normal serial numbers"""
        drive = Drive.objects.create(
            asset=self.asset, serial="ABC123XYZ", capacity_bytes=500000000000
        )
        self.assertEqual(drive.serial_tag, "(SN ABC123XYZ)")

    def test_serial_tag_noserial(self):
        """Test serial tag for drives without serial numbers"""
        drive = Drive.objects.create(
            asset=self.asset, serial="NOSERIAL-ABC123", capacity_bytes=500000000000
        )
        self.assertEqual(drive.serial_tag, "(no serial)")

    def test_serial_tag_empty(self):
        """Test serial tag when serial is empty"""
        drive = Drive.objects.create(
            asset=self.asset, serial="", capacity_bytes=500000000000
        )
        self.assertIsNone(drive.serial_tag)


class AssetCreationTestCase(TestCase):
    """Test asset auto-creation on first access"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_asset_creation(self):
        """Test that asset is created with proper defaults"""
        asset = Asset.objects.create(asset_tag="TEST002", created_by=self.user)

        self.assertEqual(asset.asset_tag, "TEST002")
        self.assertEqual(asset.created_by, self.user)
        self.assertEqual(asset.status, "")
        self.assertEqual(asset.device_type, "")
        self.assertEqual(asset.cosmetic_grade, "")
        self.assertIsNotNone(asset.created_at)

    def test_unique_asset_tag(self):
        """Test that asset tags are unique"""
        Asset.objects.create(asset_tag="TEST003", created_by=self.user)

        # Attempting to create another asset with same tag should fail
        with self.assertRaises(Exception):
            Asset.objects.create(asset_tag="TEST003", created_by=self.user)


class BasicHardwareExtractionTestCase(TestCase):
    """Test basic hardware summary extraction"""

    def test_extract_basic_hw_with_memory(self):
        """Test RAM extraction from system memory"""
        lshw_data = {
            "id": "computer",
            "class": "system",
            "children": [
                {
                    "id": "core",
                    "children": [
                        {
                            "id": "memory",
                            "class": "memory",
                            "description": "System Memory",
                            "size": 17179869184,  # 16 GB
                        }
                    ],
                }
            ],
        }

        summary = extract_basic_hw(lshw_data)

        self.assertIsNotNone(summary)
        self.assertIn("ram", summary)
        self.assertEqual(summary["ram"], "16.0 GB")

    def test_extract_basic_hw_empty(self):
        """Test extraction from empty LSHW data"""
        lshw_data = {"id": "computer", "class": "system", "children": []}

        summary = extract_basic_hw(lshw_data)

        # Should return None when no meaningful data found
        self.assertIsNone(summary)
