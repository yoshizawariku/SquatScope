import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import tkinter as tk
from collections import deque
import threading
import time

class RealTimePlotter:
    """リアルタイムデータ表示用のプロッタークラス"""
    
    def __init__(self, parent, title="Data", ylabel="Value", window_size=1000, 
                 line_configs=None, figsize=(6, 3)):
        self.parent = parent
        self.title = title
        self.ylabel = ylabel
        self.window_size = window_size
        self.line_configs = line_configs or [
            {'label': 'Data', 'color': 'blue', 'linewidth': 1}
        ]
        
        # データバッファ
        self.time_data = deque(maxlen=window_size)
        self.data_buffers = {}
        for i, config in enumerate(self.line_configs):
            self.data_buffers[i] = deque(maxlen=window_size)
        
        # Matplotlib設定
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.fig.patch.set_facecolor('#2E2E2E')
        self.ax.set_facecolor('#3E3E3E')
        
        # プロットライン初期化
        self.lines = {}
        for i, config in enumerate(self.line_configs):
            line, = self.ax.plot([], [], 
                               label=config['label'], 
                               color=config['color'],
                               linewidth=config.get('linewidth', 1))
            self.lines[i] = line
        
        # グラフのスタイル設定
        self.setup_plot_style()
        
        # Tkinterキャンバス
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # データ更新用
        self.last_update = time.time()
        self.update_interval = 0.1  # 10FPS - より安定した表示
        
    def setup_plot_style(self):
        """プロットのスタイルを設定"""
        self.ax.set_title(self.title, color='white', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('Time (seconds)', color='white', fontsize=10)
        self.ax.set_ylabel(self.ylabel, color='white', fontsize=10)
        
        # 軸とグリッドのスタイル
        self.ax.tick_params(colors='white', labelsize=9)
        self.ax.grid(True, alpha=0.3, color='gray')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        
        # 凡例
        if len(self.line_configs) > 1:
            legend = self.ax.legend(loc='upper right', fontsize=9)
            legend.get_frame().set_facecolor('#2E2E2E')
            legend.get_frame().set_alpha(0.8)
            for text in legend.get_texts():
                text.set_color('white')
    
    def add_data(self, timestamp, *values):
        """データを追加"""
        if len(values) != len(self.line_configs):
            return
            
        # 現在時刻との相対時間を計算
        if not self.time_data:
            self.start_time = timestamp
            relative_time = 0
        else:
            relative_time = (timestamp - self.start_time) / 1000.0  # ミリ秒を秒に変換
        
        self.time_data.append(relative_time)
        
        for i, value in enumerate(values):
            if i in self.data_buffers:
                self.data_buffers[i].append(value)
        
        # フレームレート制御
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.update_plot()
            self.last_update = current_time
    
    def update_plot(self):
        """プロットを更新"""
        if not self.time_data:
            return
            
        time_array = list(self.time_data)
        
        for i, line in self.lines.items():
            if i in self.data_buffers and self.data_buffers[i]:
                data_array = list(self.data_buffers[i])
                if len(data_array) == len(time_array):
                    line.set_data(time_array, data_array)
        
        # 軸の範囲を自動調整
        if time_array:
            # 時間窓を調整 - より長い期間を表示
            time_window = 20  # 20秒のウィンドウ
            if len(time_array) > 1:
                data_duration = time_array[-1] - time_array[0]
                if data_duration < time_window:
                    # データが少ない場合は全データを表示
                    self.ax.set_xlim(time_array[0] - 1, time_array[-1] + 1)
                else:
                    # データが多い場合は最新の時間窓を表示
                    self.ax.set_xlim(time_array[-1] - time_window, time_array[-1] + 1)
            else:
                self.ax.set_xlim(0, time_window)
            
            # Y軸の範囲を全データに基づいて設定
            all_values = []
            for buffer in self.data_buffers.values():
                if buffer:
                    all_values.extend(list(buffer))
            
            if all_values:
                y_min, y_max = min(all_values), max(all_values)
                y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
                self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
        
        self.canvas.draw_idle()
    
    def clear_data(self):
        """データをクリア"""
        self.time_data.clear()
        for buffer in self.data_buffers.values():
            buffer.clear()
        self.update_plot()


class MultiChannelPlotter:
    """多チャネルデータ用のプロッタークラス"""
    
    def __init__(self, parent, title="Multi-Channel Data", window_size=1000, figsize=(8, 6)):
        self.parent = parent
        self.title = title
        self.window_size = window_size
        
        # データバッファ
        self.time_data = deque(maxlen=window_size)
        self.emg_data = deque(maxlen=window_size)
        self.acc_x_data = deque(maxlen=window_size)
        self.acc_y_data = deque(maxlen=window_size)
        self.acc_z_data = deque(maxlen=window_size)
        self.gyro_x_data = deque(maxlen=window_size)
        self.gyro_y_data = deque(maxlen=window_size)
        self.gyro_z_data = deque(maxlen=window_size)
        
        # Matplotlib設定（3つのサブプロット）
        self.fig, (self.ax_emg, self.ax_acc, self.ax_gyro) = plt.subplots(3, 1, figsize=figsize, 
                                                                         sharex=True)
        self.fig.patch.set_facecolor('#2E2E2E')
        
        # プロットライン初期化
        self.setup_plots()
        
        # Tkinterキャンバス
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 更新制御
        self.last_update = time.time()
        self.update_interval = 0.1  # 10FPS - より安定した表示
        
    def setup_plots(self):
        """プロットを設定"""
        # EMGプロット
        self.emg_line, = self.ax_emg.plot([], [], 'r-', label='EMG', linewidth=1)
        self.ax_emg.set_title('Electromyography (EMG)', color='white', fontsize=11, fontweight='bold')
        self.ax_emg.set_ylabel('ADC Value', color='white', fontsize=9)
        self.setup_axis_style(self.ax_emg)
        
        # 加速度プロット
        self.acc_x_line, = self.ax_acc.plot([], [], 'b-', label='X', linewidth=1)
        self.acc_y_line, = self.ax_acc.plot([], [], 'g-', label='Y', linewidth=1)
        self.acc_z_line, = self.ax_acc.plot([], [], 'r-', label='Z', linewidth=1)
        self.ax_acc.set_title('Acceleration', color='white', fontsize=11, fontweight='bold')
        self.ax_acc.set_ylabel('G', color='white', fontsize=9)
        self.setup_axis_style(self.ax_acc)
        legend_acc = self.ax_acc.legend(loc='upper right', fontsize=8)
        self.setup_legend_style(legend_acc)
        
        # ジャイロプロット
        self.gyro_x_line, = self.ax_gyro.plot([], [], 'b-', label='X', linewidth=1)
        self.gyro_y_line, = self.ax_gyro.plot([], [], 'g-', label='Y', linewidth=1)
        self.gyro_z_line, = self.ax_gyro.plot([], [], 'r-', label='Z', linewidth=1)
        self.ax_gyro.set_title('Angular Velocity', color='white', fontsize=11, fontweight='bold')
        self.ax_gyro.set_ylabel('dps', color='white', fontsize=9)
        self.ax_gyro.set_xlabel('Time (seconds)', color='white', fontsize=9)
        self.setup_axis_style(self.ax_gyro)
        legend_gyro = self.ax_gyro.legend(loc='upper right', fontsize=8)
        self.setup_legend_style(legend_gyro)
        
        plt.tight_layout()
    
    def setup_axis_style(self, ax):
        """軸のスタイルを設定"""
        ax.set_facecolor('#3E3E3E')
        ax.tick_params(colors='white', labelsize=8)
        ax.grid(True, alpha=0.3, color='gray')
        for spine in ax.spines.values():
            spine.set_color('white')
    
    def setup_legend_style(self, legend):
        """凡例のスタイルを設定"""
        legend.get_frame().set_facecolor('#2E2E2E')
        legend.get_frame().set_alpha(0.8)
        for text in legend.get_texts():
            text.set_color('white')
    
    def add_data(self, timestamp, emg_value, acc_data, gyro_data):
        """データを追加"""
        # 現在時刻との相対時間を計算
        if not self.time_data:
            self.start_time = timestamp
            relative_time = 0
        else:
            relative_time = (timestamp - self.start_time) / 1000.0  # ミリ秒を秒に変換
        
        self.time_data.append(relative_time)
        self.emg_data.append(emg_value)
        self.acc_x_data.append(acc_data[0])
        self.acc_y_data.append(acc_data[1])
        self.acc_z_data.append(acc_data[2])
        self.gyro_x_data.append(gyro_data[0])
        self.gyro_y_data.append(gyro_data[1])
        self.gyro_z_data.append(gyro_data[2])
        
        # フレームレート制御
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.update_plot()
            self.last_update = current_time
    
    def update_plot(self):
        """プロットを更新"""
        if not self.time_data:
            return
            
        time_array = list(self.time_data)
        
        # EMGプロット更新
        if self.emg_data:
            self.emg_line.set_data(time_array, list(self.emg_data))
        
        # 加速度プロット更新
        if self.acc_x_data:
            self.acc_x_line.set_data(time_array, list(self.acc_x_data))
            self.acc_y_line.set_data(time_array, list(self.acc_y_data))
            self.acc_z_line.set_data(time_array, list(self.acc_z_data))
        
        # ジャイロプロット更新
        if self.gyro_x_data:
            self.gyro_x_line.set_data(time_array, list(self.gyro_x_data))
            self.gyro_y_line.set_data(time_array, list(self.gyro_y_data))
            self.gyro_z_line.set_data(time_array, list(self.gyro_z_data))
        
        # 軸の範囲を調整
        if time_array:
            time_window = 20  # 20秒のウィンドウ
            
            if len(time_array) > 1:
                data_duration = time_array[-1] - time_array[0]
                if data_duration < time_window:
                    # データが少ない場合は全データを表示
                    x_min = time_array[0] - 1
                    x_max = time_array[-1] + 1
                else:
                    # データが多い場合は最新の時間窓を表示
                    x_min = time_array[-1] - time_window
                    x_max = time_array[-1] + 1
            else:
                x_min = 0
                x_max = time_window
            
            for ax in [self.ax_emg, self.ax_acc, self.ax_gyro]:
                ax.set_xlim(x_min, x_max)
            
            # Y軸の範囲を個別に設定
            self.auto_scale_y_axis(self.ax_emg, self.emg_data)
            self.auto_scale_y_axis(self.ax_acc, [self.acc_x_data, self.acc_y_data, self.acc_z_data])
            self.auto_scale_y_axis(self.ax_gyro, [self.gyro_x_data, self.gyro_y_data, self.gyro_z_data])
        
        self.canvas.draw_idle()
    
    def auto_scale_y_axis(self, ax, data_buffers):
        """Y軸の範囲を自動調整"""
        all_values = []
        
        if isinstance(data_buffers, list):
            for buffer in data_buffers:
                if buffer:
                    all_values.extend(list(buffer))
        else:
            if data_buffers:
                all_values.extend(list(data_buffers))
        
        if all_values:
            y_min, y_max = min(all_values), max(all_values)
            y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
            ax.set_ylim(y_min - y_margin, y_max + y_margin)
    
    def clear_data(self):
        """データをクリア"""
        self.time_data.clear()
        self.emg_data.clear()
        self.acc_x_data.clear()
        self.acc_y_data.clear()
        self.acc_z_data.clear()
        self.gyro_x_data.clear()
        self.gyro_y_data.clear()
        self.gyro_z_data.clear()
        self.update_plot()