"""
Django Admin Configuration for Asset Management
This gives you a powerful web interface to manage all data
Access at: http://localhost:8000/admin/
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Asset, AssetTouch, Drive, HardwareScan


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    Asset admin interface - manage all assets
    """

    list_display = [
        "asset_tag",
        "status",
        "device_type",
        "cosmetic_grade",
        "location",
        "created_by",
        "created_at",
    ]
    list_filter = ["status", "device_type", "cosmetic_grade", "created_at"]
    search_fields = ["asset_tag", "location", "cosmetic_notes"]
    readonly_fields = ["created_at", "created_by"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "asset_tag",
                    "created_by",
                    "created_at",
                )
            },
        ),
        (
            "Intake Information",
            {
                "fields": (
                    "status",
                    "device_type",
                    "cosmetic_grade",
                    "cosmetic_notes",
                    "location",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Auto-set created_by on new assets"""
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class DriveInline(admin.TabularInline):
    """
    Show drives inline within the HardwareScan admin
    """

    model = Drive
    extra = 0
    readonly_fields = ["serial", "logicalname", "capacity_bytes", "model", "source"]
    can_delete = False


@admin.register(HardwareScan)
class HardwareScanAdmin(admin.ModelAdmin):
    """
    Hardware scan admin interface
    """

    list_display = [
        "asset",
        "device_serial",
        "scanned_at",
        "scanned_by",
        "drive_count",
    ]
    list_filter = ["scanned_at", "scanned_by"]
    search_fields = ["asset__asset_tag", "device_serial"]
    readonly_fields = [
        "asset",
        "device_serial",
        "scanned_at",
        "scanned_by",
        "raw_json",
        "summary",
    ]
    ordering = ["-scanned_at"]

    fieldsets = (
        (
            "Scan Information",
            {
                "fields": (
                    "asset",
                    "device_serial",
                    "scanned_by",
                    "scanned_at",
                    "user_notes",
                )
            },
        ),
        (
            "Hardware Data",
            {
                "fields": ("summary", "raw_json"),
                "classes": ["collapse"],
            },
        ),
    )

    def drive_count(self, obj):
        """Show number of drives found in scan"""
        return obj.asset.drives.count()

    drive_count.short_description = "Drives"


@admin.register(Drive)
class DriveAdmin(admin.ModelAdmin):
    """
    Drive admin interface - manage all drives
    """

    list_display = [
        "serial",
        "asset",
        "model",
        "capacity_display",
        "status",
        "status_by",
        "status_at",
    ]
    list_filter = ["status", "source", "status_at"]
    search_fields = ["serial", "model", "asset__asset_tag"]
    readonly_fields = ["status_at"]
    ordering = ["-status_at"]

    fieldsets = (
        (
            "Drive Information",
            {
                "fields": (
                    "asset",
                    "serial",
                    "logicalname",
                    "capacity_bytes",
                    "model",
                    "source",
                )
            },
        ),
        (
            "Status Tracking",
            {
                "fields": (
                    "status",
                    "status_note",
                    "status_by",
                    "status_at",
                )
            },
        ),
    )

    def capacity_display(self, obj):
        """Show human-readable capacity"""
        if obj.capacity_bytes:
            return obj.capacity_human
        return "-"

    capacity_display.short_description = "Capacity"


@admin.register(AssetTouch)
class AssetTouchAdmin(admin.ModelAdmin):
    """
    Asset touch (audit trail) admin interface
    Shows complete history of all asset interactions
    """

    list_display = [
        "asset",
        "touch_type",
        "touched_by",
        "touched_at",
        "details_preview",
    ]
    list_filter = ["touch_type", "touched_at", "touched_by"]
    search_fields = ["asset__asset_tag", "touched_by__username"]
    readonly_fields = ["asset", "touch_type", "touched_by", "touched_at", "details"]
    ordering = ["-touched_at"]

    fieldsets = (
        (
            "Touch Information",
            {
                "fields": (
                    "asset",
                    "touch_type",
                    "touched_by",
                    "touched_at",
                )
            },
        ),
        (
            "Details",
            {
                "fields": ("details",),
            },
        ),
    )

    def details_preview(self, obj):
        """Show preview of details JSON"""
        if obj.details:
            preview = str(obj.details)[:50]
            if len(str(obj.details)) > 50:
                preview += "..."
            return preview
        return "-"

    details_preview.short_description = "Details"

    def has_add_permission(self, request):
        """Don't allow manual creation of touches"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of audit trail"""
        return False
