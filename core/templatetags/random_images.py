# core/templatetags/random_images.py
import random
import os
from django import template
from django.conf import settings

register = template.Library()

# List of available images
KUHES_IMAGES = [
    'aerial_view.jpg',
    'aerial_view_from_library_top.jpg',
    'best_aerial_view.jpg',
    'fine_uni_pastures.jpg',
    'library_interior_night_view.jpg',
    'students_passing_by.jpg',
    'uni_swimming_pool.jpg',
]

@register.simple_tag
def random_kuhes_image():
    """Return a random KUHeS image filename"""
    return random.choice(KUHES_IMAGES)

@register.simple_tag
def random_kuhes_image_url():
    """Return the full static URL for a random KUHeS image"""
    image = random.choice(KUHES_IMAGES)
    return f"{settings.STATIC_URL}core/images/{image}"

@register.simple_tag
def specific_kuhes_image(image_name):
    """Return a specific KUHeS image URL"""
    return f"{settings.STATIC_URL}core/images/{image_name}"