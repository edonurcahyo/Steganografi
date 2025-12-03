import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import os
import math
import io
import numpy as np
import webbrowser
from datetime import datetime
import sys

def ubah_teks_ke_bit(teks):
    return ''.join(f'{byte:08b}' for byte in teks.encode())

def ubah_bit_ke_teks(bit):
    hasil_bytes = []
    for i in range(0, len(bit), 8):
        b = bit[i:i+8]
        if len(b) == 8:
            hasil_bytes.append(int(b, 2))
    return bytes(hasil_bytes).decode(errors='ignore')

def sembunyikan_pesan(path_gambar_masuk, path_gambar_keluar, pesan):
    try:
        gambar = Image.open(path_gambar_masuk)
        gambar = gambar.convert("RGB")
        piksel = gambar.load()

        # Tambahkan timestamp dan info panjang pesan
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pesan_dengan_info = f"[{timestamp}]|{len(pesan)}|{pesan}"
        
        bit_pesan = ubah_teks_ke_bit(pesan_dengan_info) + "0000000000000000"  # 16-bit terminator
        indeks_bit = 0
        panjang_bit = len(bit_pesan)

        # Cek kapasitas
        kapasitas_maks = gambar.width * gambar.height * 3
        if panjang_bit > kapasitas_maks:
            return False, f"Pesan terlalu panjang! Kapasitas: {kapasitas_maks//8} karakter"

        for y in range(gambar.height):
            for x in range(gambar.width):
                if indeks_bit >= panjang_bit:
                    break

                r, g, b = piksel[x, y]

                if indeks_bit < panjang_bit:
                    r = (r & 0xFE) | int(bit_pesan[indeks_bit])
                    indeks_bit += 1

                if indeks_bit < panjang_bit:
                    g = (g & 0xFE) | int(bit_pesan[indeks_bit])
                    indeks_bit += 1

                if indeks_bit < panjang_bit:
                    b = (b & 0xFE) | int(bit_pesan[indeks_bit])
                    indeks_bit += 1

                piksel[x, y] = (r, g, b)

            if indeks_bit >= panjang_bit:
                break

        gambar.save(path_gambar_keluar)
        
        # Hitung penggunaan kapasitas
        persentase_penggunaan = (panjang_bit / kapasitas_maks) * 100
        
        return True, f"Pesan berhasil disembunyikan!\nPenggunaan kapasitas: {persentase_penggunaan:.2f}%"
    except Exception as e:
        return False, f"Error: {str(e)}"

def ambil_pesan(path_gambar):
    try:
        gambar = Image.open(path_gambar)
        gambar = gambar.convert("RGB")
        piksel = gambar.load()

        bit_terambil = ""

        for y in range(gambar.height):
            for x in range(gambar.width):
                r, g, b = piksel[x, y]

                bit_terambil += str(r & 1)
                bit_terambil += str(g & 1)
                bit_terambil += str(b & 1)

                if bit_terambil.endswith("0000000000000000"):
                    pesan_bit_asli = bit_terambil[:-16]
                    
                    # Decode pesan
                    pesan_terenkripsi = ubah_bit_ke_teks(pesan_bit_asli)
                    
                    # Parse informasi tambahan
                    if '|' in pesan_terenkripsi:
                        parts = pesan_terenkripsi.split('|', 2)
                        if len(parts) >= 3:
                            timestamp = parts[0]
                            panjang = parts[1]
                            pesan_asli = parts[2]
                            return f"Waktu: {timestamp}\nPanjang: {panjang} karakter\n\nPesan: {pesan_asli}"
                    
                    return pesan_terenkripsi

        return "Tidak ditemukan pesan atau terminator tidak ditemukan"
    except Exception as e:
        return f"Error: {str(e)}"

def hitung_psnr(gambar_asli_path, gambar_stego_path):
    """Hitung PSNR antara gambar asli dan gambar stego"""
    try:
        img1 = Image.open(gambar_asli_path).convert("RGB")
        img2 = Image.open(gambar_stego_path).convert("RGB")
        
        if img1.size != img2.size:
            return "Ukuran gambar tidak sama"
        
        # Konversi ke array numpy
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Hitung MSE (Mean Squared Error)
        mse = np.mean((arr1 - arr2) ** 2)
        
        if mse == 0:
            return "∞ (Identical)"
        
        # Hitung PSNR
        max_pixel = 255.0
        psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        
        return f"{psnr:.2f} dB"
    except Exception as e:
        return f"Error: {str(e)}"

