from .models import ScrollBanner

def scroll_banner(request):
    """
    Returns the highest priority active scroll banner.
    """
    banner = ScrollBanner.objects.filter(is_active=True, is_deleted=False).order_by('-priority').first()
    return {'global_scroll_banner': banner}
