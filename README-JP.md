[日本語](README-JP.md) | [English](README.md)

# SquatScope - IMU+EMG BLE Data Receiver

M5StickC Plus2からのIMU（6軸）および筋電位データを1000HzでBLE受信・可視化するPythonアプリケーションです。

ハードウエアに関してはこちらから
https://www.hackster.io/yoshizawa555res/squatscope-3d837a#schematics

## 🔧 環境情報

- **Python バージョン**: 3.9.12
- **環境タイプ**: 仮想環境 (venv)

## 📦 パッケージ

### BLE通信
- `bleak` (1.1.0) - クロスプラットフォームBLEライブラリ
- `pyobjc-framework-CoreBluetooth` (11.1) - macOS BLEサポート

### データ処理・可視化
- `numpy` (2.0.2) - 数値計算
- `pandas` (2.3.1) - データ分析
- `tkinter` - GUI (Python標準ライブラリ)

### その他
- `pyserial` (3.5) - シリアル通信
- `psutil` (7.0.0) - システム情報
- `async-timeout` (5.0.1) - 非同期タイムアウト

## 🚀 使用方法

### 1. 仮想環境の有効化

```bash
cd あなたのルートディレクトリ/SquatScope/Python
source ../venv/bin/activate  # macOS/Linux
# または ..\venv\Scripts\activate  # Windows
```

### 2. アプリケーションの実行

```bash
# メインGUIアプリケーション
python src/main.py

# コマンドライン接続テスト
python test_connection.py
```

### 3. 仮想環境の無効化

```bash
deactivate
```


## ⚡ システム機能

### BLE通信 (1000Hz)
- M5StickC Plus2からの高速データ受信
- バイナリフォーマット (14バイト/サンプル × 10サンプル/パケット)
- パケット紛失検出と統計表示
- 自動再接続処理

### データ処理
- **7チャネル**: 加速度3軸 + ジャイロ3軸 + EMG1チャネル
- **リアルタイムフィルタリング**: ローパスフィルタでノイズ除去
- **派生指標**: RMS、平均、標準偏差、動き検出
- **1000サンプル分のバッファ管理**n

### 可視化・UI
- ダークモードUI
- リアルタイムグラフ表示
- 接続状態・統計情報表示
- データ保存・読み込み機能

## 🔧 開発者向け情報

### 新しいパッケージの追加

```bash
# 仮想環境を有効化
source ../venv/bin/activate

# パッケージをインストール
pip install package_name

# requirements.txtを更新
pip freeze | grep -E "(bleak|numpy|pandas|pyobjc)" > requirements.txt
```

### データフォーマット

**受信データ構造:**
```
パケット: [2B パケット番号] + [14B × 10サンプル]
1サンプル: accX,accY,accZ,gyroX,gyroY,gyroZ,emg (各int16_t)
```

**スケーリング:**
- 加速度: ±8G → int16_t (1G = 4096)
- ジャイロ: ±2000dps → int16_t (1dps = 16.384)  
- EMG: 12bit ADC値 (0-4095)

### カスタマイズポイント

- **フィルタ係数**: `data_processor.py`のfilter_alpha値
- **バッファサイズ**: `DataProcessor.__init__(buffer_size=1000)`
- **表示更新間隔**: `main.py`のupdate_intervals

## 🐛 トラブルシューティング

### BLE接続エラー
```bash
# Bluetoothサービス再起動 (macOS)
sudo pkill bluetoothd

# 権限確認
ls -la /dev/cu.Bluetooth-Incoming-Port
```

### パッケージエラー
```bash
# pipアップグレード
pip install --upgrade pip

# キャッシュクリア
pip cache purge

# 再インストール
pip install -r requirements.txt --force-reinstall
```

### 高いパケット紛失率
1. デバイス間の距離を短くする
2. 他の2.4GHz機器を停止
3. BLE接続間隔を確認
4. MTUサイズ交渉を確認

## 📊 パフォーマンス

- **目標データレート**: 1000Hz × 7ch = 7000サンプル/秒
- **実測パケット転送**: ~100パケット/秒 (10サンプル/パケット)
- **最大遅延**: <20ms（バッチ送信による）
- **紛失率**: <1%（良好な環境下）

## 📝 ライセンス

このプロジェクトはMITライセンスの下で提供されています。

