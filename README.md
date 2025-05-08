# image2qgis

位置情報付き画像ファイルをQGISで表示・管理するためのPythonツール

## 概要

`image2qgis`は、位置情報（ジオタグ）が付加された画像ファイルを処理し、QGIS上で効率的に表示・管理するためのツールです。画像ファイルから位置情報や撮影日時を抽出し、GeoPackageファイルを生成します。QGISでは、各画像の位置をポイントデータとして表示し、画像のプレビューやメタ情報の閲覧が可能です。最終的にはGoogle MyMapsのような地図上のアイコンとポップアップで画像情報を表示することができます。

## 主な機能

1. **画像ファイルの処理**
   - 対応フォーマット: JPG, JPEG, PNG, TIF, TIFF, HEIC
   - 位置情報（緯度・経度）の抽出
   - 撮影日時の取得
   - サムネイル画像の生成（JPEG形式、最大サイズ1280px）

2. **データ管理**
   - GeoPackageファイルの生成
   - GeoJSONファイルの生成
   - 位置情報が存在しない画像の除外オプション

3. **QGIS上での表示機能**
   - 画像位置のポイント表示
   - ポップアップダイアログによる画像情報の表示
     - 画像名（クリックで元画像を開く）
     - 位置情報（クリックでGoogle Mapsを開く）
     - 撮影日時
     - サムネイル画像（クリックで元画像を開く）

## 使用方法

1. ImageToQGISクラスのインスタンスを作成
```python
from image2qgis import ImageToQGIS

# 入力ディレクトリと出力ディレクトリを指定
img2gis = ImageToQGIS(input_dir="画像フォルダのパス", output_dir="出力先フォルダのパス")
```

2. 画像の処理
```python
# JPEG形式への変換とサムネイル生成
img2gis.convert_to_jpeg()

# 位置情報の取得
img2gis.get_coordinates()

# 撮影日時の取得
img2gis.get_datetime()
```

3. 位置情報が存在しない画像の除外（オプション）
```python
# 位置情報が存在しない画像を除外
img2gis.remove_nongeotagged_image()
```

4. QGISでの表示
- 生成されたGeoPackageファイル（summary.gpkg）をQGISに読み込む
- アクション機能を使用してポップアップ表示を設定
  - アクションタイプ: Python
  - アクションの内容: action_text.pyの内容を使用
- summary_style.qmlを使用してスタイルを適用することもできます。

5. 表示結果

![QGISの表示例 (背景は地理院地図を利用)](/image2qgis/sample.png)


## 注意事項

- 位置情報の抽出にはExifToolが必要です
- HEICファイルの処理にはpillow_heifライブラリが必要です
- QGISでの表示には、相対パスではなく絶対パスを使用する必要があります
- 画像ファイルの数が多い場合、処理に時間がかかる可能性があります

## 必要なライブラリ

- geopandas
- PIL (Pillow)
- exiftool
- pillow_heif
- pandas
- shapely
