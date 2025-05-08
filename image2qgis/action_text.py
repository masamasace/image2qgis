from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
from qgis.PyQt.QtGui import QDesktopServices
from pathlib import Path

def create_popup(
    file_name,      # gpkg の file_name
    file_path,      # gpkg の file_path
    thumb_path,     # gpkg の new_file_path
    latitude,       # gpkg の latitude
    longitude,      # gpkg の longitude
    datetime_value  # gpkg の datetime
):
    dialog = QDialog()
    dialog.setWindowTitle("画像情報" + " - " + file_name)
    dialog.setMinimumWidth(400)
    dialog.setMinimumHeight(300)

    layout = QVBoxLayout()
    text_browser = QTextBrowser()
    
    # 絶対パスの取得
    file_path = Path(file_path).resolve()
    thumb_path = Path(thumb_path).resolve()
    
    # file uri 形式に変換
    file_path = file_path.as_uri()
    thumb_path = thumb_path.as_uri()
    
    # 数値化できなければ 0.0
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        lat = lon = 0.0

    # datetime が空なら「不明」
    dt_disp = datetime_value or "不明"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <table>
            <tr>
                <th>画像名</th>
                <td><a href="{file_path} title="画像を開く">{file_name}</a></td>
            </tr>
            <tr>
                <th>緯度経度</th>
                <td>
                  <a href="https://www.google.com/maps/search/?api=1&query={lat},{lon}" target="_blank">
                    {lat:.6f}, {lon:.6f}
                  </a>
                </td>
            </tr>
            <tr>
                <th>撮影日時</th>
                <td>{dt_disp}</td>
            </tr>
            <tr>
                <td colspan="2" style="text-align: center; font-weight: bold;">サムネイル</td>
            </tr>
            <tr>
                <td colspan="2">
                    <a href="{file_path}">
                        <img src="{thumb_path}" width="300";">
                    </a>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    def handle_link_clicked(url):
        # リンクがクリックされたときの処理
        if url.scheme() == 'file':
            # ファイルを開く処理
            file_path = url.toLocalFile()
            if Path(file_path).exists():
                QDesktopServices.openUrl(url)  # デフォルトのアプリケーションで開く
                pass
            else:
                print(f"File not found: {file_path}")
        elif url.scheme() == 'http' or url.scheme() == 'https':
            # ウェブリンクを開く処理
            import webbrowser
            webbrowser.open(url.toString()) 
    
    text_browser.setOpenLinks(False)
    text_browser.setHtml(html_content)
    text_browser.anchorClicked.connect(handle_link_clicked)  # リンククリック時の処理を接続
    layout.addWidget(text_browser)
    dialog.setLayout(layout)
    dialog.exec()

create_popup(
      '[% "file_name" %]', r'[% "file_path" %]', r'[% "new_file_path" %]',
      '[% "latitude" %]', '[% "longitude" %]', '[% "datetime" %]'
    )