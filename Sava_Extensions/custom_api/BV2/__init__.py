def register(context):    
    globals().update(context)
    from .bv2 import BV2
    return BV2()