def hitung_mse(gambar_asli_path, gambar_stego_path):
    """Hitung MSE antara gambar asli dan gambar stego"""
    try:
        img1 = Image.open(gambar_asli_path).convert("RGB")
        img2 = Image.open(gambar_stego_path).convert("RGB")
        
        if img1.size != img2.size:
            return "Ukuran gambar tidak sama"
        
        # Konversi ke array numpy
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Hitung MSE (Mean Squared Error)
        mse = np.mean((arr1 - arr2) ** 2)
        
        return f"{mse:.6f}"
    except Exception as e:
        return f"Error: {str(e)}"

class SteganografiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steganografi dengan LSB - Hide & Extract Messages")
        self.root.geometry("1000x850")
        
        # Style
        self.setup_style()
        
        # Variabel untuk menyimpan path gambar
        self.input_image_path = ""
        self.output_image_path = ""
        self.extracted_image_path = ""
        
        # Setup GUI
        self.setup_gui()
        
    def setup_style(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 14, "bold"), foreground="darkblue")
        style.configure("Subtitle.TLabel", font=("Arial", 11, "bold"), foreground="darkgreen")
        style.configure("Info.TLabel", font=("Arial", 10), foreground="gray")
        
    def setup_gui(self):
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        
        # Title
        title_frame = ttk.Frame(main_container)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(title_frame, text="STEGANOGRAFI DENGAN LEAST SIGNIFICANT BIT (LSB)", 
                 style="Title.TLabel").grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(title_frame, text="Sembunyikan dan Ekstrak Pesan dari Gambar", 
                 style="Subtitle.TLabel").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Notebook untuk tab utama
        main_notebook = ttk.Notebook(main_container)
        main_notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Tab 1: Hide Message
        hide_tab = ttk.Frame(main_notebook)
        main_notebook.add(hide_tab, text="Sembunyikan Pesan")
        self.setup_hide_tab(hide_tab)
        
        # Tab 2: Extract Message
        extract_tab = ttk.Frame(main_notebook)
        main_notebook.add(extract_tab, text="Ekstrak Pesan")
        self.setup_extract_tab(extract_tab)
        
        # Tab 3: Comparison & Analysis
        analysis_tab = ttk.Frame(main_notebook)
        main_notebook.add(analysis_tab, text="Analisis & Perbandingan")
        self.setup_analysis_tab(analysis_tab)
        
        # Status bar
        self.status_bar = ttk.Label(main_container, text="Status: Siap", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_hide_tab(self, parent):
        # Input Image Section
        input_frame = ttk.LabelFrame(parent, text="1. Pilih Gambar Input", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="File Gambar:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_path_entry = ttk.Entry(input_frame, width=60)
        self.input_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(input_frame, text="Browse...", command=self.browse_input_image).grid(row=0, column=2, padx=5)
        
        # Image Info
        self.image_info_label = ttk.Label(input_frame, text="", style="Info.TLabel")
        self.image_info_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Message Section
        message_frame = ttk.LabelFrame(parent, text="2. Masukkan Pesan Rahasia", padding="10")
        message_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        message_frame.columnconfigure(0, weight=1)
        
        # Frame untuk text input dengan tombol browse
        message_input_frame = ttk.Frame(message_frame)
        message_input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        message_input_frame.columnconfigure(0, weight=1)
        
        ttk.Label(message_input_frame, text="Pesan:").grid(row=0, column=0, sticky=tk.W)
        
        # Frame untuk tombol-tombol
        message_buttons_frame = ttk.Frame(message_input_frame)
        message_buttons_frame.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        # Tombol untuk membuka file txt
        ttk.Button(message_buttons_frame, text="Buka File TXT", 
                  command=self.browse_text_file, width=12).pack(side=tk.LEFT, padx=2)
        
        # Tombol untuk menghapus teks
        ttk.Button(message_buttons_frame, text="Hapus Teks", 
                  command=self.clear_message_text, width=10).pack(side=tk.LEFT, padx=2)
        
        # Area input pesan
        self.pesan_entry = scrolledtext.ScrolledText(message_frame, width=80, height=10)
        self.pesan_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Info karakter
        self.char_count_label = ttk.Label(message_frame, text="Karakter: 0", style="Info.TLabel")
        self.char_count_label.grid(row=2, column=0, sticky=tk.W)
        
        # Bind event untuk menghitung karakter
        self.pesan_entry.bind('<KeyRelease>', self.update_char_count)
        
        # Output Options
        output_frame = ttk.LabelFrame(parent, text="3. Pengaturan Output", padding="10")
        output_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(output_frame, text="Nama File Output:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.output_name_entry = ttk.Entry(output_frame, width=40)
        self.output_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.output_name_entry.insert(0, "stego_output.png")
        
        # Action Button
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=3, column=0, pady=20)
        
        ttk.Button(action_frame, text="Sembunyikan Pesan", command=self.sembunyikan_pesan_gui,
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Reset", command=self.reset_hide_tab,
                  width=15).pack(side=tk.LEFT, padx=5)
        
    def setup_extract_tab(self, parent):
        # Stego Image Section
        stego_frame = ttk.LabelFrame(parent, text="1. Pilih Gambar Stego", padding="10")
        stego_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        stego_frame.columnconfigure(1, weight=1)
        
        ttk.Label(stego_frame, text="File Gambar Stego:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stego_path_entry = ttk.Entry(stego_frame, width=60)
        self.stego_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(stego_frame, text="Browse...", command=self.browse_stego_image).grid(row=0, column=2, padx=5)
        
        # Extract Button
        extract_btn_frame = ttk.Frame(parent)
        extract_btn_frame.grid(row=1, column=0, pady=10)
        
        ttk.Button(extract_btn_frame, text="Ekstrak Pesan", command=self.ambil_pesan_gui,
                  width=20).pack()
        
        # Extracted Message Section
        extracted_frame = ttk.LabelFrame(parent, text="2. Pesan yang Ditemukan", padding="10")
        extracted_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        extracted_frame.columnconfigure(0, weight=1)
        extracted_frame.rowconfigure(0, weight=1)
        
        self.pesan_ditemukan_text = scrolledtext.ScrolledText(extracted_frame, width=80, height=15)
        self.pesan_ditemukan_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame untuk tombol di bawah pesan yang diekstrak
        extracted_buttons_frame = ttk.Frame(parent)
        extracted_buttons_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(extracted_buttons_frame, text="Simpan Pesan ke File", 
                  command=self.save_extracted_message, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(extracted_buttons_frame, text="Hapus Hasil", 
                  command=self.clear_extracted_message, width=15).pack(side=tk.LEFT, padx=5)
        
    def setup_analysis_tab(self, parent):
        # Comparison Section
        comparison_frame = ttk.LabelFrame(parent, text="Perbandingan Gambar Asli vs Stego", padding="10")
        comparison_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        comparison_frame.columnconfigure(1, weight=1)
        
        # Original Image
        ttk.Label(comparison_frame, text="Gambar Asli:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.original_compare_entry = ttk.Entry(comparison_frame, width=50)
        self.original_compare_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(comparison_frame, text="Browse...", command=self.browse_original_compare).grid(row=0, column=2, padx=5)
        
        # Stego Image
        ttk.Label(comparison_frame, text="Gambar Stego:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.stego_compare_entry = ttk.Entry(comparison_frame, width=50)
        self.stego_compare_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(comparison_frame, text="Browse...", command=self.browse_stego_compare).grid(row=1, column=2, padx=5)
        
        # Calculate Button
        ttk.Button(comparison_frame, text="Hitung Perbandingan", command=self.hitung_perbandingan_lengkap,
                  width=20).grid(row=2, column=0, columnspan=3, pady=10)
        
        # Results Frame
        results_frame = ttk.LabelFrame(parent, text="Hasil Analisis", padding="10")
        results_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Results grid
        results_grid = ttk.Frame(results_frame)
        results_grid.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Visual Comparison
        ttk.Label(results_grid, text="Perbedaan Visual:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.visual_label = ttk.Label(results_grid, text="Belum dihitung", foreground="blue")
        self.visual_label.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        # File Size
        ttk.Label(results_grid, text="Ukuran File:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.size_label = ttk.Label(results_grid, text="Belum dihitung", foreground="blue")
        self.size_label.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # PSNR
        ttk.Label(results_grid, text="PSNR (Peak Signal-to-Noise Ratio):", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.psnr_label = ttk.Label(results_grid, text="Belum dihitung", foreground="blue")
        self.psnr_label.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        
        # MSE
        ttk.Label(results_grid, text="MSE (Mean Squared Error):", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.mse_label = ttk.Label(results_grid, text="Belum dihitung", foreground="blue")
        self.mse_label.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Image Previews
        preview_frame = ttk.LabelFrame(parent, text="Preview Gambar", padding="10")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Original Preview
        ttk.Label(preview_frame, text="Gambar Asli:").grid(row=0, column=0, padx=20)
        self.original_preview_container = tk.Frame(preview_frame, relief=tk.SUNKEN, borderwidth=2)
        self.original_preview_container.grid(row=1, column=0, padx=20, pady=5)
        self.original_preview_label = tk.Label(self.original_preview_container, text="Tidak ada gambar", width=25, height=10)
        self.original_preview_label.pack(padx=5, pady=5)
        
        # Stego Preview
        ttk.Label(preview_frame, text="Gambar Stego:").grid(row=0, column=1, padx=20)
        self.stego_preview_container = tk.Frame(preview_frame, relief=tk.SUNKEN, borderwidth=2)
        self.stego_preview_container.grid(row=1, column=1, padx=20, pady=5)
        self.stego_preview_label = tk.Label(self.stego_preview_container, text="Tidak ada gambar", width=25, height=10)
        self.stego_preview_label.pack(padx=5, pady=5)
        
        # Difference Preview
        ttk.Label(preview_frame, text="Perbedaan:").grid(row=0, column=2, padx=20)
        self.diff_preview_container = tk.Frame(preview_frame, relief=tk.SUNKEN, borderwidth=2)
        self.diff_preview_container.grid(row=1, column=2, padx=20, pady=5)
        self.diff_preview_label = tk.Label(self.diff_preview_container, text="Tidak ada gambar", width=25, height=10)
        self.diff_preview_label.pack(padx=5, pady=5)
        
    def browse_input_image(self):
        file_path = filedialog.askopenfilename(
            title="Pilih Gambar Input",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if file_path:
            self.input_image_path = file_path
            self.input_path_entry.delete(0, tk.END)
            self.input_path_entry.insert(0, file_path)
            self.update_image_info(file_path)
            
    def browse_text_file(self):
        """Membuka dialog untuk memilih file teks"""
        file_path = filedialog.askopenfilename(
            title="Pilih File Teks",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                # Tampilkan konten di text area
                self.pesan_entry.delete("1.0", tk.END)
                self.pesan_entry.insert("1.0", content)
                
                # Update karakter count
                self.update_char_count()
                
                # Tampilkan info
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                self.status_bar.config(text=f"File '{filename}' berhasil dibuka ({file_size} bytes)")
                
            except UnicodeDecodeError:
                # Coba dengan encoding lain
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        content = file.read()
                    
                    self.pesan_entry.delete("1.0", tk.END)
                    self.pesan_entry.insert("1.0", content)
                    self.update_char_count()
                    
                    filename = os.path.basename(file_path)
                    self.status_bar.config(text=f"File '{filename}' dibuka dengan encoding latin-1")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Gagal membaca file: {str(e)}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka file: {str(e)}")
                
    def browse_stego_image(self):
        file_path = filedialog.askopenfilename(
            title="Pilih Gambar Stego",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if file_path:
            self.stego_path_entry.delete(0, tk.END)
            self.stego_path_entry.insert(0, file_path)
            
    def browse_original_compare(self):
        file_path = filedialog.askopenfilename(
            title="Pilih Gambar Asli",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if file_path:
            self.original_compare_entry.delete(0, tk.END)
            self.original_compare_entry.insert(0, file_path)
            self.update_preview(file_path, self.original_preview_label)
            
    def browse_stego_compare(self):
        file_path = filedialog.askopenfilename(
            title="Pilih Gambar Stego",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if file_path:
            self.stego_compare_entry.delete(0, tk.END)
            self.stego_compare_entry.insert(0, file_path)
            self.update_preview(file_path, self.stego_preview_label)
            
    def update_image_info(self, image_path):
        try:
            img = Image.open(image_path)
            width, height = img.size
            file_size = os.path.getsize(image_path)
            file_size_kb = file_size / 1024
            
            # Hitung kapasitas maksimum (setiap piksel RGB bisa menyimpan 3 bit)
            kapasitas_maks = width * height * 3
            kapasitas_karakter = kapasitas_maks // 8  # Setiap karakter butuh 8 bit
            
            info_text = f"Ukuran: {width} x {height} piksel | "
            info_text += f"File: {file_size_kb:.2f} KB | "
            info_text += f"Kapasitas: ~{kapasitas_karakter} karakter"
            
            self.image_info_label.config(text=info_text)
        except Exception as e:
            self.image_info_label.config(text=f"Error: {str(e)}")
            
    def update_char_count(self, event=None):
        """Update jumlah karakter di label"""
        text = self.pesan_entry.get("1.0", tk.END).strip()
        char_count = len(text)
        self.char_count_label.config(text=f"Karakter: {char_count}")
            
    def clear_message_text(self):
        """Menghapus teks di area pesan"""
        self.pesan_entry.delete("1.0", tk.END)
        self.update_char_count()
        self.status_bar.config(text="Teks telah dihapus")
            
    def clear_extracted_message(self):
        """Menghapus teks di area pesan yang diekstrak"""
        self.pesan_ditemukan_text.delete("1.0", tk.END)
        self.status_bar.config(text="Hasil ekstraksi telah dihapus")
            
    def sembunyikan_pesan_gui(self):
        if not self.input_image_path:
            messagebox.showerror("Error", "Pilih gambar input terlebih dahulu!")
            return
        
        pesan = self.pesan_entry.get("1.0", tk.END).strip()
        if not pesan:
            messagebox.showerror("Error", "Masukkan pesan rahasia terlebih dahulu!")
            return
        
        output_name = self.output_name_entry.get().strip()
        if not output_name:
            output_name = "stego_output.png"
        
        # Tentukan path output
        output_dir = os.path.dirname(self.input_image_path)
        self.output_image_path = os.path.join(output_dir, output_name)
        
        # Tanyakan konfirmasi jika file sudah ada
        if os.path.exists(self.output_image_path):
            if not messagebox.askyesno("Konfirmasi", f"File {output_name} sudah ada. Timpa?"):
                return
        
        # Sembunyikan pesan
        success, message = sembunyikan_pesan(self.input_image_path, self.output_image_path, pesan)
        
        if success:
            messagebox.showinfo("Sukses", message)
            self.status_bar.config(text="Pesan berhasil disembunyikan!")
            
            # Update preview di tab analisis
            self.original_compare_entry.delete(0, tk.END)
            self.original_compare_entry.insert(0, self.input_image_path)
            self.stego_compare_entry.delete(0, tk.END)
            self.stego_compare_entry.insert(0, self.output_image_path)
            
            # Update previews
            self.update_preview(self.input_image_path, self.original_preview_label)
            self.update_preview(self.output_image_path, self.stego_preview_label)
            
            # Tampilkan pesan konfirmasi
            self.show_success_dialog()
        else:
            messagebox.showerror("Error", message)
            self.status_bar.config(text="Gagal menyembunyikan pesan!")
            
    def show_success_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Pesan Disembunyikan!")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="✓ Pesan berhasil disembunyikan!", 
                 font=("Arial", 12, "bold"), foreground="green").pack(pady=20)
        
        ttk.Label(dialog, text=f"File disimpan sebagai:\n{self.output_image_path}").pack(pady=10)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Buka Folder", 
                  command=lambda: self.open_file_location(self.output_image_path)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="OK", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
    def ambil_pesan_gui(self):
        stego_path = self.stego_path_entry.get().strip()
        if not stego_path or not os.path.exists(stego_path):
            messagebox.showerror("Error", "Pilih gambar stego terlebih dahulu!")
            return
        
        pesan = ambil_pesan(stego_path)
        
        self.pesan_ditemukan_text.delete("1.0", tk.END)
        self.pesan_ditemukan_text.insert("1.0", pesan)
        
        self.status_bar.config(text="Pesan berhasil diekstrak!")
        
    def save_extracted_message(self):
        pesan = self.pesan_ditemukan_text.get("1.0", tk.END).strip()
        if not pesan:
            messagebox.showerror("Error", "Tidak ada pesan untuk disimpan!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Simpan Pesan",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(pesan)
                messagebox.showinfo("Sukses", f"Pesan disimpan ke: {file_path}")
                self.status_bar.config(text=f"Pesan disimpan ke: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan: {str(e)}")
                
    def hitung_perbandingan_lengkap(self):
        original_path = self.original_compare_entry.get().strip()
        stego_path = self.stego_compare_entry.get().strip()
        
        if not original_path or not os.path.exists(original_path):
            messagebox.showerror("Error", "Pilih gambar asli terlebih dahulu!")
            return
        
        if not stego_path or not os.path.exists(stego_path):
            messagebox.showerror("Error", "Pilih gambar stego terlebih dahulu!")
            return
        
        # 1. Perbedaan Visual
        try:
            img1 = Image.open(original_path)
            img2 = Image.open(stego_path)
            
            if img1.size == img2.size and img1.mode == img2.mode:
                # Periksa perbedaan piksel
                arr1 = np.array(img1)
                arr2 = np.array(img2)
                
                if np.array_equal(arr1, arr2):
                    visual_text = "Tidak ada perbedaan visual (identik)"
                else:
                    # Hitung persentase perbedaan
                    diff = np.sum(arr1 != arr2)
                    total_pixels = arr1.size
                    diff_percent = (diff / total_pixels) * 100
                    visual_text = f"Ada perbedaan ({diff_percent:.4f}% piksel berubah)"
                    
                    # Buat gambar perbedaan
                    self.create_difference_image(original_path, stego_path)
            else:
                visual_text = "Ukuran atau mode gambar berbeda"
        except Exception as e:
            visual_text = f"Error: {str(e)}"
        
        self.visual_label.config(text=visual_text)
        
        # 2. Ukuran File
        try:
            size1 = os.path.getsize(original_path)
            size2 = os.path.getsize(stego_path)
            
            size1_kb = size1 / 1024
            size2_kb = size2 / 1024
            selisih_kb = size2_kb - size1_kb
            selisih_persen = (selisih_kb / size1_kb) * 100 if size1_kb > 0 else 0
            
            size_text = f"Asli: {size1_kb:.2f} KB, Stego: {size2_kb:.2f} KB\n"
            size_text += f"Selisih: {selisih_kb:+.2f} KB ({selisih_persen:+.2f}%)"
        except Exception as e:
            size_text = f"Error: {str(e)}"
        
        self.size_label.config(text=size_text)
        
        # 3. PSNR
        psnr_text = hitung_psnr(original_path, stego_path)
        self.psnr_label.config(text=psnr_text)
        
        # 4. MSE
        mse_text = hitung_mse(original_path, stego_path)
        self.mse_label.config(text=mse_text)
        
        self.status_bar.config(text="Perbandingan selesai dihitung!")
        
    def create_difference_image(self, original_path, stego_path):
        try:
            img1 = Image.open(original_path).convert("RGB")
            img2 = Image.open(stego_path).convert("RGB")
            
            # Buat gambar perbedaan (highlight perubahan dengan warna merah)
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # Temukan piksel yang berbeda
            diff_mask = (arr1 != arr2).any(axis=2)
            
            # Buat gambar dengan highlight merah di area yang berbeda
            diff_img = arr1.copy()
            diff_img[diff_mask] = [255, 0, 0]  # Warna merah untuk perubahan
            
            # Konversi ke PIL Image
            diff_pil = Image.fromarray(diff_img.astype('uint8'))
            diff_pil.thumbnail((150, 150))
            
            # Tampilkan di preview
            photo = ImageTk.PhotoImage(diff_pil)
            self.diff_preview_label.config(image=photo, text="")
            self.diff_preview_label.image = photo
            
        except Exception as e:
            self.diff_preview_label.config(text=f"Error: {str(e)[:20]}...", image="")
            
    def update_preview(self, image_path, label_widget):
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                label_widget.config(image=photo, text="")
                label_widget.image = photo
            except Exception as e:
                label_widget.config(text=f"Error", image="")
        else:
            label_widget.config(text="Tidak ada gambar", image="")
            
    def reset_hide_tab(self):
        self.pesan_entry.delete("1.0", tk.END)
        self.output_name_entry.delete(0, tk.END)
        self.output_name_entry.insert(0, "stego_output.png")
        self.input_path_entry.delete(0, tk.END)
        self.input_image_path = ""
        self.image_info_label.config(text="")
        self.update_char_count()
        self.status_bar.config(text="Form telah direset")
        
    def open_file_location(self, file_path):
        folder_path = os.path.dirname(file_path)
        if os.path.exists(folder_path):
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS, Linux
                import subprocess
                try:
                    if sys.platform == 'darwin':  # macOS
                        subprocess.Popen(['open', folder_path])
                    else:  # Linux
                        subprocess.Popen(['xdg-open', folder_path])
                except:
                    pass

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganografiApp(root)
    root.mainloop()