# PyInstaller hook for numpy
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all numpy submodules
hiddenimports = collect_submodules('numpy')

# Collect numpy data files
datas = collect_data_files('numpy')

