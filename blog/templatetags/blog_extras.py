from django import template

register = template.Library()


@register.filter
def signed_score(score):
    score = score or 0
    if score < 0:
        return f"−{abs(score)}"
    return f"+{score}"


@register.filter
def score_class(score):
    score = score or 0
    if score > 0:
        return "score--pos"
    if score < 0:
        return "score--neg"
    return "score--zero"
