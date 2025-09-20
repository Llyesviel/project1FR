from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Project, ProjectMembership, Facility, FacilityDocument


class ProjectMembershipInline(admin.TabularInline):
    """Инлайн для участников проекта"""
    model = ProjectMembership
    extra = 0
    fields = ('user', 'role', 'is_active', 'joined_at')
    readonly_fields = ('joined_at',)
    autocomplete_fields = ('user',)


class FacilityInline(admin.TabularInline):
    """Инлайн для объектов проекта"""
    model = Facility
    extra = 0
    fields = ('code', 'name', 'type', 'status', 'progress', 'responsible_person')
    readonly_fields = ('code',)
    autocomplete_fields = ('responsible_person',)
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Админка для проектов"""
    
    list_display = (
        'code', 'name', 'status', 'priority', 'manager',
        'progress_bar', 'team_count', 'facilities_count',
        'start_date', 'end_date', 'is_overdue_display'
    )
    
    list_filter = (
        'status', 'priority', 'is_active',
        'created_at', 'start_date', 'end_date'
    )
    
    search_fields = (
        'name', 'code', 'description', 'client',
        'manager__first_name', 'manager__last_name',
        'manager__email'
    )
    
    autocomplete_fields = ('manager', 'created_by')
    
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'is_overdue',
        'duration_planned', 'duration_actual', 'team_count_display',
        'facilities_count_display', 'defects_count_display'
    )
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name', 'code', 'description', 'client'
            )
        }),
        ('Статус и приоритет', {
            'fields': (
                'status', 'priority', 'progress', 'is_active'
            )
        }),
        ('Управление', {
            'fields': (
                'manager', 'created_by'
            )
        }),
        ('Даты', {
            'fields': (
                'start_date', 'end_date',
                'actual_start_date', 'actual_end_date'
            )
        }),
        ('Местоположение', {
            'fields': (
                'location', 'coordinates_lat', 'coordinates_lng'
            ),
            'classes': ('collapse',)
        }),
        ('Финансы', {
            'fields': (
                'budget',
            ),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': (
                'team_count_display', 'facilities_count_display',
                'defects_count_display', 'duration_planned',
                'duration_actual', 'is_overdue'
            ),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': (
                'id', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ProjectMembershipInline, FacilityInline]
    
    actions = ['mark_as_active', 'mark_as_completed', 'mark_as_on_hold']
    
    def progress_bar(self, obj):
        """Отображение прогресса в виде прогресс-бара"""
        color = 'green' if obj.progress >= 80 else 'orange' if obj.progress >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">' +
            '<div style="width: {}px; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">{}</div>' +
            '</div>',
            obj.progress, color, f'{obj.progress}%'
        )
    progress_bar.short_description = 'Прогресс'
    
    def team_count(self, obj):
        """Количество участников команды"""
        return obj.get_team_count()
    team_count.short_description = 'Команда'
    
    def facilities_count(self, obj):
        """Количество объектов"""
        return obj.get_facilities_count()
    facilities_count.short_description = 'Объекты'
    
    def is_overdue_display(self, obj):
        """Отображение просрочки"""
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠ Просрочен</span>')
        return '✓'
    is_overdue_display.short_description = 'Статус сроков'
    
    def team_count_display(self, obj):
        """Количество участников для readonly поля"""
        return obj.get_team_count()
    team_count_display.short_description = 'Участников в команде'
    
    def facilities_count_display(self, obj):
        """Количество объектов для readonly поля"""
        return obj.get_facilities_count()
    facilities_count_display.short_description = 'Объектов в проекте'
    
    def defects_count_display(self, obj):
        """Количество дефектов для readonly поля"""
        return obj.get_defects_count()
    defects_count_display.short_description = 'Всего дефектов'
    
    def mark_as_active(self, request, queryset):
        """Отметить как активные"""
        queryset.update(status=Project.Status.ACTIVE)
        self.message_user(request, f'Отмечено как активные: {queryset.count()} проектов')
    mark_as_active.short_description = 'Отметить как активные'
    
    def mark_as_completed(self, request, queryset):
        """Отметить как завершенные"""
        queryset.update(status=Project.Status.COMPLETED, progress=100)
        self.message_user(request, f'Отмечено как завершенные: {queryset.count()} проектов')
    mark_as_completed.short_description = 'Отметить как завершенные'
    
    def mark_as_on_hold(self, request, queryset):
        """Отметить как приостановленные"""
        queryset.update(status=Project.Status.ON_HOLD)
        self.message_user(request, f'Отмечено как приостановленные: {queryset.count()} проектов')
    mark_as_on_hold.short_description = 'Приостановить'


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    """Админка для участия в проектах"""
    
    list_display = (
        'user', 'project', 'role', 'is_active',
        'joined_at', 'left_at'
    )
    
    list_filter = (
        'role', 'is_active', 'joined_at',
        'project__status', 'project__priority'
    )
    
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'project__name', 'project__code'
    )
    
    autocomplete_fields = ('user', 'project')
    
    readonly_fields = ('joined_at',)
    
    date_hierarchy = 'joined_at'


class FacilityDocumentInline(admin.TabularInline):
    """Инлайн для документов объекта"""
    model = FacilityDocument
    extra = 0
    fields = ('name', 'type', 'file', 'version', 'is_active')
    readonly_fields = ('uploaded_at',)


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """Админка для объектов"""
    
    list_display = (
        'code', 'name', 'project', 'type', 'status',
        'progress_bar', 'responsible_person', 'defects_count',
        'construction_end', 'is_overdue_display'
    )
    
    list_filter = (
        'type', 'status', 'is_active',
        'project__status', 'construction_start', 'construction_end'
    )
    
    search_fields = (
        'name', 'code', 'description',
        'project__name', 'project__code',
        'responsible_person__first_name',
        'responsible_person__last_name'
    )
    
    autocomplete_fields = ('project', 'responsible_person', 'created_by')
    
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'is_overdue',
        'construction_duration_planned', 'construction_duration_actual',
        'defects_count_display', 'open_defects_count_display'
    )
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'project', 'name', 'code', 'description'
            )
        }),
        ('Характеристики', {
            'fields': (
                'type', 'status', 'progress',
                'floor_count', 'area', 'volume'
            )
        }),
        ('Управление', {
            'fields': (
                'responsible_person', 'created_by', 'is_active'
            )
        }),
        ('Строительство', {
            'fields': (
                'construction_start', 'construction_end',
                'actual_completion'
            )
        }),
        ('Местоположение', {
            'fields': (
                'location', 'coordinates_lat', 'coordinates_lng'
            ),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': (
                'defects_count_display', 'open_defects_count_display',
                'construction_duration_planned', 'construction_duration_actual',
                'is_overdue'
            ),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': (
                'id', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [FacilityDocumentInline]
    
    actions = ['mark_as_completed', 'mark_as_in_construction', 'mark_as_testing']
    
    def progress_bar(self, obj):
        """Отображение прогресса в виде прогресс-бара"""
        color = 'green' if obj.progress >= 80 else 'orange' if obj.progress >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">' +
            '<div style="width: {}px; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">{}</div>' +
            '</div>',
            obj.progress, color, f'{obj.progress}%'
        )
    progress_bar.short_description = 'Прогресс'
    
    def defects_count(self, obj):
        """Количество дефектов"""
        count = obj.get_defects_count()
        open_count = obj.get_open_defects_count()
        if open_count > 0:
            return format_html(
                '<span style="color: red;">{}</span> (<span style="color: orange;">{} откр.</span>)',
                count, open_count
            )
        return count
    defects_count.short_description = 'Дефекты'
    
    def is_overdue_display(self, obj):
        """Отображение просрочки"""
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠ Просрочен</span>')
        return '✓'
    is_overdue_display.short_description = 'Статус сроков'
    
    def defects_count_display(self, obj):
        """Количество дефектов для readonly поля"""
        return obj.get_defects_count()
    defects_count_display.short_description = 'Всего дефектов'
    
    def open_defects_count_display(self, obj):
        """Количество открытых дефектов для readonly поля"""
        return obj.get_open_defects_count()
    open_defects_count_display.short_description = 'Открытых дефектов'
    
    def mark_as_completed(self, request, queryset):
        """Отметить как завершенные"""
        queryset.update(status=Facility.Status.COMPLETED, progress=100)
        self.message_user(request, f'Отмечено как завершенные: {queryset.count()} объектов')
    mark_as_completed.short_description = 'Отметить как завершенные'
    
    def mark_as_in_construction(self, request, queryset):
        """Отметить как строящиеся"""
        queryset.update(status=Facility.Status.CONSTRUCTION)
        self.message_user(request, f'Отмечено как строящиеся: {queryset.count()} объектов')
    mark_as_in_construction.short_description = 'Отметить как строящиеся'
    
    def mark_as_testing(self, request, queryset):
        """Отметить как тестируемые"""
        queryset.update(status=Facility.Status.TESTING)
        self.message_user(request, f'Отмечено как тестируемые: {queryset.count()} объектов')
    mark_as_testing.short_description = 'Отметить как тестируемые'


@admin.register(FacilityDocument)
class FacilityDocumentAdmin(admin.ModelAdmin):
    """Админка для документов объектов"""
    
    list_display = (
        'name', 'facility', 'type', 'version',
        'file_size_display', 'uploaded_by', 'uploaded_at', 'is_active'
    )
    
    list_filter = (
        'type', 'is_active', 'uploaded_at',
        'facility__project', 'facility__type'
    )
    
    search_fields = (
        'name', 'description',
        'facility__name', 'facility__code',
        'facility__project__name'
    )
    
    autocomplete_fields = ('facility', 'uploaded_by')
    
    readonly_fields = ('uploaded_at', 'file_size_display', 'file_extension_display')
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'facility', 'name', 'description', 'type'
            )
        }),
        ('Файл', {
            'fields': (
                'file', 'version', 'file_size_display', 'file_extension_display'
            )
        }),
        ('Управление', {
            'fields': (
                'uploaded_by', 'is_active'
            )
        }),
        ('Системная информация', {
            'fields': (
                'uploaded_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    def file_size_display(self, obj):
        """Отображение размера файла"""
        size = obj.get_file_size()
        if size:
            if size > 1024 * 1024:  # MB
                return f'{size / (1024 * 1024):.1f} МБ'
            elif size > 1024:  # KB
                return f'{size / 1024:.1f} КБ'
            else:
                return f'{size} байт'
        return '-'
    file_size_display.short_description = 'Размер файла'
    
    def file_extension_display(self, obj):
        """Отображение расширения файла"""
        ext = obj.get_file_extension()
        return ext.upper() if ext else '-'
    file_extension_display.short_description = 'Тип файла'


# Настройка заголовков админки
admin.site.site_header = 'Система управления объектами - Проекты'
admin.site.site_title = 'Проекты'
admin.site.index_title = 'Управление проектами и объектами'