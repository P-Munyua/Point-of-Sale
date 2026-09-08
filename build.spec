# build.spec
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\Admin\\minimart_pos'],
    binaries=[],
    datas=[
        ('minimart_pos\\templates\\*', 'minimart_pos\\templates'),
        ('minimart_pos\\*.py', 'minimart_pos'),
        ('manage.py', '.'),
        ('pos\\migrations\\*', 'pos\\migrations'),
        ('pos\\*.py', 'pos'),
        ('proache\\*.py', 'proache'),
    ],
    hiddenimports=[
        'django.contrib.staticfiles',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'waitress',
        'pos',
        'proache',
        'custom_filters',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Minimart_POS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False if you don't want console window
    icon='pos_icon.ico'  # Optional: add if you have an icon file
)