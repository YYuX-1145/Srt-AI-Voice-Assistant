def register(context):
    globals().update(context)
    from .custom import Custom
    return Custom()
