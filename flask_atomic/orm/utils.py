def check_inputs(cls, field, value):
    if isinstance(field, str):
        key_name = field
    else:
        key_name = field.name

    instrument = getattr(cls, field)
    if instrument.key not in cls.__dict__.keys() or key_name is None:
        raise ValueError('Invalid input field')
    instrument_key = instrument.key
    return {instrument_key: value}
