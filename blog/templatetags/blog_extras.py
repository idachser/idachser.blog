from django import template

register = template.Library()


@register.filter
def signed_score(score):
    score = score or 0
    if score < 0:
        return f"−{abs(score)}"
    return f"+{score}"


@register.filter
def plain_score(score):
    score = score or 0
    if score < 0:
        return f"\u2212{abs(score)}"
    return str(score)


@register.filter
def score_class(score):
    score = score or 0
    if score > 0:
        return "score--pos"
    if score < 0:
        return "score--neg"
    return "score--zero"
