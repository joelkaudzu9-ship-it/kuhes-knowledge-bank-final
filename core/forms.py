from django import forms
from .models import Resource, User
from .models import ResourceRequest


class ResourceUploadForm(forms.ModelForm):
    video_link = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://www.youtube.com/watch?v=...'
    }))

    class Meta:
        model = Resource
        fields = [
            'title', 'description', 'resource_type',
            'level', 'premed_subject', 'school', 'programme',
            'year_of_study', 'semester', 'lecturer', 'course_code',
            'academic_year', 'tags', 'file', 'video_link'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'resource_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_resource_type'}),
            'level': forms.Select(attrs={'class': 'form-control', 'id': 'id_level'}),
            'premed_subject': forms.Select(attrs={'class': 'form-control', 'id': 'id_premed_subject'}),
            'school': forms.Select(attrs={'class': 'form-control', 'id': 'id_school'}),
            'programme': forms.TextInput(attrs={'class': 'form-control'}),
            'year_of_study': forms.NumberInput(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control', 'id': 'id_semester'},
                                     choices=[('', 'Select...'), (1, 'Semester 1'), (2, 'Semester 2')]),
            'lecturer': forms.TextInput(attrs={'class': 'form-control'}),
            'course_code': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., biology, cells, mitosis'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'id': 'id_file'}),
        }


class ResourceRequestForm(forms.ModelForm):
    class Meta:
        model = ResourceRequest
        fields = [
            'title', 'description', 'level', 'premed_subject',
            'school', 'programme', 'year_of_study', 'course_code',
            'urgency', 'deadline'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MBBS Year 2 Pathology Past Papers 2023'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe exactly what you need...'}),
            'level': forms.Select(attrs={'class': 'form-control', 'id': 'req_level'}),
            'premed_subject': forms.Select(attrs={'class': 'form-control', 'id': 'req_premed_subject'}),
            'school': forms.Select(attrs={'class': 'form-control', 'id': 'req_school'}),
            'programme': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MBBS, BNS'}),
            'year_of_study': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'course_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., PRE101'}),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }