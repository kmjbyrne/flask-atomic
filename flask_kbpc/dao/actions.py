class ActionsModel:
    ED = dict(
        name='actions',
        key='actions',
        schema=False,
        items=[
            dict(name='Edit', key='edit'),
            dict(name='Delete', key='delete'),
        ]
    )
    PED = dict(
        name='actions',
        key='actions',
        schema=False,
        items=[
            dict(name='Edit', key='edit'),
            dict(name='Delete', key='delete'),
            dict(name='Publish', key='publish'),
        ]
    )
    VED = dict(
        name='actions',
        key='actions',
        schema=False,
        items=[
            dict(name='Edit', key='edit'),
            dict(name='View', key='view'),
            dict(name='Delete', key='delete'),
        ]
    )
