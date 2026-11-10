"""Package the saved dashboard for local opening; no network or recalculation. MPL-2.0."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parent.parent

def main():
    files={
        'index.html':(ROOT/'docs/preview.html').read_bytes(),
        'validation-preview.html':(ROOT/'docs/validation-preview.html').read_bytes(),
        'LIVE_PIPELINE_ACCEPTANCE.md':(ROOT/'docs/LIVE_PIPELINE_ACCEPTANCE.md').read_bytes(),
        'README.txt':('\ufeff8zz 可核對戰績看板\r\n\r\n'
            '1. 先將 8zz-dashboard-preview.zip 下載到電腦。\r\n'
            '2. Windows：右鍵 ZIP → 解壓縮全部。\r\n'
            '3. 在解壓縮後的資料夾，雙擊 index.html，以 Chrome 或 Edge 開啟。\r\n'
            '請勿開啟為原始碼、另存成 .txt，或只在 GitHub 原始檔頁面閱讀。\r\n\r\n'
            '資料、樣式與程式均已內嵌；不需安裝，不需啟動伺服器。\r\n'
            'index.html 為257個保存事件的部分資料績效；validation-preview.html 全為模擬驗收資料。計算、Telegram操作與限制見 LIVE_PIPELINE_ACCEPTANCE.md。\r\n'
            '© hansai-art / Group.G | Mozilla Public License 2.0\r\n').encode('utf-8'),
        'DASHBOARD_AUDIT.md':(ROOT/'docs/DASHBOARD_AUDIT.md').read_bytes(),
    }
    with ZipFile(ROOT/'docs/8zz-dashboard-preview.zip','w') as z:
        for name,data in files.items():
            info=ZipInfo(name,date_time=(2026,11,7,0,0,0));info.compress_type=ZIP_DEFLATED
            z.writestr(info,data)
    print('Packaged docs/8zz-dashboard-preview.zip; saved data unchanged.')
if __name__=='__main__':main()
