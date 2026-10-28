from django import template

register = template.Library()


@register.filter
def peso(amount):
    """40000 -> '₱40,000'. Empty stays empty."""
    if amount is None or amount == '':
        return ''
    return f'₱{amount:,.0f}'


@register.filter
def stars(rating):
    """3.6 -> [True, True, True, True, False]: which of the 5 stars are filled."""
    filled = round(rating or 0)
    return [number <= filled for number in range(1, 6)]


@register.filter
def km(distance):
    """12.3 -> '12.3 km'. Empty stays empty."""
    if distance is None or distance == '':
        return ''
    return f'{distance} km'
