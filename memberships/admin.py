from django.contrib import admin

from .models import MembershipPlan


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'visits_total', 'validity_days', 'price_list', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('sort_order', 'name')
    list_editable = ('is_active',)
    readonly_fields = (
        'name',
        'visits_total',
        'validity_days',
        'price_list',
        'sort_order',
        'notes',
    )
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False