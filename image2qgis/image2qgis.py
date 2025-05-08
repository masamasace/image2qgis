import os
from pathlib import Path
from PIL import Image
import geopandas as gpd
from shapely.geometry import Point
from exiftool import ExifToolHelper
import pillow_heif
import pandas as pd


class ImageToQGIS:
    def __init__(self, input_dir, output_dir):
        """
        初期化メソッド
        Args:
            input_dir (str): 画像ファイルのディレクトリ
            output_dir (str): GeoPackageファイルの保存先
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_image_dir = self.output_dir / "image"
        self.output_image_dir.mkdir(exist_ok=True)
        self.conv_dir = self.output_dir / "converted"
        
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.heic'}
    
    def remove_nongeotagged_image(self):
        
        gdf = self.generate_file_list()
        
        # 緯度・経度が0あるいはNoneの画像を抽出
        non_geotagged = gdf[(gdf['latitude'] == 0) | (gdf['latitude'].isnull()) | (gdf['longitude'] == 0) | (gdf['longitude'].isnull())]
        
        non_geotagged_count = len(non_geotagged)
        print(f"位置情報がない画像の数: {non_geotagged_count}")
        
        # 位置情報がない画像を削除
        for index, row in non_geotagged.iterrows():
            image_path = row['file_path']
            image_path = Path(image_path)
            
            # 画像ファイルを削除
            if image_path.exists():
                image_path.unlink()
                print(f"削除しました: {image_path.relative_to(self.input_dir)}")
            else:
                print(f"ファイルが存在しません: {image_path.relative_to(self.input_dir)}")
        
        # GeoDataFrameを更新
        gdf = gdf[(gdf['latitude'] != 0) | (gdf['longitude'] != 0)]
        
        self.save_file_list(gdf)
    
    # input_dirに存在しない画像を削除するメソッド
    def remove_not_contained_image(self):
        
        gdf = self.generate_file_list()
        
        # 画像ファイルを処理
        for index, row in gdf.iterrows():
            
            print(f"Processing {index+1}/{len(gdf)}: ", end="")
            
            image_path = row['file_path']
            image_path = Path(image_path)
            
            # 画像ファイルが存在しない場合は削除
            if not image_path.exists():
                print(f"削除しました: {image_path.relative_to(self.input_dir)}")
                gdf.drop(index, inplace=True)
            else:
                print(f"存在します: {image_path.relative_to(self.input_dir)}")
        
        self.save_file_list(gdf)
        
    
    
    def generate_file_list(self, force_new=False):
        
        # gpkgファイルの読み取り
        summary_gpkg = self.output_dir / "summary.gpkg"
        
        if summary_gpkg.exists() and not force_new:
            
            gdf = gpd.read_file(summary_gpkg)
            # print(f"既存のgpkgファイルを読み込みました: {summary_gpkg}")
            return gdf
        
        # gpkgファイルが存在しない場合は新規作成
        else:
            image_data = []
            image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.heic'}
            
            # 画像ファイルを処理
            for image_path in self.input_dir.glob('**/*'):
                if image_path.suffix.lower() in image_extensions:
                    
                    image_data.append(
                        {
                            'file_name': image_path.name,
                            'file_path': image_path,
                            'geometry': Point(0, 0)  # 初期値として(0, 0)を設定
                        }
                    )
            
            # GeoDataFrameの作成
            gdf = gpd.GeoDataFrame(image_data, geometry='geometry')
            
            # CRSの設定（WGS84）
            gdf.set_crs(epsg=4326, inplace=True)
            
            # print(f"新規にgpkgファイルを作成しました: {summary_gpkg}")
            return gdf             
            
    def save_file_list(self, gdf):
        
        # ソートとインデックスのリセット
        gdf = gdf.sort_values(by='file_name')
        gdf = gdf.reset_index(drop=True)
        
        # GeoDataFrameをgeopackage, geojson形式で保存
        summary_gpkg = self.output_dir / "summary.gpkg"
        summary_geojson = self.output_dir / "summary.geojson"

        summary_gpkg = gdf.to_file(summary_gpkg, driver='GPKG')
        summary_geojson = gdf.to_file(summary_geojson, driver='GeoJSON')
        # print("GeoPackage, GeoJSONファイルを保存しました")
    
    
    def convert_to_jpeg(self, force_new=False):
        
        gdf = self.generate_file_list()
        

        for index, row in gdf.iterrows():
            
            print(f"Processing {index+1}/{len(gdf)}: ", end="")
            
            image_path = row['file_path']
            image_path = Path(image_path)
            
            # 画像をJPEG形式に変換
            jpeg_path = self._convert_to_jpeg(image_path, force_new=force_new)
                
            gdf.at[index, 'new_file_path'] = jpeg_path
            
            if index % 10 == 0:
                self.save_file_list(gdf)
        
        self.save_file_list(gdf)
        
    
    def _convert_to_jpeg(self, image_path, max_size=1280, force_new=False):
        
        jpeg_path = self.output_image_dir / f"{image_path.stem}.jpg"
        
        if not force_new and jpeg_path.exists():
            print(f"JPEGファイルは既に存在します: {jpeg_path.relative_to(self.output_image_dir)}")
            return jpeg_path
        
        # JPEGの場合もリサイズして変換
        if image_path.suffix.lower() == '.jpg':
            with Image.open(image_path) as img:
                w, h = img.size
                scale = max_size / max(w, h)
                new_width, new_height = int(w * scale), int(h * scale)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img_resized = img.resize((new_width, new_height))
                img_resized.save(jpeg_path, 'JPEG')
            
            print(f"JPEGファイルを変換しました: {jpeg_path.relative_to(self.output_image_dir)}")
            return jpeg_path
        
        # HEICの場合
        elif image_path.suffix.lower() == '.heic':
            heif_file = pillow_heif.read_heif(image_path)[0]
            image = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode, heif_file.stride
            )
            image = image.convert("RGB")
            w, h = image.size
            scale = max_size / max(w, h)
            new_width, new_height = int(w * scale), int(h * scale)
            image_resized = image.resize((new_width, new_height))
            image_resized.save(jpeg_path, format='JPEG')
            
            print(f"HEICファイルを変換しました: {jpeg_path.relative_to(self.output_image_dir)}")
            return jpeg_path
        
        # その他の画像形式の場合
        else:
            with Image.open(image_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                w, h = img.size
                scale = max_size / max(w, h)
                new_width, new_height = int(w * scale), int(h * scale)
                img_resized = img.resize((new_width, new_height))
                img_resized.save(jpeg_path, 'JPEG')
            
            print(f"{image_path.suffix[1:]}ファイルをJPEGに変換しました: {jpeg_path.relative_to(self.output_image_dir)}")
            return jpeg_path
    
    def get_datetime(self):
        
        # gdfを読み込み
        gdf = self.generate_file_list()
        
        if "datetime" not in gdf.columns:
            gdf["datetime"] = None
        
        # 画像ファイルを処理
        for index, row in gdf.iterrows():
            
            print(f"Processing {index+1}/{len(gdf)}: ", end="")
            
            image_path = row['file_path']
            image_path = Path(image_path)
            
            if row['datetime'] is not None:
                print(f"Already exists: {row['file_name']}, datetime: {row['datetime']}")
                continue
            
            # 日時の取得
            dt = self._get_image_datetime(image_path)
            
            if dt is None:
                print(f"日時が見つかりませんでした: {image_path.name}")
                continue
            
            # 日時をGeoDataFrameに追加
            gdf.at[index, 'datetime'] = dt
            
            print(f"{image_path.name}: datetime: {dt}")
            
            if index % 10 == 0:
                self.save_file_list(gdf)
        
        self.save_file_list(gdf)
        
    def _get_image_datetime(self, image_path):
        
        # osを利用して更新日時を取得
        try:
            dt = os.path.getmtime(image_path)
            dt = pd.to_datetime(dt, unit='s')
            return dt
        except Exception as e:
            print(f"日時の取得に失敗しました: {image_path.name}, {e}")
            return None
    
    def get_coordinates(self):
        
        # gdfを読み込み
        gdf = self.generate_file_list()
        
        if "latitude" not in gdf.columns:
            gdf["latitude"] = None
        if "longitude" not in gdf.columns:
            gdf["longitude"] = None
        
        # 画像ファイルを処理
        for index, row in gdf.iterrows():
            
            print(f"Processing {index+1}/{len(gdf)}: ", end="")
            
            image_path = row['file_path']
            image_path = Path(image_path)
            
            if row['latitude'] is not None and row['longitude'] is not None:
                print(f"Already exists: {row['file_name']}, lat: {row['latitude']}, lon: {row['longitude']}")
                continue
            
            # 位置情報の取得
            lat, lon = self._get_image_coordinates(image_path)
            
            if lat is None or lon is None:
                print(f"位置情報が見つかりませんでした: {image_path.name}")
                continue
            
            # 緯度・経度をGeoDataFrameに追加
            gdf.at[index, 'latitude'] = lat
            gdf.at[index, 'longitude'] = lon
            gdf.at[index, 'geometry'] = Point(lon, lat)
            
            print(f"{image_path.name}: lat: {lat}, lon: {lon}")
            
            if index % 10 == 0:
                self.save_file_list(gdf)
        
        self.save_file_list(gdf)
        
        
    # 位置情報を取得するメソッド
    def _get_image_coordinates(self, image_path):
            
            with ExifToolHelper(encoding="utf-8") as et:
                metadata = et.get_metadata(str(image_path))
                
                try:
                    lat = metadata[0].get('EXIF:GPSLatitude')
                    lon = metadata[0].get('EXIF:GPSLongitude')
                    
                    if lat is None or lon is None:
                        return None, None
                    
                    return lat, lon
                
                except Exception as e:
                    print(f"位置情報の取得に失敗しました: {image_path.name}, {e}")
                    return None, None
    
    # NOTE: このメソッドは実行する必要はない
    # 理由：QGISは生成されるHTMLに対して、相対パスの動的生成には対応していないため
    # そのため、Edit Actionを利用するようにする
    def generate_html(self):
        
        # gdfを読み込み
        gdf = self.generate_file_list()
        
        # HTMLコードを生成
        
        for index, row in gdf.iterrows():
            
            print(f"Processing {index+1}/{len(gdf)}: ", end="")
            
            html_code = ""
            
            file_name = row['file_name']
            file_path = row['file_path']
            lat = row['latitude']
            lon = row['longitude']
            datetime = row['datetime']
            thumb_path = row['new_file_path']
            
            html_code = self._generate_html(file_name, file_path, thumb_path, lat, lon, datetime)
        
            gdf.at[index, 'html_code'] = html_code
            
            print(f"HTMLコードを生成しました: {file_name}")
            
            if index % 1000 == 0:
                self.save_file_list(gdf)
                
        # GeoDataFrameをGeoPackageに保存
        self.save_file_list(gdf)
        
        print("HTMLコードを生成しが完了しました")
    

    def _generate_html(self, file_name, file_path, thumb_path, lat, lon, datetime):
        
        file_path = Path(file_path)
        file_path_qgis = f"file:///{str(file_path.absolute()).replace(os.sep, '/')}"
        thumb_path = Path(thumb_path)
        thumb_path_name = Path(thumb_path).name
        
        # QGIS用のパスに変換
        # NOTE: 2行目は相対パスを活用したもの、ただし現時点 (2025/05/08) では動作しない
        # より正確に記述すると、html_codeフィールドを読み込ませると、画像は表示されないが
        # 同じhtmlコードをHTML Map Tipに貼り付けると表示される
        
        thumb_path_qgis = f"file:///{str(thumb_path.absolute()).replace(os.sep, '/')}"
        # thumb_path_qgis = "file:///[% replace( file_path(layer_property(@layer_id, 'path')), '\\\\', '/') %]/image/" + thumb_path_name
        
        if lat is None or lon is None:
            lat, lon = 0, 0
        else:
            lat, lon = float(lat), float(lon)
            
        if datetime is None:
            datetime = "不明"
        
        html = f"""
        <table style="border:none;">
            <tr>
                <td>画像名</td>
                <td><a href="{file_path_qgis}">{file_name}</a></td>
            </tr>
            <tr>
                <td>緯度経度</td>
                <td><a href="https://www.google.com/maps/search/?api=1&query={lat},{lon}" target="_blank">{lat:.6f}, {lon:.6f}</a></td>
            </tr>
            <tr>
                <td>撮影日時</td>
                <td>{datetime}</td>
            <tr>
            <tr>
                <td colspan="2">
                    <a href="{file_path_qgis}">
                        <img src="{thumb_path_qgis}" style="max-width:300px; max-height:300px;">
                    </a>
                </td>
            </tr>
        </table>
        """
        return html
    
    # remmove_html_code_columnメソッド
    def remove_html_code_column(self):
        
        # gdfを読み込み
        gdf = self.generate_file_list()
        
        # html_code列を削除
        if "html_code" in gdf.columns:
            gdf.drop(columns=["html_code"], inplace=True)
            print("html_code列を削除しました")
        else:
            print("html_code列は存在しません")
        
        # GeoDataFrameをGeoPackageに保存
        self.save_file_list(gdf)