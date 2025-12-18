---

## 📌 README 

**Steganografi** is a simple Python project that implements *data hiding techniques* to embed secret text into an image file without visibly changing the image. The goal of this repository is to demonstrate how steganography works by encoding and decoding hidden messages using Python. ([GitHub][1])

This project reads a plain text file and hides its content within an image using a steganography algorithm, then produces a new *stego image* that carries the hidden data. The encoded message can be extracted later with the provided decoding function. ([GitHub][1])

### 🛠 Features

* 🔐 **Hide text data inside an image**
* 🖼 Output stego image that visually looks the same as the original
* 🔄 Decode hidden messages from stego images
* 🐍 Implemented in Python

### 🚀 How to Use

1. Clone this repository

   ```bash
   git clone https://github.com/edonurcahyo/Steganografi.git
   ```
2. Navigate into the project folder

   ```bash
   cd Steganografi
   ```
3. Run the steganography script

   ```bash
   python stega.py
   ```

Replace the input text file or image as needed to hide different messages.

### 📁 Project Structure

* `stega.py` — main Python script for encoding and decoding
* `input.png` — sample cover image
* `lorem_*.txt` — sample text files to hide
* `stego_output*.png` — result images containing hidden data

---
