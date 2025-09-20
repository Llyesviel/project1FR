from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from .models import (
    FacilityType,
    Facility,
    FacilityDocument,
    FacilityImage,
    MaintenanceSchedule
)


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'description',
        'icon',
        'facilities_count',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'icon', 'is_active')
        }),
        (_('Временные метки'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def facilities_count(self, obj):
        """Количество объектов данного типа"""
        count = obj.facilities.count()
        if count > 0:
            url = reverse('admin:facilities_facility_changelist')
            return format_html(
                '<a href="{}?facility_type__id__exact={}">{}</a>',
                url, obj.pk, count
            )
        return count
    facilities_count.short_description = _('Объектов')
    facilities_count.admin_order_field = 'facilities__count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            facilities_count=Count('facilities')
        )


class FacilityDocumentInline(admin.TabularInline):
    model = FacilityDocument
    extra = 0
    fields = [
        'name',
        'document_type',
        'file',
        'document_date',
        'expiry_date',
        'is_active'
    ]
    readonly_fields = ['uploaded_at', 'uploaded_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


class FacilityImageInline(admin.TabularInline):
    model = FacilityImage
    extra = 0
    fields = [
        'title',
        'image',
        'image_type',
        'is_primary',
        'order',
        'image_preview'
    ]
    readonly_fields = ['image_preview', 'uploaded_at', 'uploaded_by']
    
    def image_preview(self, obj):
        """Превью изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;"/>',
                obj.image.url
            )
        return _('Нет изображения')
    image_preview.short_description = _('Превью')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


class MaintenanceScheduleInline(admin.TabularInline):
    model = MaintenanceSchedule
    extra = 0
    fields = [
        'name',
        'frequency',
        'next_maintenance_date',
        'responsible_person',
        'status'
    ]
    readonly_fields = ['created_at', 'created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'facility_type',
        'project',
        'city',
        'status',
        'condition',
        'manager',
        'defects_info',
        'created_at'
    ]
    list_filter = [
        'status',
        'condition',
        'facility_type',
        'city',
        'project',
        'created_at'
    ]
    search_fields = [
        'name',
        'description',
        'address',
        'city',
        'region'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'created_at',
        'updated_at',
        'coordinates_display',
        'defects_summary'
    ]
    inlines = [
        FacilityImageInline,
        FacilityDocumentInline,
        MaintenanceScheduleInline
    ]
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'name',
                'description',
                'facility_type',
                'project',
                'manager'
            )
        }),
        (_('Адрес и местоположение'), {
            'fields': (
                'address',
                'city',
                'region',
                'postal_code',
                ('latitude', 'longitude'),
                'coordinates_display'
            )
        }),
        (_('Технические характеристики'), {
            'fields': (
                ('total_area', 'usable_area'),
                'floors_count',
                ('construction_year', 'renovation_year')
            )
        }),
        (_('Статус и состояние'), {
            'fields': (
                'status',
                'condition',
                'condition_notes'
            )
        }),
        (_('Финансовая информация'), {
            'fields': (
                'purchase_price',
                'current_value',
                'insurance_value'
            ),
            'classes': ('collapse',)
        }),
        (_('Дополнительные данные'), {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
        (_('Дефекты'), {
            'fields': ('defects_summary',),
            'classes': ('collapse',)
        }),
        (_('Временные метки'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def coordinates_display(self, obj):
        """Отображение координат"""
        if obj.coordinates:
            return f"Широта: {obj.latitude}, Долгота: {obj.longitude}"
        return _('Координаты не указаны')
    coordinates_display.short_description = _('Координаты')
    
    def defects_info(self, obj):
        """Информация о дефектах"""
        total = obj.get_defects_count()
        open_count = obj.get_open_defects_count()
        critical = obj.get_critical_defects_count()
        
        if total == 0:
            return format_html('<span style="color: green;">✓ Нет дефектов</span>')
        
        color = 'red' if critical > 0 else 'orange' if open_count > 0 else 'green'
        return format_html(
            '<span style="color: {};">{} всего / {} открытых / {} критических</span>',
            color, total, open_count, critical
        )
    defects_info.short_description = _('Дефекты')
    
    def defects_summary(self, obj):
        """Подробная сводка по дефектам"""
        if obj.pk:
            total = obj.get_defects_count()
            open_count = obj.get_open_defects_count()
            critical = obj.get_critical_defects_count()
            
            html = f"""
            <div style="padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                <h4>Статистика дефектов:</h4>
                <ul>
                    <li>Всего дефектов: <strong>{total}</strong></li>
                    <li>Открытых дефектов: <strong>{open_count}</strong></li>
                    <li>Критических дефектов: <strong style="color: red;">{critical}</strong></li>
                </ul>
            </div>
            """
            return mark_safe(html)
        return _('Сохраните объект для просмотра статистики дефектов')
    defects_summary.short_description = _('Сводка по дефектам')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'facility_type',
            'project',
            'manager',
            'created_by'
        ).prefetch_related('defects')


@admin.register(FacilityDocument)
class FacilityDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'facility',
        'document_type',
        'document_date',
        'expiry_date',
        'expiry_status',
        'file_info',
        'is_active',
        'uploaded_at'
    ]
    list_filter = [
        'document_type',
        'is_active',
        'document_date',
        'expiry_date',
        'uploaded_at'
    ]
    search_fields = [
        'name',
        'description',
        'facility__name'
    ]
    ordering = ['-uploaded_at']
    readonly_fields = [
        'uploaded_at',
        'uploaded_by',
        'file_info_detailed',
        'expiry_status'
    ]
    
    fieldsets = (
        (None, {
            'fields': (
                'facility',
                'name',
                'document_type',
                'description'
            )
        }),
        (_('Файл'), {
            'fields': (
                'file',
                'file_info_detailed'
            )
        }),
        (_('Даты'), {
            'fields': (
                'document_date',
                'expiry_date',
                'expiry_status'
            )
        }),
        (_('Статус'), {
            'fields': ('is_active',)
        }),
        (_('Информация о загрузке'), {
            'fields': ('uploaded_at', 'uploaded_by'),
            'classes': ('collapse',)
        })
    )
    
    def expiry_status(self, obj):
        """Статус истечения срока действия"""
        if not obj.expiry_date:
            return format_html('<span style="color: gray;">Без срока действия</span>')
        
        if obj.is_expired:
            return format_html('<span style="color: red;">⚠ Просрочен</span>')
        
        from django.utils import timezone
        from datetime import timedelta
        
        days_left = (obj.expiry_date - timezone.now().date()).days
        if days_left <= 30:
            return format_html(
                '<span style="color: orange;">⚠ Истекает через {} дней</span>',
                days_left
            )
        
        return format_html('<span style="color: green;">✓ Действителен</span>')
    expiry_status.short_description = _('Статус срока действия')
    
    def file_info(self, obj):
        """Краткая информация о файле"""
        if obj.file:
            size_mb = obj.file_size / (1024 * 1024) if obj.file_size else 0
            return f"{obj.file_extension.upper()} ({size_mb:.1f} MB)"
        return _('Нет файла')
    file_info.short_description = _('Файл')
    
    def file_info_detailed(self, obj):
        """Подробная информация о файле"""
        if obj.file:
            size_mb = obj.file_size / (1024 * 1024) if obj.file_size else 0
            html = f"""
            <div style="padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                <p><strong>Имя файла:</strong> {obj.file.name}</p>
                <p><strong>Размер:</strong> {size_mb:.2f} MB</p>
                <p><strong>Расширение:</strong> {obj.file_extension.upper()}</p>
                <p><a href="{obj.file.url}" target="_blank">Скачать файл</a></p>
            </div>
            """
            return mark_safe(html)
        return _('Файл не загружен')
    file_info_detailed.short_description = _('Информация о файле')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FacilityImage)
class FacilityImageAdmin(admin.ModelAdmin):
    list_display = [
        'title_or_default',
        'facility',
        'image_type',
        'is_primary',
        'order',
        'image_thumbnail',
        'uploaded_at'
    ]
    list_filter = [
        'image_type',
        'is_primary',
        'uploaded_at'
    ]
    search_fields = [
        'title',
        'description',
        'facility__name'
    ]
    ordering = ['facility', 'order', '-uploaded_at']
    readonly_fields = [
        'uploaded_at',
        'uploaded_by',
        'image_preview_large'
    ]
    
    fieldsets = (
        (None, {
            'fields': (
                'facility',
                'title',
                'image_type',
                'description'
            )
        }),
        (_('Изображение'), {
            'fields': (
                'image',
                'image_preview_large'
            )
        }),
        (_('Настройки'), {
            'fields': (
                'is_primary',
                'order'
            )
        }),
        (_('Информация о загрузке'), {
            'fields': ('uploaded_at', 'uploaded_by'),
            'classes': ('collapse',)
        })
    )
    
    def title_or_default(self, obj):
        """Заголовок или значение по умолчанию"""
        return obj.title or f"Изображение #{obj.pk}"
    title_or_default.short_description = _('Заголовок')
    
    def image_thumbnail(self, obj):
        """Миниатюра изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;"/>',
                obj.image.url
            )
        return _('Нет изображения')
    image_thumbnail.short_description = _('Миниатюра')
    
    def image_preview_large(self, obj):
        """Большое превью изображения"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px;"/>',
                obj.image.url
            )
        return _('Изображение не загружено')
    image_preview_large.short_description = _('Превью')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'facility',
        'frequency',
        'next_maintenance_date',
        'maintenance_status',
        'responsible_person',
        'status',
        'created_at'
    ]
    list_filter = [
        'frequency',
        'status',
        'next_maintenance_date',
        'created_at'
    ]
    search_fields = [
        'name',
        'description',
        'facility__name',
        'responsible_person__username',
        'responsible_person__first_name',
        'responsible_person__last_name'
    ]
    ordering = ['next_maintenance_date']
    readonly_fields = [
        'created_at',
        'updated_at',
        'created_by',
        'maintenance_status'
    ]
    
    fieldsets = (
        (None, {
            'fields': (
                'facility',
                'name',
                'description',
                'responsible_person'
            )
        }),
        (_('Расписание'), {
            'fields': (
                'frequency',
                'custom_frequency_days',
                'start_date',
                'end_date',
                'next_maintenance_date',
                'maintenance_status'
            )
        }),
        (_('Оценки'), {
            'fields': (
                'estimated_duration_hours',
                'estimated_cost'
            )
        }),
        (_('Статус и примечания'), {
            'fields': (
                'status',
                'notes'
            )
        }),
        (_('Временные метки'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def maintenance_status(self, obj):
        """Статус обслуживания"""
        if obj.status != 'active':
            return format_html(
                '<span style="color: gray;">{}</span>',
                obj.get_status_display()
            )
        
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠ Просрочено</span>')
        
        from django.utils import timezone
        from datetime import timedelta
        
        days_left = (obj.next_maintenance_date - timezone.now().date()).days
        if days_left <= 7:
            return format_html(
                '<span style="color: orange;">⚠ Через {} дней</span>',
                days_left
            )
        
        return format_html('<span style="color: green;">✓ По расписанию</span>')
    maintenance_status.short_description = _('Статус обслуживания')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'facility',
            'responsible_person',
            'created_by'
        )


# Настройка заголовков админки
admin.site.site_header = _('Система управления объектами недвижимости')
admin.site.site_title = _('Админ-панель')
admin.site.index_title = _('Добро пожаловать в админ-панель')